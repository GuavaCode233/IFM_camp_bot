from nextcord.ext import commands
from nextcord import ui
import nextcord as ntd

from datetime import datetime
from typing import Dict, List, Literal, Tuple

from .assets_manager import AssetsManager
from .utilities import access_file
from .utilities.datatypes import (
    AlterationLog,
    AssetDict,
    ChannelIDs,
    ChangeMode,
    Config,
    FinancialStatement,
    GameState,
    InitialStockData,
    LogData,
    LogType,
    MessageIDs,
    RawStockData,
    StockDict,
    TradeType
)


PURPLE: Literal[0x433274] = 0x433274   # Embed color: purple
# 隊輔id跟小隊對照表
USER_ID_TO_TEAM: Dict[int, int] = {
    601014917746786335: 9   # Guava
}
# 股票開頭資料
INITIAL_STOCK_DATA: List[InitialStockData] = access_file.read_file(
    "raw_stock_data"
)["initial_data"]
# 小隊個數
NUMBER_OF_TEAMS: int = access_file.read_file("game_config").get("NUMBER_OF_TEAMS")


def get_stock_name_symbol(index_: int | str) -> str:
    """抓取 "股票名 股票代碼" string。
    """
    
    index_ = int(index_)
    name = INITIAL_STOCK_DATA[index_]["name"]
    symbol = INITIAL_STOCK_DATA[index_]["symbol"]
    return f"{name} {symbol}"


def get_stock_inventory(team: int | str) -> Dict[str, List[int]]:
    """擷取小隊股票庫存。
    """

    asset: AssetDict = access_file.read_file("team_assets")[f"{team}"]
    stock_inv: Dict[str, List[int]] = asset.get("stock_inv")

    return stock_inv


def get_deposit(team: int | str) -> int:
    """擷取小隊存款額。
    """

    return access_file.read_file("team_assets")[f"{team}"]["deposit"]


def inventory_to_string(
        stock_inv: Dict[str, List[int]],
        index_: str | int | None = None
    ) -> str:
    """將股票庫存資料格式化。
    """

    if(index_ is None):
        output = [
            f"{INITIAL_STOCK_DATA[int(index_)]["name"]} {INITIAL_STOCK_DATA[int(index_)]["symbol"]}" \
            f"\t張數: {len(stocks)}\n" for index_, stocks in stock_inv.items()
        ]
    else:
        output = f"{INITIAL_STOCK_DATA[int(index_)]["name"]} {INITIAL_STOCK_DATA[int(index_)]["symbol"]}" \
                 f"\t張數: {len(stock_inv[index_])}\n"
    return "".join(output)


def get_stock_price(index_: int | str) -> float:
    """擷取指定股票當下的價格。
    """

    stock_dict: StockDict = access_file.read_file(
        "market_data"
    )[int(index_)]

    return stock_dict["price"]


class MarketFunctionView(ui.View):
    """股市 View 放置交易功能按鈕及財務報表查詢按鈕。
    """

    __slots__ = ("bot")

    trading_user_ids: List[int] = []    # 存放使用「股票交易」的使用者id
    querying_user_ids: List[int] = []   # 存放使用「查詢財務報表」的使用者id

    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @classmethod
    def add_trading_user(cls, user_id: int):
        """將使用者加入`trading_user_ids`中。
        """

        cls.trading_user_ids.append(user_id)
    
    @classmethod
    def remove_trading_user(cls, user_id: int):
        """將交易結束的使用者從`trading_user_ids`中移除。
        """

        cls.trading_user_ids.remove(user_id)

    @classmethod
    def add_querying_user(cls, user_id: int):
        """將使用者加入`querying_user_ids`中。
        """

        cls.querying_user_ids.append(user_id)
    
    @classmethod
    def remove_querying_user(cls, user_id: int):
        """將查詢結束的使用者從`querying_user_ids`中移除。
        """

        cls.querying_user_ids.remove(user_id)
    
    @ui.button(
        label="股票交易",
        style=ntd.ButtonStyle.gray,
        emoji="📊",
        row=0
    )
    async def trade_button_callback(
        self,
        button: ui.Button,
        interaction: ntd.Interaction
    ):
        """股票交易按鈕 callback。
        """

        if(interaction.user.id in MarketFunctionView.trading_user_ids):    # 防止重複呼叫功能
            await interaction.response.send_message(
                content="**已開啟交易選單!!!**",
                delete_after=5,
                ephemeral=True
            )
            return
        
        MarketFunctionView.add_trading_user(interaction.user.id)
        view = TradeView(
            bot=self.bot,
            user_name=interaction.user.display_name,
            user_avatar=interaction.user.display_avatar,
            user_id=interaction.user.id
        )
        await interaction.response.send_message(
            embed=view.status_embed(),
            view=view,
            ephemeral=True
        )

    @ui.button(
        label="查詢財務報表",
        style=ntd.ButtonStyle.gray,
        emoji="📋",
        row=0
    )
    async def query_button_callback(
        self,
        button: ui.Button,
        interaction: ntd.Interaction
    ):
        """查詢財務報表按鈕 callback。
        """
        
        if(interaction.user.id in MarketFunctionView.querying_user_ids):    # 防止重複呼叫功能
            await interaction.response.send_message(
                content="**已開啟查詢選單!!!**",
                delete_after=5,
                ephemeral=True
            )
            return

        MarketFunctionView.add_querying_user(interaction.user.id)
        view = FinancialStatementView()
        await interaction.response.send_message(
            content=view.initial_message(),
            view=view,
            ephemeral=True
        )


