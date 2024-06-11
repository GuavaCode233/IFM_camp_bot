"""存取檔案用。
"""
from typing import Any
import json
import os


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