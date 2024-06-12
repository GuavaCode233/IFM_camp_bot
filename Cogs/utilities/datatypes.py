from typing import TypedDict, List, Dict, Literal, NotRequired


class TeamChannelIDs(TypedDict):
    ASSET: int
    NOTICE: int


class ChannelIDs(TypedDict):
    """頻道ID。

    NEWS_FEED: `int`
        「地球新聞台」頻道ID。
    CHANGE_DEPOSIT: `int`
        「小隊收支」頻道ID。
    ALTERATION_LOG: `int`
        「收支動態」頻道ID。
    """

    NEWS_FEED: int
    CHANGE_DEPOSIT: int
    ALTERATION_LOG: int
    STOCK_MARKET: int
    __root__: TeamChannelIDs


class MessageIDs(TypedDict):
    CHANGE_DEPOSIT: int
    ALTERATION_LOG: int
    STOCK_MARKET: int
    TRADE_VIEW: int
    ASSET_MESSAGE_IDS: Dict[str, int]
    """該隊「資產」頻道內之資產訊息ID。

    `"TEAM_n"`: `int`
    """


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
    CONVERT_RAW_NEWS_DATA: `bool`
        將Excel原始新聞資料轉換為JSON檔案。
    RELEASE_NEWS: `bool`
        是否發送新聞(測試使用)。
    STARTER_CASH: `int`
        遊戲開始時各小隊的初始資產額。
    ROUND_TO_QUARTER: `dict[str, str]`
        回合與季對照表("round": "quarter")。
    NUMBER_OF_TEAMS: `int`
        總小隊數量。
    
    頻道及訊息ID
    -----------
    channel_ids: `ChannelIDs`
        存放「地球新聞台」、「小隊收支」、「收支動態」以及各小隊「資產」與「即時通知」頻道ID。
    message_ids: `MessageIDs`
        存放「小隊收支」、「收支動態」以及各小隊「資產」與「即時通知」訊息ID。
    """

    NEW_GAME: bool
    RESET_UI: bool
    CLEAR_LOG: bool
    UPDATE_ASSET: bool
    CONVERT_RAW_STOCK_DATA: bool
    CONVERT_RAW_NEWS_DATA: bool
    RELEASE_NEWS: bool
    STARTER_CASH: int
    ROUND_TO_QUARTER: Dict[str, str]
    NUMBER_OF_TEAMS: int
    channel_ids: ChannelIDs
    message_ids: MessageIDs


class AssetDict(TypedDict):
    """小隊資產資料。

    資料說明
    -------
    deposit: `int`
        該小隊存款額。
    stock_inv: `Dict[str, List[int]]`
        該小隊所有股票以及原始成本。
    revenue: `int`
        該小隊總收益。
    """

    deposit: int
    stock_inv: Dict[str, List[int]]
    revenue: int


class AssetsData(TypedDict):
    __root__: AssetDict


ChangeMode = Literal["Deposit", "Withdraw", "Change"]
LogType = Literal["DepositChange", "Transfer", "StockChange"]

LogData = TypedDict(
    "LogData",
    {
        "log_type": LogType,
        "time": str,
        "user": str,
        "serial": int,
        "team": str | List[str, str],
        "original_deposit": NotRequired[int | List[int, int]],
        "changed_deposit": NotRequired[int | List[int, int]],
        "trade_type": NotRequired[str],
        "stock": NotRequired[str],
        "quantity": NotRequired[str]
    }
)

class AlterationLog(TypedDict):
    serial: int
    __root__ = List[LogData]


class InitialStockData(TypedDict):
    """股票開頭資料。

    name: `str`
        股票名稱。
    symbol: `str`
        股票代號。
    sector: `str`
        所屬產業。
    first_open: `float`
        首次開盤價格。
    """

    name: str
    symbol: str
    sector: str
    first_open: float


class FinancialStatement(TypedDict):
    """公司財務報表(財務狀況)。

    random_ratio: `float`
        隨機變動值調整率。
    eps: `float`
        EPS。
    eps_qoq: `float`
        EPS季增率。
    adjust_ratio: `float`
        EPS QoQ調整率。
    net_revenue: `int`
        銷貨淨額。
    gross_income: `int`
        銷貨毛額。
    income_from_operating: `int`
        營業收入。
    net_income: `int`
        本期損益。
    """

    random_ratio: float
    eps: float
    eps_qoq: float
    adjust_ratio: float
    net_revenue: int
    gross_income: int
    income_from_operating: int
    net_income: int


class RawStockData(TypedDict):
    """原始股票資料。
    """

    initial_data: List[InitialStockData]
    __root__: List[FinancialStatement]


class StockDict(TypedDict):
    """個股市場資料。

    price: `float`
        當前價格。
    close: `float`
        上季收盤價格。
    eps_qoq: `float`
        上季EPS季增率。
    adjust_ratio: `float`
        EPS QoQ調整率。
    random_ratio: `float`
        隨機變動值調整率。
    """

    price: float
    close: float
    eps_qoq: float
    adjust_ratio: float
    random_ratio: float


MarketData = List[StockDict]
"""每支股票的市場資料。
"""

TradeType = Literal["買進", "賣出"]
"""交易類別(買進、賣出)。
"""

class News(TypedDict):
    """個別新聞資料。

    title: `str`
        新聞標題。
    content: `str`
        新聞內容。
    """

    title: str
    content: str


RawNews = Dict[str, List[News]]
"""原始新聞資料(全部資料)。

`"round"`: `List[News]`
"""


GameState = TypedDict(
    "GameState",
    {
        "round": int,
        "released_news_count": Dict[str, int],
        "is_in_round": bool,
    },
    total=True
)
"""遊戲狀態資料。

round: `int`
    第n回合，0代表準備狀態；5代表遊戲結束。
released_news_count: `Dict[str, int]`
    每回合已發送新聞數量。
is_in_round: `bool`
    標記回合是否開始(遊戲過程重啟使用)。
"""