class TradeView(ui.View):
    """交易功能 View。
    """
    
    __slots__ = (
        "bot",
        "user_name",
        "user_avatar",
        "team",
        "stock_inv",
        "embed_title",
        "deposit",
        "trade_field_name",
        "quantity_field_name",
        "quantity_field_value",
        "trade_type",
        "stock_select",
        "selected_stock_index"
    )

    def __init__(
            self,
            *,
            bot: commands.Bot,
            user_name: str,
            user_avatar: ntd.Asset,
            user_id: int
        ):
        super().__init__(timeout=None)
        self.bot = bot
        self.user_name = user_name
        self.user_avatar = user_avatar
        self.team = USER_ID_TO_TEAM[user_id]
        self.stock_inv = get_stock_inventory(self.team)   # 該小隊股票庫存
        # embed message
        self.embed_title: str = "股票交易"
        self.deposit: int = get_deposit(self.team)
        self.trade_field_name: str = "請選擇交易別"   # 買進: 商品；賣出: 目前庫存
        self.trade_field_value: str = "請選擇商品"    # 買進: name symbol；賣出: 庫存內容
        self.quantity_field_name: str = "張數"      # 買進 or 賣出 張數
        self.quantity_field_value: str | int = "請輸入張數" # quantity
        # select status
        self.trade_type: TradeType = None
        self.stock_select: TradeStockSelect = None # 紀錄股票選取下拉選單
        self.selected_stock_index: int = None
    
    def status_embed(self) -> ntd.Embed:
        """用於編排選單狀態訊息。
        """

        self.deposit = get_deposit(self.team)   # 更新顯示的存款額
        time = datetime.now()
        time = time.strftime("%I:%M%p")

        embed = ntd.Embed(
            color=PURPLE,
            title=f"第{self.team}小隊 {self.embed_title}",
            description=f"目前存款: {self.deposit:,}"
        )
        embed.add_field(
            name=self.trade_field_name,
            value=self.trade_field_value
        )
        embed.add_field(
            name=self.quantity_field_name,
            value=f"{self.quantity_field_value}\n*(1張 = 1000股)*"
        )
        embed.set_footer(
            text=f"{self.user_name} | Today at {time}",
            icon_url=self.user_avatar
        )
        return embed
    
    def input_check(self) -> bool:
        """檢查輸入資料是否完整。
        """

        if(self.trade_type is None or
           self.selected_stock_index is None or
           isinstance(self.quantity_field_value, str)):
            return False
        else:
            return True
        
    @ui.select(
        placeholder="選擇買賣別",
        options=[
            ntd.SelectOption(
                label="買進",
                description="買進指定的股票"
            ),
            ntd.SelectOption(
                label="賣出",
                description="賣出指定的股票"
            )
        ],
        row=1
    )
    async def trade_type_select_callback(
        self,
        select: ui.StringSelect,
        interaction: ntd.Interaction
    ):
        """買賣別選取選單callback。
        """
        
        self.trade_type = select.values[0]
        # 刪除舊的股票選單再發新的
        self.remove_item(self.stock_select)

        if(self.trade_type == "買進"):   # 看有沒有更好的解決方式
            self.embed_title = "買進 股票交易"
            self.trade_field_name = "商品"
            self.trade_field_value = "請選擇商品"
            self.quantity_field_name = "買進張數"
            
            self.stock_select = TradeStockSelect(self)
            self.add_item(self.stock_select)
        elif(self.trade_type == "賣出"):
            self.embed_title = "賣出 股票交易"
            self.trade_field_name = "目前庫存"
            self.quantity_field_name = "賣出張數"

            if(not self.stock_inv):
                self.trade_field_value = "無股票庫存"
            else:
                self.trade_field_value = inventory_to_string(
                    self.stock_inv
                )
                self.stock_select = TradeStockSelect(self)
                self.add_item(self.stock_select)
            
        await interaction.response.edit_message(
            embed=self.status_embed(),
            view=self
        )

    @ui.button(
        label="輸入張數",
        style=ntd.ButtonStyle.blurple,
        emoji="📃",
        row=3
    )
    async def input_quantity_button_callback(
        self,
        button: ui.Button,
        interaction: ntd.Interaction
    ):
        """輸入張數按鈕callback。
        """

        await interaction.response.send_modal(TradeQuantityInput(self))

    @ui.button(
        label="確認交易",
        style=ntd.ButtonStyle.green,
        emoji="✅",
        row=4
    )
    async def confirm_button_callback(
        self,
        button: ui.Button,
        interaction: ntd.Interaction
    ):
        """確認送出按扭callback。
        """

        if(not self.input_check()): # 檢查資料都填齊
            await interaction.response.send_message(
                    content="**輸入資料不完整!!!**",
                    delete_after=5,
                    ephemeral=True
                )
            return
        
        if(self.trade_type == "買進" and
            (get_stock_price(self.selected_stock_index)
            * self.quantity_field_value * 1000 > self.deposit)):    # 餘額不足
            await interaction.response.send_message(
                content="**存款餘額不足**",
                delete_after=5,
                ephemeral=True
            )
            return
        elif(self.trade_type == "賣出" and
             self.quantity_field_value > len(self.stock_inv[f"{self.selected_stock_index}"])):
            await interaction.response.send_message(
                content=f"**{get_stock_name_symbol(self.selected_stock_index)} 持有張數不足**",
                delete_after=5,
                ephemeral=True
            )
            return
        
        MarketFunctionView.remove_trading_user(interaction.user.id)
        self.clear_items()
        await interaction.response.edit_message(
            content=f"**{self.trade_type}成功!!!**",
            embed=None,
            delete_after=5,
            view=self
        )
        self.stop()
        # stock_trade, update_log
        assets_manager: AssetsManager = self.bot.get_cog("AssetsManager")
        display_value = await assets_manager.stock_trade(
            team=self.team,
            trade_type=self.trade_type,
            stock=self.selected_stock_index,
            quantity=self.quantity_field_value,
            user=self.user_name
        )

        discord_ui: DiscordUI = self.bot.get_cog("DiscordUI")
        await discord_ui.send_notification(
            log_type="StockChange",
            team=self.team,
            user=self.user_name,
            trade_type=self.trade_type,
            stock=self.selected_stock_index,
            quantity=self.quantity_field_value,
            display_value=display_value
        )
        await discord_ui.update_alteration_log()
        await discord_ui.update_asset_ui(team=self.team)

    @ui.button(
        label="取消交易",
        style=ntd.ButtonStyle.red,
        emoji="✖️",
        row=4
    )
    async def cancel_button_callback(
        self,
        button: ui.button,
        interaction: ntd.Interaction
    ):
        """取消按鈕callback。
        """

        MarketFunctionView.remove_trading_user(interaction.user.id)
        self.clear_items()
        await interaction.response.edit_message(
            content="**已取消交易**",
            embed=None,
            delete_after=5,
            view=self
        )
        self.stop()


class TradeStockSelect(ui.StringSelect):
    """選取買賣別後選取商品。
    """

    __slots__ = ("original_view", "stock_inv")

    def __init__(
            self,
            original_view: TradeView
    ):
        self.original_view = original_view
        if(original_view.trade_type == "買進"):
            super().__init__(
                placeholder="選擇商品",
                options=[
                    ntd.SelectOption(
                        label=get_stock_name_symbol(i),
                        value=str(i)
                    ) for i in range(10)
                ],
                row=2
            )
        elif(original_view.trade_type == "賣出"):
            super().__init__(
                placeholder="選擇庫存",
                options=[
                    ntd.SelectOption(
                        label=get_stock_name_symbol(int(i)),
                        value=i
                    ) for i in self.original_view.stock_inv.keys()
                ],
                row=2
            )
    
    async def callback(self, interaction: ntd.Interaction):    
        self.original_view.selected_stock_index = int(self.values[0])
        if(self.original_view.trade_type == "買進"):
            self.original_view.trade_field_value = get_stock_name_symbol(
                self.original_view.selected_stock_index
            )
        elif(self.original_view.trade_type == "賣出"):
            self.original_view.trade_field_name = "已選擇的庫存股票"
            self.original_view.trade_field_value = inventory_to_string(
                self.original_view.stock_inv, self.values[0]
            )
        await interaction.response.edit_message(
            view=self.original_view,
            embed=self.original_view.status_embed()
        )


