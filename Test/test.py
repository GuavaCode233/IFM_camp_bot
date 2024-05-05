from typing import TypedDict, List, Union

class Data(TypedDict):
    type: str
    time: str
    user: str
    serial: int
    team: str
    original: int
    updated: int

class Log(TypedDict):
    serial: int
    # 使用動態鍵，並將其值定義為 AssetUpdate 的列表
    # 這樣就可以接受任意流水號的資料
    __root__: List[Data]

# 使用 DynamicSerialDict 作為資料型態提示
data: Log = {}
a = data["1"]

