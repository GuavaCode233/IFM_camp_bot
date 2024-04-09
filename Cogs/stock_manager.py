from nextcord.ext import commands
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
        self.CONFIG = self.acc_game_config()
        self.quarters:List[str] = ["4", "1", "2", "3"]
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
        json_data: List[Dict[str, str | int]] = json.loads(
            df.to_json(orient="records")
        )   # 將pd.DataFrame轉成json object
        for d in json_data: # 將股票代碼前面的"n"刪除
            d["symbol"] = d["symbol"].lstrip("n")
        dict_["initial_data"] = json_data

        for quarter in self.quarters:   # 1-4季資料
            df: pd.DataFrame = pd.read_excel(
                ".\\Data\\stock_data.xlsx", f"Q{quarter}"
            )
            json_data: List[Dict[str, str | int | float]] = json.loads(
                df.to_json(orient="records")
            )   # 將pd.DataFrame轉成json object
            # 當季公司之財務狀況以股票代碼為key
            temp_dict = {}
            for d in json_data:
                symbol_key: str = d.pop("symbol").lstrip("n")
                temp_dict[symbol_key] = d
            dict_[f"Q{quarter}"] = temp_dict
        
        self.save_to("stock_data", dict_=dict_)


def setup(bot: commands.Bot):
    bot.add_cog(StockManager(bot))