class TradeQuantityInput(ui.Modal):
    """按下「設定張數」按鈕後彈出的文字輸入視窗。
    """
    
    __slots__ = ("original_view", "quantity")

    def __init__(self, original_view: TradeView):
        super().__init__(title="請輸入交易張數")

        self.original_view = original_view

        self.quantity = ui.TextInput(
            label="請輸入張數",
            style=ntd.TextInputStyle.short,
            min_length=1,
            max_length=3,
            required=True,
            default_value=1,
            placeholder="輸入張數"
        )
        self.add_item(self.quantity)
    
    async def callback(self, interaction: ntd.Interaction):
        try:
            self.original_view.quantity_field_value = int(self.quantity.value)

            if(self.original_view.quantity_field_value < 0):
                raise ValueError
            
            await interaction.response.edit_message(
                embed=self.original_view.status_embed(),
                view=self.original_view
            )
        except ValueError:  # 防呆(輸入文字或負數)
            await interaction.response.send_message(
                content="**張數請輸入正整數!!!**",
                delete_after=5,
                ephemeral=True
            )
        self.stop()


class FinancialStatementView(ui.View):
    """財務報表檢視 View。
    """

    ROUND_TO_QUARTER: Dict[int, str] = {
        int(r): q for r, q in access_file.read_file("game_config")["ROUND_TO_QUARTER"].items()
    }
    RAW_STOCK_DATA: RawStockData = access_file.read_file("raw_stock_data")

    def __init__(self):
        super().__init__(timeout=None)
    
    @classmethod
    def query_financial_statements(cls, index_: int) -> List[FinancialStatement]:
        """查詢報表。
        """

        round_: int = access_file.read_file("game_state")["round"]

        if(round_ == 0):
            end = 1
        else:
            end = round_
        return [
            cls.RAW_STOCK_DATA[cls.ROUND_TO_QUARTER[r]][index_] for r in range(1, end+1)
        ]
    
    def initial_message(self) -> str:
        """叫出此 View十顯示的初始訊息。
        """

        return "⬇️請選擇要查詢的公司"

    def financial_statement_format(self, selected_stock_index: int) -> str:
        """財務報表格式。
        """

        statements = FinancialStatementView.query_financial_statements(selected_stock_index)
        output: str = f"## {get_stock_name_symbol(selected_stock_index)} 財務報表\n"
        for quarter, statement in zip(
            FinancialStatementView.ROUND_TO_QUARTER.values(), statements
        ):
            output += f"### {quarter}\n" \
                      f"```銷貨淨額 {statement['net_revenue']:>10,}\n" \
                      f"銷貨毛額 {statement['gross_income']:>10,}\n" \
                      f"營業收入 {statement['income_from_operating']:>10,}\n" \
                      f"本期損益 {statement['net_income']:>10,}\n\n" \
                      f"每股盈餘(EPS) {statement['eps']:.2f}\n" \
                      f"每股盈餘年增率 {statement['eps_qoq']*100:.2f}%```\n"
        return output
    
    @ui.select(
        placeholder="選擇查詢的公司",
        options=[
            ntd.SelectOption(
                label=get_stock_name_symbol(i),
                value=str(i)
            ) for i in range(10)
        ],
        row=0
    )
    async def company_select_callback(
        self,
        select: ui.StringSelect,
        interaction: ntd.Interaction
    ):
        """選擇公司 callback。
        """

        await interaction.response.edit_message(
            content=self.financial_statement_format(int(select.values[0]))
        )
    
    @ui.button(
        label="關閉查詢",
        style=ntd.ButtonStyle.red,
        emoji="✖️",
        row=1
    )
    async def close_button_callback(
        self,
        button: ui.Button,
        interaction: ntd.Interaction
    ):
        """關閉按鈕 callback。
        """

        MarketFunctionView.querying_user_ids.remove(interaction.user.id)
        self.clear_items()
        await interaction.response.edit_message(
            content="已關閉查詢。",
            view=self,
            delete_after=5
        )
        self.stop()


class DepositFunctionView(ui.View):
    """小隊收支 View。
    """

    __slots__ = ("bot")

    changing_user_ids: List[int] = []   # 存放使用「變更小隊存款」的使用者id
    transfering_user_ids: List[int] = []    # 存放使用「過路費轉帳」的使用者id

    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @classmethod
    def add_changing_user(cls, user_id: int):
        """將使用者加入`changing_user_ids`中。
        """

        cls.changing_user_ids.append(user_id)
    
    @classmethod
    def remove_changing_user(cls, user_id: int):
        """將交易結束的使用者從`changing_user_ids`中移除。
        """

        cls.changing_user_ids.remove(user_id)

    @classmethod
    def add_transfering_user(cls, user_id: int):
        """將使用者加入`transfering_user_ids`中。
        """

        cls.transfering_user_ids.append(user_id)
    
    @classmethod
    def remove_transfering_user(cls, user_id: int):
        """將交易結束的使用者從`transfering_user_ids`中移除。
        """

        cls.transfering_user_ids.remove(user_id)

    def embed_message(self) -> ntd.Embed:
        """嵌入訊息。
        """

        time = datetime.now()
        time = time.strftime("%m/%d %I:%M%p")

        embed = ntd.Embed(
            color=PURPLE,
            title="變更小隊存款"
        )
        # embed.add_field(name="功能介紹", value="")
        embed.add_field(
            name="功能介紹",
            value="➕**增加存款**\n" \
                  "增加指定小隊的存款額"
        )
        embed.add_field(
            name="",
            value="➖**減少存款**\n" \
                  "減少指定小隊的存款額"
        )
        embed.add_field(
            name="",
            value="🔑**更改存款額**\n" \
                  "直接更改指定小隊的存款額"
        )
        embed.set_footer(
            text=f"按下按鈕以變更小隊存款 • {time}"
        )

        return embed
    
    @ui.button(
        label="變更小隊存款",
        style=ntd.ButtonStyle.gray,
        emoji="⚙️"
    )
    async def change_deposit_button_callback(
        self,
        button: ui.Button,
        interaction: ntd.Interaction
    ):
        
        if(interaction.user.id in DepositFunctionView.changing_user_ids):    # 防止重複呼叫功能
            await interaction.response.send_message(
                content="**已開啟變更小隊存款選單!!!**",
                delete_after=5,
                ephemeral=True
            )
            return

        DepositFunctionView.add_changing_user(interaction.user.id)
        view = DepositChangeView(
            user_name=interaction.user.display_name,
            user_icon=interaction.user.display_avatar,
            bot=self.bot
        )
        await interaction.response.send_message(
            embed=view.status_embed(),
            view=view,
            ephemeral=True
        )

    @ui.button(
        label="轉帳",
        style=ntd.ButtonStyle.gray,
        emoji="💸"
    )
    async def transfer_button_callback(
        self,
        button: ui.Button,
        interaction: ntd.Interaction
    ):
        
        if(interaction.user.id in DepositFunctionView.transfering_user_ids):    # 防止重複呼叫功能
            await interaction.response.send_message(
                content="**已開啟轉帳選單!!!**",
                delete_after=5,
                ephemeral=True
            )
            return

        DepositFunctionView.add_transfering_user(interaction.user.id)
        view = DepositTransferView(
            user_name=interaction.user.display_name,
            user_icon=interaction.user.display_avatar,
            bot=self.bot
        )
        await interaction.response.send_message(
            embed=view.status_embed(),
            view=view,
            ephemeral=True
        )
        

