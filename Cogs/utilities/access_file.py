from typing import Dict, List, Any
from datetime import datetime
import json
import os


class AccessFile:
    """存取檔案用之母類別。
    """
    
    @staticmethod
    def read_file(file_name: str) -> Any:
        """讀取指定檔名的檔案
        """

        file_path = f".\\Data\\{file_name}.json"
        if(not os.path.exists(file_path)):
            raise FileNotFoundError(f"File: '{file_name}' not found.")
        
        with open(
            file_path,
            mode="r",
            encoding="utf-8"
        ) as json_file:
            return json.load(json_file)
            
    @staticmethod
    def save_to(file_name: str, dict_: Dict):
        """開啟指定檔名的檔案並將dict_寫入。

        如果未找到檔案則 raise `FileNotFoundError`。
        """

        file_path = f".\\Data\\{file_name}.json"
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File: '{file_name}' not found.")
        
        with open(
            file_path,
            mode="w",
            encoding="utf-8"
        ) as json_file:
            json.dump(
                dict_, json_file,
                ensure_ascii=False,
                indent=4
            )
    
    @staticmethod
    def log(
        *,
        type_: str,
        time: datetime,
        user: str,
        team: str,
        original: int | None = None,
        updated: int | None = None,
        change_type: str | None = None,
        stock_name_symbol: str | None = None
    ):
        """紀錄收支動態(各小隊)。
        """
        with open(
            ".\\Data\\alteration_log.json",
            mode="r",
            encoding="utf-8"
        ) as json_file:
            dict_: Dict[str, int | List[Dict[str, Any]]] = json.load(json_file)

        if(dict_.get(team, None) is None):
            dict_[team] = []
        
        if(type_ == "AssetUpdate"):
            dict_[team].append(
                {
                    "type": type_,
                    "time": time.strftime("%m/%d %I:%M%p"),
                    "user": user,
                    "serial": dict_["serial"],
                    "team": team,
                    "original": original,
                    "updated": updated
                }            
            )
        elif(type_ == "StockChange"):
            raise NotImplementedError("StockChange log not implemented .")
        else:
            raise Exception(f"log type: {type_} not found.")

        dict_["serial"] += 1

        with open(
            ".\\Data\\alteration_log.json",
            mode="w",
            encoding="utf-8"
        ) as json_file:
            json.dump(
                dict_, json_file,
                ensure_ascii=False,
                indent=4
            )
    
    @staticmethod
    def clear_log_data():
        """清除log。
        """

        with open(
            ".\\Data\\alteration_log.json",
            mode="w",
            encoding="utf-8"
        ) as json_file:
            json.dump(
                {"serial": 0}, json_file,
                ensure_ascii=False,
                indent=4
            )