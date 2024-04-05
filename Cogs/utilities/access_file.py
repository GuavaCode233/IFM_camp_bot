from typing import Dict, List, Any
from datetime import datetime
import json
import os


class AccessFile:
    """存取檔案用之母類別。
    """

    @classmethod
    def acc_game_config(cls) -> Dict[str, Any]:
        with open(".\\Data\\game_config.json", "r") as temp_file:
            return json.load(temp_file)

    @classmethod
    def acc_team_assets(cls) -> Dict[str, Dict[str, Any]]:
        with open(".\\Data\\team_assets.json", "r") as temp_file:
            return json.load(temp_file)
        
    @classmethod
    def acc_log(cls) -> Dict[str, List[Dict[str, Any]]]:
        with open(".\\Data\\alteration_log.json", "r") as temp_file:
            return json.load(temp_file)

    @classmethod
    def save_to(cls, file_name: str, dict_: Dict):
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
    
    @classmethod
    def log(
        cls,
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
    
    @classmethod
    def clear_log_data(cls):
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