class DepositChangeView(ui.View):
    """變更小隊存款更能View。
    """

    __slots__ = (
        "embed_title",
        "embed_description",
        "mode_field_value",
        "amount",
        "user_name",
        "user_icon",
        "selected_team",
        "selected_team_deposit",
        "selected_mode",
        "bot"
    )
    # 更改模式轉換標籤
    CHANGE_MODE_TO_LABEL: Dict[ChangeMode, str] = {
        "Deposit": "增加存款",
        "Withdraw": "減少存款",
        "Change": "更改存款餘額"
    }

    def __init__(
            self,
            *,
            user_name: str,
            user_icon: ntd.Asset,
            bot: commands.Bot
    ):
        super().__init__(timeout=None)
        # embed message
        self.embed_title: str = "變更小隊存款"  # 變更第n小隊存款
        self.embed_description: str = "請選擇小隊"
        self.mode_field_value: str = "請選擇變更模式"
        self.amount: str | int = "請輸入金額"   # 金額: int
        self.user_name = user_name
        self.user_icon = user_icon
        # slect status
        self.selected_team: int | None = None
        self.selected_team_deposit: int | None = None # 該小隊目前存款
        self.selected_mode: ChangeMode | None = None
        # bot
        self.bot = bot

    def status_embed(self) -> ntd.Embed:
        """用於編排選單狀態訊息。
        """

        time = datetime.now()
        time = time.strftime("%I:%M%p")

        embed = ntd.Embed(
            color=PURPLE,
            title=self.embed_title,
            description=self.embed_description
        )
        embed.add_field(
            name="變更模式",
            value=self.mode_field_value
        )
        if(isinstance(self.amount, str)):
            embed.add_field(
                name="變更金額",
                value=self.amount
            )
        else:
            embed.add_field(
                name="變更金額",
                value=f"{self.amount:,}"
            )
        embed.set_footer(
            text=f"{self.user_name} | Today at {time}",
            icon_url=self.user_icon
        )

        return embed

    def input_check(self) -> bool:
        """檢查輸入資料是否完整。
        """

        if(self.selected_team is None or
           self.selected_mode is None or
           isinstance(self.amount, str)
        ):
            return False
        else:
            return True

    @ui.select(
        placeholder="選擇小隊",
        options=[
            ntd.SelectOption(
                label=f"第{t}小隊",
                value=str(t)
            )
            for t in range(1, NUMBER_OF_TEAMS+2)   # +1 (Testing team)
        ],
        row=0
    )
    async def team_select_callback(
        self,
        select: ui.StringSelect, 
        interaction: ntd.Interaction
    ):
        """小隊選取選單callback。
        """

        self.selected_team = int(select.values[0])
        self.embed_title = f"變更第{select.values[0]}小隊存款"
        self.selected_team_deposit = get_deposit(self.selected_team)
        self.embed_description = \
            f"第{select.values[0]}小隊目前存款: " \
            f"{self.selected_team_deposit:,}"

        await interaction.response.edit_message(
            embed=self.status_embed()
        )
   
    @ui.select(
        placeholder="選擇變更模式",
        options=[
            ntd.SelectOption(
                label="增加存款",
                value="Deposit",
                description="輸入增加的金額。",
                emoji="➕"
            ),
            ntd.SelectOption(
                label="減少存款",
                value="Withdraw",
                description="輸入減少的金額。",
                emoji="➖"
            ),
            ntd.SelectOption(
                label="更改存款餘額",
                value="Change",
                description="輸入改變的餘額。",
                emoji="🔑"
            )
        ],
        row=1
    )
    async def mode_select_callback(
        self,
        select: ui.StringSelect, 
        interaction: ntd.Interaction
    ):
        """模式選取選單callback。
        """

        self.selected_mode = select.values[0]
        
        self.mode_field_value = DepositChangeView.CHANGE_MODE_TO_LABEL[
            self.selected_mode
        ]
        await interaction.response.edit_message(
            embed=self.status_embed(),
        )

    @ui.button(
        label="輸入金額",
        style=ntd.ButtonStyle.blurple,
        emoji="🪙",
        row=2
    )
    async def input_amount_button_callback(
        self,
        button: ui.Button,
        interaction: ntd.Interaction
    ):
        """輸入金額按鈕callback。
        """

        await interaction.response.send_modal(AmountInput(self))

    @ui.button(
        label="確認送出",
        style=ntd.ButtonStyle.green,
        emoji="✅",
        row=3
    )
    async def comfirm_button_callback(
        self,
        button: ui.Button,
        interaction: ntd.Interaction
    ):
        """確認送出按扭callback。
        """
        
        if(not self.input_check()): # 檢查資料都填齊
            await interaction.response.send_message(
                    content="**輸入資料不完整!!!**",
                    delete_after=5,
                    ephemeral=True
                )
            return
        # 檢查小隊金額是否足夠
        self.selected_team_deposit = get_deposit(self.selected_team)
        if(self.selected_mode == "Withdraw" and
            self.selected_team_deposit < self.amount):   # 此小隊金額不足扣繳
            await interaction.response.send_message(
                content=f"**第{self.selected_team}小隊帳戶餘額不足!!!**",
                delete_after=5,
                ephemeral=True
            )
            return
        
        # 改變成功訊息
        self.clear_items()
        await interaction.response.edit_message(
            content="**改變成功!!!**",
            embed=None,
            view=self,
            delete_after=5,
        )
        DepositFunctionView.remove_changing_user(interaction.user.id)
        # 變更第n小隊存款
        assets_manager: AssetsManager = self.bot.get_cog("AssetsManager")
        assets_manager.change_deposit(   
            team=self.selected_team,  
            change_mode=self.selected_mode,
            amount=self.amount,
            user=self.user_name
        )
        # 更新小隊資產
        discord_ui: DiscordUI = self.bot.get_cog("DiscordUI")
        await discord_ui.update_asset_ui(team=self.selected_team)
        # 發送即時通知
        await discord_ui.send_notification(
            log_type="DepositChange",
            team=self.selected_team,
            user=self.user_name,
            change_mode=self.selected_mode,
            amount=self.amount
        )
        # 更新收支紀錄
        await discord_ui.update_alteration_log()
        self.stop()
    
    @ui.button(
        label="取消",
        style=ntd.ButtonStyle.red,
        emoji="✖️",
        row=3
    )
    async def cancel_button_callback(
        self,
        button: ui.button,
        interaction: ntd.Interaction
    ):
        """取消按鈕callback。
        """

        DepositFunctionView.remove_changing_user(interaction.user.id)
        self.clear_items()
        await interaction.response.edit_message(
            content="**已取消變更**",
            embed=None,
            delete_after=5,
            view=self
        )
        self.stop()


