from nextcord.ext import tasks, commands, application_checks
import nextcord as ntd
import pandas as pd

from typing import List, Dict, Any
from dataclasses import dataclass
from pprint import pprint
import asyncio
import random
import json

from .utilities import AccessFile


@dataclass(kw_only=True, slots=True)
class Stock:
    """儲存個股資料。
    """
    
    name: str
    symbol: str
    eps_qoq: float = 0.0
    adjust_ratio: float = 0.0
    random_ratio: float = 0.0
    price: float = 0.0
    close: float = 0.0

    def delta_price(self):
        """股價變動量。

        股價變動
        delta P = EPS QoQ * Adjust Ratio + Random * Random Ratio * Rise/Fall
        """

        # # 有隨機機制
        # # 控制隨機變動數的正負
        # rise_fall_factor: int = 1
        # if(random.random() <= 0.3): # 跌價機率是否模組化?
        #     rise_fall_factor = -1
        
        # self.price += (self.eps_qoq * self.adjust_ratio
        #                + random.random() * self.random_ratio
        #                * rise_fall_factor)
        
        # 無隨機機制
        self.price += self.eps_qoq * self.adjust_ratio
        self.price = round(self.price, 6)
        # 會顯得有規律，可能要隨機，扣款時用round(price, 2)
        
    def get_price(self) -> str:
        return f"{self.name:7}{self.symbol:5} 收盤: {self.close:4.2f} 價格: {self.price:4.2f} 漲跌: {self.price - self.close:4.2f}"


