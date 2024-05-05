from typing import TypedDict, List, Dict


class TeamChannelIDs(TypedDict):
    ASSET: int
    NOTICE: int


class ChannelIDs(TypedDict):
    CHANGE_DEPOSIT: int
    ALTERATION_LOG: int
    __root__: TeamChannelIDs


class TeamMessageIDs(TypedDict):
    __root__: int


class MessageIDs(TypedDict):
    CHANGE_DEPOSIT: int
    ALTERATION_LOG: int
    __root__: TeamMessageIDs


class Config(TypedDict):
    """遊戲初始資料字典型別。

    初始常數
    ---------
    NEW_GAME: `bool`
        新遊戲，刷新所有遊戲資料。
    RESET_UI: `bool`
        重製所有ui元素訊息，以重新抓取互動功能。
    CLEAR_LOG: `bool`
        清除已發送的小隊即時訊息以及清除收支動態，並清除log資料。
    UPDATE_ASSET: `bool`
        更新各小隊資產狀況訊息。
    CONVERT_RAW_STOCK_DATA: `bool`
        將Excel原始股票資料轉換為JSON檔案。
    STARTER_CASH: `int`
        遊戲開始時各小隊的初始資產額。
    
    頻道及訊息ID
    -----------
    channel_ids: `ChannelIDs`
        存放「小隊收支」、「收支動態」以及各小隊「資產」與「即時通知」頻道ID。
    message_ids: `MessageIDs`
        存放「小隊收支」、「收支動態」以及各小隊「資產」與「即時通知」訊息ID。
    """

    NEW_GAME: bool
    RESET_UI: bool
    CLEAR_LOG: bool
    UPDATE_ASSET: bool
    CONVERT_RAW_STOCK_DATA: bool
    STARTER_CASH: int
    channel_ids: ChannelIDs
    message_ids: MessageIDs


class TeamAssetsDict(TypedDict):
    """小隊資產資料。

    資料說明
    -------
    deposit: `int`
        該小隊存款額。
    stock_cost: `Dict[str, List[int]]`
        該小隊所有股票以及原始成本。
    revenue: `int`
        該小隊總收益。
    """

    deposit: int
    stock_cost: Dict[str, List[int]]
    revenue: int

class AssetsData(TypedDict):
    __root__: TeamAssetsDict

LogData = TypedDict(
    "LogData",
    {
        "type": str,
        "time": str,
        "user": str,
        "serial": int,
        "team": str,
        "original": int,
        "updated": int
    },
    total=True
)

class AlterationLog(TypedDict):
    serial: int
    __root__ = List[LogData]