class DepositTransferView(ui.View):
    """轉帳功能 View。
    """

    __slots__ = (
        "user_name",
        "user_icon",
        "transfer_team",
        "t_team_deposit",
        "d_team_deposit",
        "deposit_team",
        "amount",
        "bot"
    )

    def __init__(
            self,
            *,
            user_name: str,
            user_icon: ntd.Asset,
            bot: commands.Bot
    ):
        super().__init__(timeout=None)
        self.user_name = user_name
        self.user_icon = user_icon
        # select status
        self.transfer_team: str = "請選擇轉出小隊"
        self.t_team_deposit: int | None = None    # 轉出小隊目前存款額
        self.deposit_team: str = "請選擇轉入小隊"
        self.d_team_deposit: int | None = None    # 轉入小隊目前存款額
        self.amount: int | str = "請輸入轉帳金額"
        # bot
        self.bot = bot

    def status_embed(self) -> ntd.Embed:
        """用於編排選單狀態訊息。
        """

        time = datetime.now()
        time = time.strftime("%I:%M%p")

        embed = ntd.Embed(
            color=PURPLE,
            title="過路費轉帳"
        )
        # 轉出小隊
        if(self.t_team_deposit is None):
            field_value = self.transfer_team
        else:
            field_value = f"第{self.transfer_team}小隊\n" \
                          f"帳戶餘額: {self.t_team_deposit:,}"
        embed.add_field(
            name="轉出小隊",
            value=field_value
        )
        # 轉入小隊
        if(self.d_team_deposit is None):
            field_value = self.deposit_team
        else:
            field_value = f"第{self.deposit_team}小隊\n" \
                          f"帳戶餘額: {self.d_team_deposit:,}"
        embed.add_field(
            name="轉入小隊",
            value=field_value
        )
        # 轉帳金額
        embed.add_field(
            name="轉帳金額",
            value=self.amount,
            inline=False
        )
        embed.set_footer(
            text=f"{self.user_name} | Today at {time}",
            icon_url=self.user_icon
        )
        return embed

    def input_check(self) -> bool:
        """檢查輸入資料是否完整。
        """

        if(self.d_team_deposit is None or
           self.t_team_deposit is None or 
           isinstance(self.amount, str) or
           self.amount == 0 # 轉帳金額不可為0
        ):
            return False
        else:
            return True

    @ui.select(
        placeholder="選擇轉出小隊",
        options=[
            ntd.SelectOption(
                label=f"第{t}小隊",
                value=str(t)
            ) for t in range(1, NUMBER_OF_TEAMS+2)  # +1 (Testing team)
        ],
        row=0
    )
    async def transfer_team_select_callback(
        self,
        select: ui.StringSelect,
        interaction: ntd.Interaction
    ):
        """選取轉出小隊 callback。
        """

        self.transfer_team = select.values[0]
        self.t_team_deposit = get_deposit(self.transfer_team)
        await interaction.response.edit_message(
            embed=self.status_embed()
        )

    @ui.select(
        placeholder="選擇轉入小隊",
        options=[
            ntd.SelectOption(
                label=f"第{t}小隊",
                value=str(t)
            ) for t in range(1, NUMBER_OF_TEAMS+2)  # +1 (Testing team)
        ],
        row=1
    )
    async def deposit_team_select_callback(
        self,
        select: ui.StringSelect,
        interaction: ntd.Interaction
    ):
        """選取轉入小隊 callback。
        """

        self.deposit_team = select.values[0]
        self.d_team_deposit = get_deposit(self.deposit_team)
        await interaction.response.edit_message(
            embed=self.status_embed()
        )

    @ui.button(
    label="輸入金額",
    style=ntd.ButtonStyle.blurple,
    emoji="🪙",
    row=2
    )
    async def input_amount_button_callback(
        self,
        button: ui.Button,
        interaction: ntd.Interaction
    ):
        """輸入金額按鈕callback。
        """

        await interaction.response.send_modal(AmountInput(self))

    @ui.button(
        label="確認轉出",
        style=ntd.ButtonStyle.green,
        emoji="✅",
        row=3
    )
    async def comfirm_button_callback(
        self,
        button: ui.Button,
        interaction: ntd.Interaction
    ):
        """確認轉出按鈕 callback。
        """

        if(not self.input_check()): # 檢查資料都填齊
            await interaction.response.send_message(
                    content="**輸入資料不完整!!!**",
                    delete_after=5,
                    ephemeral=True
                )
            return
        # 檢查轉出小隊金額是否足夠
        self.t_team_deposit = get_deposit(self.transfer_team)
        if(self.t_team_deposit < self.amount):
            await interaction.response.send_message(
                content=f"**第{self.transfer_team}小隊帳戶餘額不足!!!**",
                delete_after=5,
                ephemeral=True
            )
            return
        # 不可轉帳給同個小隊
        if(self.transfer_team == self.deposit_team):
            await interaction.response.send_message(
                content="**不可轉帳給同個小隊!!!**",
                delete_after=5,
                ephemeral=True
            )
            return
        
        # 轉帳成功訊息
        self.clear_items()
        await interaction.response.edit_message(
            content="**轉帳成功**",
            embed=None,
            view=self,
            delete_after=5
        )
        DepositFunctionView.remove_transfering_user(interaction.user.id)
        # Transfer
        assets_manager: AssetsManager = self.bot.get_cog("AssetsManager")
        assets_manager.transfer(
            transfer_deposit_teams=(self.transfer_team, self.deposit_team),
            amount=self.amount,
            user=self.user_name
        )
        
        discord_ui: DiscordUI = self.bot.get_cog("DiscordUI")
        # Update Asset UI
        await discord_ui.update_asset_ui(team=self.transfer_team)
        await discord_ui.update_asset_ui(team=self.deposit_team)
        # Send Notification
        await discord_ui.send_notification(
            log_type="Transfer",
            team=(self.transfer_team, self.deposit_team),
            user=self.user_name,
            amount=self.amount
        )
        await discord_ui.update_alteration_log()
        self.stop()

    @ui.button(
        label="取消",
        style=ntd.ButtonStyle.red,
        emoji="✖️",
        row=3
    )
    async def cancel_button_callback(
        self,
        button: ui.button,
        interaction: ntd.Interaction
    ):
        """取消按鈕callback。
        """

        DepositFunctionView.remove_transfering_user(interaction.user.id)
        self.clear_items()
        await interaction.response.edit_message(
            content="**已取消轉帳**",
            embed=None,
            delete_after=5,
            view=self
        )
        self.stop()


