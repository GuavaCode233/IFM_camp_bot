from nextcord.ext import tasks, commands
import nextcord as ntd
import pandas as pd

from typing import List, Dict, Any
import json

from .utilities import AccessFile


class Stock:
    """儲存個股資料。
    """
    pass


class StockManager(commands.Cog, AccessFile):
    """控制股票。
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.CONFIG: Dict[str, Any] = self.read_file("game_config")

        self.round: int = 0   # 標記目前回合
        self.quarters:Dict[int, str] = {1: "Q4", 2: "Q1", 3: "Q2", 4: "Q3"} # round: "quarter"
        self.stocks: List[Stock] = None

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


def setup(bot: commands.Bot):
    bot.add_cog(StockManager(bot))