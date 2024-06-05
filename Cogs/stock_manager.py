from nextcord.ext import tasks, commands, application_checks
import nextcord as ntd
import pandas as pd

from typing import List, Dict, ClassVar
from dataclasses import dataclass
from pprint import pprint
import asyncio
import json

from .discord_ui import DiscordUI
from .utilities import access_file
from .utilities.datatypes import (
    Config,
    FinancialStatement,
    RawStockData,
    InitialStockData,
    MarketData,
    RawNews,
    News,
    GameState
)


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

    def change_price(self):
        """變動股價。

        股價變動量:
            delta P = EPS QoQ * Adjust Ratio
        """
        
        # 無隨機機制
        self.price += self.eps_qoq * self.adjust_ratio
        self.price = round(self.price, 6)
        
    def get_price(self) -> str:
        return f"{self.name.ljust(5, '　')}{self.symbol:5} 收盤: {self.close:4.2f} " \
               f"價格: {self.price:4.2f} 漲跌: {self.price - self.close:4.2f}"


class StockManager(commands.Cog):
    """控制股票及新聞。
    """

    __slots__ = (
        "bot",
        "CONFIG",
        "RAW_STOCK_DATA",
        "INITIAL_STOCK_DATA",
    )
    # 股價變動頻率(秒)
    PRICE_CHANGE_FREQUENCY: ClassVar[float] = 3.0
    # 發送新聞間隔(秒)
    TIME_BETWEEN_NEWS: ClassVar[float] = 120.0

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.CONFIG: Config = access_file.read_file("game_config")
        self.RAW_STOCK_DATA: RawStockData = access_file.read_file("raw_stock_data")
        self.INITIAL_STOCK_DATA: List[InitialStockData] = self.RAW_STOCK_DATA["initial_data"]
        
        # 遊戲狀態
        self.game_state: GameState = None
        # 回合、季對照表(round: "quarter")
        self.QUARTERS: Dict[int, str] = {1: "Q4", 2: "Q1", 3: "Q2", 4: "Q3"}
        # 儲存即時股票資料
        self.stocks: List[Stock] = []
        # 當回合預發新聞
        self.pending_news: List[News] = []

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
        CONVERT_RAW_NEWS_DATA = self.CONFIG["CONVERT_RAW_NEWS_DATA"]

        if(CONVERT_RAW_STOCK_DATA):
            self.convert_raw_stock_data()
        
        if(CONVERT_RAW_NEWS_DATA):
            self.convert_news_data()

        if(NEW_GAME):
            self.reset_market_data()
            ui: DiscordUI = self.bot.get_cog("DiscordUI")
            await ui.clear_news()
            self.reset_game_state()
        elif(not self.stocks):  # 資料不對等
            self.fetch_stocks()
            self.fetch_game_state()

        print("Loaded stock_manager")

    def reset_game_state(self):
        """重製遊戲狀態資料(股票與新聞控制資料)。
        """
        
        self.fetch_game_state()

        self.game_state["round"] = 0
        self.game_state["is_in_round"] = False
        self.game_state["released_news_count"] = {str(r): 0 for r in range(1, 5)}

        self.save_game_state()

    def save_game_state(self):
        """儲存遊戲狀態。
        """

        access_file.save_to("game_state", self.game_state)

    def fetch_game_state(self):
        """抓取遊戲狀態self.game_state: `GameState`。
        """

        self.game_state: GameState = access_file.read_file("game_state")

    def convert_raw_stock_data(self):
        """將股票原始Excel資料轉到`stock_data.json`。
        """
        
        dict_: RawStockData = {}

        df: pd.DataFrame = pd.read_excel(   # 初始欄位資料
            ".\\Data\\raw_stock_data.xlsx", "initial_data"
        )
        json_data: Dict[str, List[Dict[str, str | int | float]]] = json.loads(
            df.to_json(orient="records")
        )   # 將pd.DataFrame轉成json object
        for d in json_data: # 將股票代碼前面的"n"刪除
            d["symbol"] = d["symbol"].lstrip("n")
        dict_["initial_data"] = json_data

        for quarter in self.QUARTERS.values():   # 1-4季資料
            df: pd.DataFrame = pd.read_excel(
                ".\\Data\\raw_stock_data.xlsx", f"{quarter}"
            )
            json_data: InitialStockData = json.loads(
                df.to_json(orient="records")
            )   # 將pd.DataFrame轉成json object
            dict_[f"{quarter}"] = json_data
        
        access_file.save_to("raw_stock_data", data=dict_)

    def reset_market_data(self):
        """清除市場資料並重新抓取 :class:`Stock`資料。
        """

        financial_statements: List[FinancialStatement] = self.RAW_STOCK_DATA[self.QUARTERS[1]]
        market_data: MarketData = [
            {
                "price": init_data["first_open"],
                "close": init_data["first_open"],
                "eps_qoq": statement["eps_qoq"],
                "adjust_ratio": statement["adjust_ratio"],
                "random_ratio": statement["random_ratio"]
            } for statement, init_data in zip(financial_statements, self.INITIAL_STOCK_DATA)
        ]
        access_file.save_to("market_data", market_data)
        self.fetch_stocks()

    def fetch_stocks(self):
        """從`stock_data.json`中抓取資料並初始化:class:`Stocks`。
        """

        stock_data: MarketData = access_file.read_file("market_data")
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
        
        stock_data: MarketData = access_file.read_file("market_data")

        print(f"Iteration: {self.price_change_loop.current_loop}")
        for stock, stock_dict in zip(self.stocks, stock_data):
            # 改變該股股價
            stock.change_price()
            print(stock.get_price())
            # 儲存股價
            stock_dict.update({"price": stock.price})
        print()

        access_file.save_to("market_data", stock_data)  # 儲存所有變動後資料
        # 更新市場資料
        ui: DiscordUI = self.bot.get_cog("DiscordUI")
        await ui.update_market_ui()

    @classmethod
    @price_change_loop.before_loop
    async def before_price_change_loop(cls):
        """在`price_change_loop`開始之前先等待。
        """

        await asyncio.sleep(cls.PRICE_CHANGE_FREQUENCY)

    def convert_news_data(self):
        """將新聞原始Excel資料轉到`raw_news.json`。
        """

        dict_: RawNews = {}

        for round_, quarter in self.QUARTERS.items():
            df: pd.DataFrame = pd.read_excel(
                ".\\Data\\raw_news.xlsx", f"{quarter}"
            )
            json_data: List[News] = json.loads(
                df.to_json(orient="records")
            )
            dict_[f"{round_}"] = json_data
        
        access_file.save_to("raw_news", dict_)

    def fetch_round_news(self):
        """抓取本回合預發新聞，如果回合中斷則從未發過的新聞開始抓取。
        """

        news: RawNews = access_file.read_file("raw_news")
        released_news_count: int = self.game_state["released_news_count"][str(self.game_state["round"])]
        self.pending_news: List[News] = news[str(self.game_state["round"])][released_news_count:]

    @tasks.loop(seconds=TIME_BETWEEN_NEWS)
    async def news_loop(self):
        """當回合開始時每過一段時間發送當回合新聞。
        """

        if(not self.pending_news):
            if(self.game_state["is_in_round"]): # 發完新聞
                self.news_loop.cancel()    
            else:   # 資料遺失    
                self.fetch_round_news()

        news = self.pending_news.pop(0)

        ui: DiscordUI = self.bot.get_cog("DiscordUI")
        await ui.release_news(
            title=news["title"],
            content=news["content"]
        )
        # 當回合已發送新聞數量+1
        self.game_state["released_news_count"][str(self.game_state["round"])] += 1
        self.save_game_state()
    
    @news_loop.before_loop
    async def before_news_loop(self):
        """在`news_loop`開始之前擷取本局新聞。
        """

        self.fetch_round_news()
        
    def update_market_and_stock_data(self):
        """回合開始時更新收盤價，並擷取本回合市場資料。
        """

        financial_statements: List[FinancialStatement] = self.RAW_STOCK_DATA[
            self.QUARTERS[self.game_state["round"]]
        ]
        market_data: MarketData = []
        for statement, stock in zip(financial_statements, self.stocks):
            market_data.append(
                {
                    "price": stock.price,
                    "close": stock.price,
                    "eps_qoq": statement["eps_qoq"],
                    "adjust_ratio": statement["adjust_ratio"],
                    "random_ratio": statement["random_ratio"]
                }
            )
            stock.close = stock.price
            stock.eps_qoq = statement["eps_qoq"]
            stock.adjust_ratio = statement["adjust_ratio"]
            stock.random_ratio = statement["random_ratio"]
        access_file.save_to("market_data", market_data)
            
    @ntd.slash_command(
        name="open_round",
        description="開始下一回合(回合未關閉無法使用)"
    )
    @application_checks.is_owner()
    async def open_round(self, interaction: ntd.Interaction):
        """下一回合(開盤)。
        """

        # TODO:
        # 更新遊戲狀態 (done)
        # 讀取新聞資料 (done)
        # 開始新聞計時 (done)
        # 開始 price_change_loop (done)
        # 開啟交易功能
     
        # 回合已開始
        if(self.price_change_loop.is_running()):
            await interaction.response.send_message(
                "**回合已開始!**",
                delete_after=3,
                ephemeral=True
            )
            return


        self.game_state["round"] += 1
        if(self.game_state["round"] != 1):
            self.update_market_and_stock_data()
            ui: DiscordUI = self.bot.get_cog("DiscordUI")
            await ui.update_market_ui()

        if(self.game_state["round"] == 5):
            pass # 遊戲結束
            return
        
        self.game_state["is_in_round"] = True
        self.save_game_state()

        self.price_change_loop.start()
        if(self.CONFIG["RELEASE_NEWS"]):
            self.news_loop.start()

        await interaction.response.send_message(
            f"回合{self.game_state["round"]}開始!",
            delete_after=3,
            ephemeral=True
        )
    
    @ntd.slash_command(
        name="close_round",
        description="結束(回合未開啟無法使用)"
    )
    @application_checks.is_owner()
    async def close_round(self, interaction: ntd.Interaction):
        """結束本回合(收盤)。
        """

        # TODO:
        # 停止 price_change_loop (done)
        # 關閉交易功能

        # 回合未開啟
        if(not self.price_change_loop.is_running()):
            await interaction.response.send_message(
                "**回合未開啟!**",
                delete_after=3,
                ephemeral=True
            )
            return
        
        self.game_state["is_in_round"] = False
        self.save_game_state()

        self.price_change_loop.stop()
        self.news_loop.cancel()

        await interaction.response.send_message(
            f"回合{self.game_state["round"]}結束!",
            delete_after=3,
            ephemeral=True
        )


def setup(bot: commands.Bot):
    bot.add_cog(StockManager(bot))