class LiquidationView(ui.View):
    """清算功能 View。
    """

    __slots__ = (
        "user_name",
        "user_icon"
    )

    def __init__(
            self,
            *,
            user_name: str,
            user_icon: ntd.Asset,
            bot: commands.Bot
    ):
        super().__init__(timeout=None)
        self.user_name = user_name
        self.user_icon = user_icon
        # Select status
        # Bot
        self.bot = bot


class AmountInput(ui.Modal):
    """金額輸入視窗。
    """

    __slots__ = ("original_view", "amount")

    def __init__(
            self,
            original_view: DepositChangeView | DepositTransferView,
            default_value: str | None = None
    ):
        super().__init__(title="請輸入金額")

        self.original_view = original_view

        self.amount = ui.TextInput(
            label="請輸入金額",
            style=ntd.TextInputStyle.short,
            min_length=1,
            max_length=6,
            required=True,
            default_value=default_value,
            placeholder="輸入金額"
        )
        self.add_item(self.amount)

    async def callback(self, interaction: ntd.Interaction):
        try:
            self.original_view.amount = int(self.amount.value)
            
            if(self.original_view.amount < 0):
                raise ValueError
            
            await interaction.response.edit_message(
                embed=self.original_view.status_embed()
            )
        except ValueError:  # 防呆(輸入文字或負數)
            await interaction.response.send_message(
                content="**金額請輸入正整數!!!**",
                delete_after=5,
                ephemeral=True
            )
        self.stop()


class LogEmbed(ntd.Embed):
    """收支紀錄 Embed Message。
    """

    def __init__(self):
        super().__init__(
            color=PURPLE,
            title="收支紀錄",
            description="小隊存款金額的變動以及\n買賣股票最近的25筆紀錄"
        )

        log: AlterationLog = access_file.read_file("alteration_log").copy()
        serial: int = log.pop("serial")
        # 將所有字典展開為一list並按照serial排序
        record_list: List[LogData] = sorted(
            [item for sublist in log.values() for item in sublist],
            key=lambda x: x["serial"]
        )
        # 只列出最近的25個紀錄
        start_index: int = 0 if serial < 25 else serial-25
        record_list = record_list[start_index:]

        for record in record_list:
            if(record["log_type"] == "DepositChange"):
                field_name = f"#{record['serial']} {record['user']} 在 {record['time']}\n" \
                             f"變更第{record['team']}小隊存款"
                field_value = f"{record['original_deposit']:,} {u'\u2192'} {record['changed_deposit']:,}"
            elif(record["log_type"] == "Transfer"):
                field_name = f"#{record['serial']} {record['user']} 在 {record['time']}\n" \
                            f"進行轉帳"
                field_value = f"轉出 第{record['team'][0]}小隊存款\n" \
                              f"{record['original_deposit'][0]} {u'\u2192'} {record['changed_deposit'][0]}\n" \
                              f"轉入 第{record['team'][1]}小隊存款\n" \
                              f"{record['original_deposit'][1]} {u'\u2192'} {record['changed_deposit'][1]}"
            elif(record["log_type"] == "StockChange"):
                field_name = f"#{record['serial']} {record['user']} 在 {record['time']}\n" \
                             f"{record['trade_type']} 第{record['team']}小隊股票"
                field_value = f"商品: {record['stock']} 張數: {record['quantity']}"
            
            self.add_field(
                name=field_name,
                value=field_value,
                inline=False
            )
        
        self.set_footer(
            text=f"資料更新時間: {datetime.now().strftime("%m/%d %I:%M%p")}"
        )


class DepositChangeNotificationEmbed(ntd.Embed):
    """資產變更即時通知 Embed Message。
    """

    def __init__(
            self,
            *,
            user: str,
            change_mode: ChangeMode,
            amount: int
    ):

        title = {
            "Deposit": "🔔即時入帳通知🔔",
            "Withdraw": "💸F-pay消費通知💸",
            "Change": "🔑帳戶額變更通知🔑"
        }[change_mode]
        description = {
            "Deposit": f"關主: {user} 已將 **FP${amount:,}** 匯入帳戶!",
            "Withdraw": f"關主: {user} 已將 **FP${amount:,}** 從帳戶中扣除!",
            "Change": f"關主: {user} 已改變帳戶餘額為 **$FP{amount:,}** !"
        }[change_mode]

        super().__init__(
            color=PURPLE,
            title=title,
            description=description
        )
        self.set_footer(
            text=f"{datetime.now().strftime("%m/%d %I:%M%p")}"
        )


class TransferNotificationEmbed(ntd.Embed):
    """轉帳即時通知 Embed Message。
    """

    def __init__(
            self,
            *,
            user: str,
            amount: int,
            deposit_team: str | None = None,
            transfer_team: str | None = None
    ):
        """根據 `deposit_team` 以及 `transfer_team` 來判斷此為「轉出小隊」或「轉入小隊」之通知。
        """

        if(isinstance(deposit_team, str)):
            title = "💸轉帳通知💸"
            description = f"已將 **FP${amount:,}** 轉入 第{deposit_team}小隊 帳號!\n" \
                          f"關主: {user}"
        elif(isinstance(transfer_team, str)):
            title = "🔔即時入帳通知🔔"
            description = f"已收到 第{transfer_team}小隊 帳款 **FP${amount:,}** !\n" \
                          f"關主: {user}"
        super().__init__(
            color=PURPLE,
            title=title,
            description=description
        )
        self.set_footer(
            text=f"{datetime.now().strftime("%m/%d %I:%M%p")}"
        )


class StockChangeNoticeEmbed(ntd.Embed):
    """股票庫存變更即時通知 Embed Message。
    """

    def __init__(
            self,
            *,
            user: str,
            trade_type: TradeType,
            stock: int,
            quantity: int,
            display_value: int
    ):
        stock = get_stock_name_symbol(stock)
        title = "📊股票成交通知📊"
        description = {
            "買進": f"隊輔: {user} 成功買進**{stock} {quantity}張!**\n" \
                    f"投資成本: **$FP{display_value:,}**",
            "賣出": f"隊輔: {user} 成功賣出**{stock} {quantity}張!**\n" \
                    "總投資損益: " + ("**__利益__**" if display_value >= 0 else "**__損失__**") + f" **$FP{abs(display_value):,}**"
        }[trade_type]

        super().__init__(
            color=PURPLE,
            title=title,
            description=description
        )
        self.set_footer(
            text=f"{datetime.now().strftime("%m/%d %I:%M%p")}"
        )