class StockManager(commands.Cog, AccessFile):
    """控制股票。
    """

    __slots__ = (
        "bot",
        "CONFIG",
        "RAW_STOCK_DATA",
        "INITIAL_STOCK_DATA",
    )
    # 設定股價變動頻率(秒)
    PRICE_CHANGE_FREQUENCY: float = 5.0

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.CONFIG: Dict[str, Any] = self.read_file("game_config")
        self.RAW_STOCK_DATA: Dict[str, List[Dict[str, Any]]] = self.read_file("raw_stock_data")
        self.INITIAL_STOCK_DATA: List[Dict[str, str | float]] = self.RAW_STOCK_DATA["initial_data"]
        
        self.round: int = 0   # 標記目前回合
        self.quarters: Dict[int, str] = {1: "Q4", 2: "Q1", 3: "Q2", 4: "Q3"} # round: "quarter"
        self.stocks: List[Stock] = []

    @commands.Cog.listener()
    async def on_ready(self):
        """StockManager啟動程序。

        `CONVERT_RAW_STOCK_DATA`
        將Excel原始股票資料轉換為JSON檔案。

        `NEW_GAME`
        清除股票資料並重新抓取股票資料，
        如果資料有遺失，重新抓取股票資料。
        """

        NEW_GAME = self.CONFIG["NEW_GAME"]
        CONVERT_RAW_STOCK_DATA = self.CONFIG["CONVERT_RAW_STOCK_DATA"]
        if(CONVERT_RAW_STOCK_DATA):
            self.convert_raw_stock_data()
        
        if(NEW_GAME):
            self.reset_stock_data()
        elif(not self.stocks):  # 資料不對等
            self.fetch_stocks()

        print("Loaded stock_manager")

    def convert_raw_stock_data(self):
        """將Excel資料轉到stock_data.json。
        """
        
        dict_ = {}

        df: pd.DataFrame = pd.read_excel(   # 初始欄位資料
            ".\\Data\\raw_stock_data.xlsx", "initial_data"
        )
        json_data: Dict[str, List[Dict[str, str | int | float]]] = json.loads(
            df.to_json(orient="records")
        )   # 將pd.DataFrame轉成json object
        for d in json_data: # 將股票代碼前面的"n"刪除
            d["symbol"] = d["symbol"].lstrip("n")
        dict_["initial_data"] = json_data

        for quarter in self.quarters.values():   # 1-4季資料
            df: pd.DataFrame = pd.read_excel(
                ".\\Data\\raw_stock_data.xlsx", f"{quarter}"
            )
            json_data: Dict[str, List[Dict[str, str | int | float]]] = json.loads(
                df.to_json(orient="records")
            )   # 將pd.DataFrame轉成json object
            dict_[f"{quarter}"] = json_data
        
        self.save_to("raw_stock_data", data=dict_)

    def reset_stock_data(self):
        """清除股票資料並重新抓取資料。

        `stock_data.json`

        紀錄回合狀態:
        
        round
        第n回合，0代表準備狀態；5代表遊戲結束。

        is_in_round
        標記回合是否開始(遊戲過程重啟使用)。

        紀錄每支股票的:

        price
        當前價格。

        close
        收盤價格。

        eps_qoq
        當季EPS季增率(價格變動標準)。

        adjust_ratio
        EPS QoQ之調整率。

        random_ratio
        隨機變動率。

        (用索引對照)
        """

        dict_: Dict[str, int | List[Dict[str, float]]] = dict()
        dict_["round"] = 0  # 第0輪
        dict_["is_in_round"] = False   # 回合未開始

        stock_data = self.RAW_STOCK_DATA[self.quarters[1]]
        dict_["market"] = [
            {
                "price": init_data["first_open"],
                "close": init_data["first_open"],
                "eps_qoq": stock["eps_qoq"],
                "adjust_ratio": stock["adjust_ratio"],
                "random_ratio": stock["random_ratio"]
            } for stock, init_data in zip(stock_data, self.INITIAL_STOCK_DATA)
        ]

        self.save_to("stock_data", dict_)
        self.fetch_stocks()

    def fetch_stocks(self):
        """從`stock_data.json`中抓取資料並初始化:class:`Stocks`。
        """

        stock_data: List[Dict[str, float]] = self.read_file("stock_data")["market"]
        self.stocks = [
            Stock(
                name=init_data["name"],
                symbol=init_data["symbol"],
                eps_qoq=stock["eps_qoq"],
                adjust_ratio=stock["adjust_ratio"],
                random_ratio=stock["random_ratio"],
                price=stock["price"],
                close=stock["close"]
            ) for stock, init_data in zip(stock_data, self.INITIAL_STOCK_DATA)
        ]

    @tasks.loop(seconds=PRICE_CHANGE_FREQUENCY)
    async def price_change_loop(self):
        """每過一段時間更改股價，並將當前股市資料儲存至`stock_data.json`。

        `PRICE_CHANGE_FREQUENCY`
        股價變動頻率(秒)。
        """

        if(not self.stocks):    # 防止資料遺失
            self.fetch_stocks()
        
        stock_data: Dict[str, Any] = self.read_file("stock_data")
        stock_data_list: List[Dict[str, float]] = stock_data["market"]

        print(f"Iteration: {self.price_change_loop.current_loop}")
        for stock, stock_dict in zip(self.stocks, stock_data_list):
            # 改變該股股價
            stock.delta_price()
            print(stock.get_price())
            # 儲存股價
            stock_dict.update({"price": stock.price})
        print()

        stock_data.update({"market": stock_data_list})
        self.save_to("stock_data", stock_data)  # 儲存所有變動後資料

    @classmethod
    @price_change_loop.before_loop
    async def before_price_change_loop(cls):
        # 開盤後先等待
        await asyncio.sleep(cls.PRICE_CHANGE_FREQUENCY)

    @ntd.slash_command(
        name="open_round",
        description="開始下一回合(回合未關閉無法使用)"
    )
    @application_checks.is_owner()
    async def open_round(self, interaction: ntd.Interaction):
        """下一回合(開盤)。
        """

        # TODO: Check if round is open, if it's open then handle error
        # 讀取股票資料存至 self.stocks的每個 Stock內
        # 讀取新聞資料 未設計
        # 開始新聞計時 未設計
        # 開始 price_change_loop
        # 開啟交易功能
     
        # 回合已開始
        if(self.price_change_loop.is_running()):
            await interaction.response.send_message(
                "**回合已開始!**",
                delete_after=3,
                ephemeral=True
            )
            return

        self.price_change_loop.start()
        await interaction.response.send_message(
            "price_change_loop started",
            delete_after=3,
            ephemeral=True
        )

        # raise NotImplementedError("Function not implimented.")
    
    @ntd.slash_command(
        name="close_round",
        description="結束(回合未開啟無法使用)"
    )
    @application_checks.is_owner()
    async def close_round(self, interaction: ntd.Interaction):
        """結束本回合(收盤)。
        """

        # TODO: Check if round is closed, if it's closed then return.
        # 停止 price_change_loop
        # 關閉交易功能

        # 回合未開啟
        if(not self.price_change_loop.is_running()):
            await interaction.response.send_message(
                "**回合未開啟!**",
                delete_after=3,
                ephemeral=True
            )
            return

        self.price_change_loop.stop()
        await interaction.response.send_message(
            "price_change_loop stopped",
            delete_after=3,
            ephemeral=True
        )
        # raise NotImplementedError("Function not implimented.")


def setup(bot: commands.Bot):
    bot.add_cog(StockManager(bot))
