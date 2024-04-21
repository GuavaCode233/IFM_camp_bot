from nextcord.ext import tasks, commands, application_checks
import nextcord as ntd
import pandas as pd

from typing import List, Dict, Any
from dataclasses import dataclass
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


class StockManager(commands.Cog, AccessFile):
    """控制股票。
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.CONFIG: Dict[str, Any] = self.read_file("game_config")

        self.round: int = 0   # 標記目前回合
        self.quarters:Dict[int, str] = {1: "Q4", 2: "Q1", 3: "Q2", 4: "Q3"} # round: "quarter"
        self.stocks: List[Stock] = []

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded stock_manager.py")

        print("Stock Status:")
        NEW_GAME = self.CONFIG["NEW_GAME"]
        CONVERT_RAW_STOCK_DATA = self.CONFIG["CONVERT_RAW_STOCK_DATA"]
        if(CONVERT_RAW_STOCK_DATA):
            self.convert_raw_stock_data()
            print("Raw stock data converted.")
        
        if(NEW_GAME):
            pass

    def convert_raw_stock_data(self):
        """將Excel資料轉到stock_data.json。
        """
        
        dict_ = {}

        df: pd.DataFrame = pd.read_excel(   # 初始欄位資料
            ".\\Data\\stock_data.xlsx", "initial_data"
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
        
        self.save_to("raw_stock_data", dict_=dict_)

    @ntd.slash_command(
        name="open_round",
        description="開始下一回合(回合未關閉無法使用)"
    )
    @application_checks.is_owner()
    async def open_round(self):
        """下一回合(開盤)。
        """

        # TODO: Check if round is open, if it's open then return.
        # 讀取股票資料存至 self.stocks的每個 Stock內
        # 讀取新聞資料 未設計
        # 開始新聞計時 未設計
        # 開始 price_change_loop
        # 開啟交易功能

        raise NotImplementedError("Function not implimented.")
    
    @ntd.slash_command(
        name="close_round",
        description="結束(回合未開啟無法使用)"
    )
    @application_checks.is_owner()
    async def close_round(self):
        """結束本回合(收盤)。
        """

        # TODO: Check if round is closed, if it's closed then return.
        # 停止 price_change_loop
        # 關閉交易功能

        raise NotImplementedError("Function not implimented.")


def setup(bot: commands.Bot):
    bot.add_cog(StockManager(bot))