class TeamAssetEmbed(ntd.Embed):
    """小隊資產狀態 Embed Message，包含存款、總收益以及持股狀況。
    """

    def __init__(self, team: int):
        super().__init__(
            color=PURPLE,
            title=f"第{team}小隊 F-pay帳戶"
        )
        self.deposit_embed_format(team)
        self.stock_embed_format(team)

    @staticmethod
    def get_profit_lost(value: int) -> str:
        """判斷利益、持平或損失。
        """

        if(value > 0):
            return "__利益__"
        elif(value == 0):
            return "__持平__"
        else:
            return "__損失__"

    def deposit_embed_format(self, team: int):
        """存款、總收益格式。
        """

        asset_data: AssetDict = access_file.read_file("team_assets")[f"{team}"]
        self.add_field(
            name="",
            value=f"**存款: {asset_data['deposit']:,}**"
        )
        self.add_field(
            name="",
            value=f"**總收益: {asset_data['revenue']:,}**"
        )
    
    def stock_embed_format(self, team: int):
        """持股狀況格式。
        """

        stock_inv = get_stock_inventory(team)
        if(stock_inv):
            total_unrealized_gain_loss = 0
            fields: List[str] = []
            for stock_idx, stocks in stock_inv.items():
                pice: int = len(stocks) # 持有張數
                total_cost: int = sum(stocks)   # 投資總成本
                avg_price: float = round(total_cost / (pice*1000), 2)   # 成交均價
                unrealized_gain_loss: int = (round(get_stock_price(stock_idx), 2)
                                             - avg_price) * pice * 1000
                total_unrealized_gain_loss += unrealized_gain_loss  # 未實現總損益
                fields.append(
                    f"**{get_stock_name_symbol(stock_idx)}**" \
                    f"持有張數: {pice}\n" \
                    f"成交均價: {avg_price:.2f}\n" \
                    f"投資總成本: {total_cost:,}\n" \
                    f"未實現損益: {self.get_profit_lost(unrealized_gain_loss)} {abs(unrealized_gain_loss):,.0f}\n" \
                )
            self.add_field(
                name=f"**未實現總損益:** " \
                     f"{self.get_profit_lost(total_unrealized_gain_loss)} " \
                     f"**{abs(total_unrealized_gain_loss):,.0f}**",
                value="",
                inline=False
            )
            for field in fields:
                self.add_field(
                    name="",
                    value=field
                )
        else:
            self.add_field(
                name="股票庫存",
                value="**未實現總損益:** 0\n",
                inline=False
            )
            self.add_field(
                name="",
                value="無股票庫存",
                inline=False
            )
            

class NewsEmbed(ntd.Embed):
    """新聞 Embed Message。
    """

    def __init__(self, title: str, content: str):
        super().__init__(
            color=PURPLE,
            title=title,
            description=content,
            timestamp=datetime.now()
        )


