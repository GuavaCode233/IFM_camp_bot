"""存取檔案用。
"""
from typing import Dict, List, Any, Literal
from datetime import datetime
import json
import os

from .datatypes import LogData, InitialStockData


def read_file(file_name: str) -> Any:
    """讀取指定檔名的檔案。
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
        

def save_to(file_name: str, data: dict | list):
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
            data, json_file,
            ensure_ascii=False,
            indent=4
        )


def log(
    *,
    type_: Literal["AssetUpdate", "StockChange"],
    time: datetime,
    user: str,
    team: str,
    original: int | None = None,
    updated: int | None = None,
    trade: str | None = None,
    stock: int | None = None,
    quantity: int | None = None
):
    """紀錄收支動態(各小隊)。
    """

    with open(
        ".\\Data\\alteration_log.json",
        mode="r",
        encoding="utf-8"
    ) as json_file:
        dict_: Dict[str, int | List[LogData]] = json.load(json_file)

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
        initail_stock_data: InitialStockData = read_file("raw_stock_data")["initial_data"][stock]
        stock_symbol_name = f"{initail_stock_data['symbol']} {initail_stock_data['name']}"
        dict_[team].append(
            {
                "type": type_,
                "time": time.strftime("%m/%d %I:%M%p"),
                "user": user,
                "serial": dict_["serial"],
                "team": team,
                "trade": trade,
                "stock": stock_symbol_name,
                "quantity": quantity
            }
        )

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
        