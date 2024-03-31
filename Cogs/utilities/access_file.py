from typing import Dict, Any
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