class DiscordUI(commands.Cog):
    """控制Discord端的UI介面。
    """

    __slots__ = (
        "bot",
        "CONFIG",
        "CHANNEL_IDS",
        "MESSAGE_IDS",
        "ALTERATION_LOG_MESSAGE",
        "STOCK_MARKET_MESSAGE",
        "NEWS_FEED_CHANNEL"
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.CONFIG: Config = access_file.read_file("game_config")
        self.CHANNEL_IDS: ChannelIDs = self.CONFIG["channel_ids"]
        self.MESSAGE_IDS: MessageIDs = self.CONFIG["message_ids"]
        
        self.ALTERATION_LOG_MESSAGE: ntd.Message = None
        self.STOCK_MARKET_MESSAGE: ntd.Message = None
        self.NEWS_FEED_CHANNEL: ntd.TextChannel = None
        
    @commands.Cog.listener()
    async def on_ready(self):
        """DiscordUI啟動程序。

        `RESET_UI`
        重製所有ui元素訊息(View、Button)

        `CLEAR_LOG`
        清除已發送的小隊即時訊息以及清除收支紀錄，
        並清除log資料。

        `UPDATE_ASSET`
        更新各小隊資產狀況訊息。
        """

        NEW_GAME: bool = self.CONFIG["NEW_GAME"]
        RESET_UI: bool = self.CONFIG["RESET_UI"]
        CLEAR_LOG: bool = self.CONFIG["CLEAR_LOG"]
        UPDATE_ASSET: bool = self.CONFIG["UPDATE_ASSET"]
        if(RESET_UI):
            await self.reset_all_ui()

        if(UPDATE_ASSET):
            await self.update_asset_ui()
        
        if(NEW_GAME and CLEAR_LOG):
            await self.clear_log()
        else:
            await self.update_alteration_log()

        await self.fetch_alteration_log_message()
        await self.fetch_news_feed_channel()
        await self.fetch_stock_market_message()

        await self.update_market_ui()

        print("Loaded discord_ui")

    @commands.command()
    async def test_ui_com(self, ctx: commands.Context):

        channel = self.bot.get_channel(1243503969032998973)
        # delete old message
        await channel.purge(limit=1)
        # prompt
        await channel.send("message")
        

    @ntd.slash_command(
            name="test_ui",
            description="For testing UIs",
            guild_ids=[1218130958536937492]
    )
    async def test_ui(self, interaction: ntd.Interaction):
        DepositFunctionView.add_transfering_user(interaction.user.id)
        view = DepositTransferView(
            user_name=interaction.user.display_name,
            user_icon=interaction.user.display_avatar,
            bot=self.bot
        )
        await interaction.response.send_message(
            embed=view.status_embed(),
            view=view,
            ephemeral=True
        )
    
    @staticmethod
    def stock_market_message() -> str:
        """市場動態訊息格式。
        """

        market_data: List[StockDict] = access_file.read_file("market_data")
        # title
        output: List[str] = [f"```商品名稱　{'代碼':^5}產業{'成交':^7}漲跌\n"]
        # string formatter
        for init_data, stock in zip(INITIAL_STOCK_DATA, market_data):
            delta_price: float = stock["price"] - stock["close"]
            # up and downs index
            if(delta_price > 0):    # up
                price_index = "🔴"  
            elif(delta_price < 0):  # down
                price_index = "🟢"
            else:
                price_index = "⚪"

            output.append(f"{init_data['name'].ljust(5, '　')}{init_data['symbol']:^6}" \
                          f"{init_data['sector']:3}{stock['price']:5.2f} {price_index}{abs(delta_price):.2f}\n"
            )     
        output.append("```")
        return "".join(output)

    async def reset_all_ui(self):
        """|coro|

        重置有ui元素的訊息，包括:

        `ChangeDepositButton`: 變更小隊存款按鈕；
        """
        
        # ChangeDepositButton
        channel = self.bot.get_channel(
            self.CHANNEL_IDS["CHANGE_DEPOSIT"]
        )
        message = await channel.fetch_message(
            self.MESSAGE_IDS["CHANGE_DEPOSIT"]
        )
        view = DepositFunctionView(self.bot)
        await message.edit(
            embed=view.embed_message(),
            view=view
        )
        # TradeButton
        channel = self.bot.get_channel(
            self.CHANNEL_IDS["STOCK_MARKET"]
        )
        message = await channel.fetch_message(
            self.MESSAGE_IDS["TRADE_VIEW"]
        )
        view = MarketFunctionView(self.bot)
        await message.edit(
            content=None,
            view=view
        )

    async def clear_log(self):
        """|coro|
        
        清除已發送的小隊即時訊息以及清除收支紀錄，並清除log資料。
        """

        log: AlterationLog = access_file.read_file("alteration_log")

        # 清除各小隊即時訊息
        for team, team_key in enumerate(self.MESSAGE_IDS["ASSET_MESSAGE_IDS"].keys(), start=1):
            channel = self.bot.get_channel(
                self.CHANNEL_IDS[team_key]["NOTICE"]
            )

            if(log.get(str(team), None) is None):  # 有記錄才需要刪
                continue
            
            msg_count = len(log[f"{team}"])
            await channel.purge(limit=msg_count)
        
        # 清除log資料
        access_file.clear_log_data()
        # 更新log
        await self.update_alteration_log()

    async def fetch_alteration_log_message(self):
        """抓取ALTERATION_LOG_MESSAGE。
        """

        channel = self.bot.get_channel(
            self.CHANNEL_IDS["ALTERATION_LOG"]
        )
        self.ALTERATION_LOG_MESSAGE = await channel.fetch_message(
            self.MESSAGE_IDS["ALTERATION_LOG"]
        )
       
    async def fetch_stock_market_message(self):
        """抓取STOCK_MARKET。
        """

        channel = self.bot.get_channel(
            self.CHANNEL_IDS["STOCK_MARKET"]
        )
        self.STOCK_MARKET_MESSAGE = await channel.fetch_message(
            self.MESSAGE_IDS["STOCK_MARKET"]
        )

    async def update_alteration_log(self):
        """|coro|

        更新收支紀錄。
        """
                
        if(self.ALTERATION_LOG_MESSAGE is None):  # 防止資料遺失
            await self.fetch_alteration_log_message()

        await self.ALTERATION_LOG_MESSAGE.edit(
            content=None,
            embed=LogEmbed()
        )

    async def send_notification(
            self,
            *,
            log_type: LogType,
            team: Tuple[str, str] | str | int,
            user: str,
            change_mode: ChangeMode | None = None,
            amount: int | None = None,
            trade_type: TradeType | None = None,
            stock: int | None = None,
            quantity: int | None = None,
            display_value: int | None = None
    ):
        """|coro|

        發送即時通知。
        """

        if(log_type == "Transfer"):
            transfer_team, deposit_team = team
            channel = self.bot.get_channel(
                self.CHANNEL_IDS[f"TEAM_{transfer_team}"]["NOTICE"]
            )
            await channel.send( # 轉出小隊之通知
                embed=TransferNotificationEmbed(
                    user=user,
                    amount=amount,
                    deposit_team=deposit_team
                )
            )
            channel = self.bot.get_channel( # 轉入小隊之通知
                self.CHANNEL_IDS[f"TEAM_{deposit_team}"]["NOTICE"]
            )
            await channel.send(
                embed=TransferNotificationEmbed(
                    user=user,
                    amount=amount,
                    transfer_team=transfer_team
                )
            )
            return
        
        channel = self.bot.get_channel(
            self.CHANNEL_IDS[f"TEAM_{team}"]["NOTICE"]
        )
        if(log_type == "DepositChange"):
            await channel.send(
                embed=DepositChangeNotificationEmbed(
                    user=user,
                    change_mode=change_mode,
                    amount=amount
                )
            )
        elif(log_type == "StockChange"):
            await channel.send(
                embed=StockChangeNoticeEmbed(
                    user=user,
                    trade_type=trade_type,
                    stock=stock,
                    quantity=quantity,
                    display_value=display_value
                )
            )
    
    async def update_market_ui(self):
        """更新市場動態。
        """

        if(self.STOCK_MARKET_MESSAGE is None):
            await self.fetch_stock_market_message()

        await self.STOCK_MARKET_MESSAGE.edit(
            content=self.stock_market_message()
        )

    async def update_asset_ui(self, team: str | int | None = None):
        """|coro|

        任一操作改變資產時更新小隊資產狀況訊息。
        """
        
        if(team is not None):  # 更新指定小隊資產訊息
            channel = self.bot.get_channel(
                self.CHANNEL_IDS[f"TEAM_{team}"]["ASSET"]
            )
            message = await channel.fetch_message(
                self.MESSAGE_IDS["ASSET_MESSAGE_IDS"][f"TEAM_{team}"]
            )
            await message.edit(
                embed=TeamAssetEmbed(team)
            )
        else:   # 更新所有小隊資產訊息
            for team, team_key in enumerate(self.MESSAGE_IDS["ASSET_MESSAGE_IDS"].keys(), start=1):
                channel = self.bot.get_channel(
                    self.CHANNEL_IDS[team_key]["ASSET"]
                )
                message = await channel.fetch_message(
                    self.MESSAGE_IDS["ASSET_MESSAGE_IDS"][team_key]
                )
                await message.edit(
                    embed=TeamAssetEmbed(team)
                )
    
    async def fetch_news_feed_channel(self):
        """|coro|
        """

        self.NEWS_FEED_CHANNEL = self.bot.get_channel(
            self.CHANNEL_IDS["NEWS_FEED"]
        )

    async def clear_news(self):
        """|coro|

        清除「地球新聞台」所有新聞。
        """
        
        if(self.NEWS_FEED_CHANNEL is None):
            await self.fetch_news_feed_channel()
        
        game_state: GameState = access_file.read_file("game_state")
        released_news_count = game_state["released_news_count"]
        news_count: int = sum(released_news_count.values())

        if(news_count):
            await self.NEWS_FEED_CHANNEL.purge(limit=news_count)

    async def release_news(self, *, title: str, content: str):
        """|coro|

        發送新聞至「地球新聞台」頻道。
        """

        if(self.NEWS_FEED_CHANNEL is None):
            await self.fetch_news_feed_channel()

        await self.NEWS_FEED_CHANNEL.send(
            embed=NewsEmbed(title=title, content=content)
        )


def setup(bot: commands.Bot):
    bot.add_cog(DiscordUI(bot))
    