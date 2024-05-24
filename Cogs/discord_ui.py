from nextcord.ext import commands
import nextcord as ntd

from datetime import datetime
from typing import Dict, List, Any, Literal, ClassVar

from .assets_manager import AssetsManager
from .utilities import access_file
from .utilities.datatypes import (
    Config,
    ChannelIDs,
    MessageIDs,
    AssetDict,
    AlterationLog,
    LogData,
    GameState,
    InitialStockData,
    StockDict
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


def fetch_stock_name_symbol(index_: int | str) -> str:
    """抓取 "股票名 股票代碼" string。
    """
    
    index_ = int(index_)
    name = INITIAL_STOCK_DATA[index_]["name"]
    symbol = INITIAL_STOCK_DATA[index_]["symbol"]
    return f"{name} {symbol}"


def fetch_stock_inventory(team: int) -> Dict[str, List[int]] | None:
    """擷取小隊股票庫存。
    """

    asset: AssetDict = access_file.read_file("team_assets")[f"{team}"]
    stock_inv: Dict[str, List[int]] | None = asset.get("stock_inv", None)

    return stock_inv


def inventory_to_string(stock_inv: Dict[str, List[int]], index_: str | int | None = None) -> str:
    """將股票庫存資料格式化。
    """

    output: str = ""
    if(index_ is None):
        for index_, stocks in stock_inv.items():
            output += f"{INITIAL_STOCK_DATA[int(index_)]["name"]} {INITIAL_STOCK_DATA[int(index_)]["symbol"]}" \
                        f"\t張數: {len(stocks)}\n"
    else:
        output = f"{INITIAL_STOCK_DATA[int(index_)]["name"]} {INITIAL_STOCK_DATA[int(index_)]["symbol"]}" \
                 f"\t張數: {len(stock_inv[index_])}\n"
    return output


def get_stock_price(index_: int | str) -> float:
    """擷取指定股票當下的價格。
    """

    stock_dict: StockDict = access_file.read_file(
        "market_data"
    )[int(index_)]

    return stock_dict["price"]


class StockMarketEmbed(ntd.Embed):
    """市場動態 Embed Message。
    """
    
    def __init__(self):
        super().__init__(
            color=PURPLE,
            title="市場動態"
        )
        market_data: List[StockDict] = access_file.read_file("market_data")
        self.add_field(
            name=f"{"商品名稱".center(5, "　")} {"商品代碼":^5} {"產業":^5} {"成交":^5} {"漲跌":^5}",
            value="",
            inline=False
        )
        for init_data, stock in zip(INITIAL_STOCK_DATA, market_data):
            self.add_field(
                name=f"{init_data["name"].center(5, "　")} {init_data["symbol"]:^5}" \
                     f"{init_data["sector"]:^5} {stock["price"]:^5.2f} {stock["price"]-stock["close"]:^5.2f}",
                value="",
                inline=False
            )
    

class TradeButton(ntd.ui.View):
    """交易功能按鈕。
    """

    __slots__ = ("bot")

    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot
    
    @ntd.ui.button(
        label="股票交易",
        style=ntd.ButtonStyle.gray,
        emoji="📊"
    )
    async def trade_button_callback(
        self,
        button: ntd.ui.Button,
        interaction: ntd.Interaction
    ):
        view = TradeView(
            bot=self.bot,
            user_name=interaction.user.display_name,
            user_avatar=interaction.user.display_avatar,
            user_id=interaction.user.id
        )
        await interaction.response.send_message(
            embed=view.status_embed(),
            view=view,
            delete_after=180,
            ephemeral=True
        )


class TradeView(ntd.ui.View):
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
        super().__init__(timeout=180)
        self.bot = bot
        self.user_name = user_name
        self.user_avatar = user_avatar
        self.team = USER_ID_TO_TEAM[user_id]
        self.stock_inv = fetch_stock_inventory(self.team)   # 該小隊股票庫存
        # embed message
        self.embed_title: str = "股票交易"
        self.deposit: int = access_file.read_file(  # 該小隊存款額
            "team_assets"
        )[f"{self.team}"]["deposit"]
        self.trade_field_name: str = "請選擇交易別"   # 買進: 商品；賣出: 目前庫存
        self.trade_field_value: str = "請選擇商品"    # 買進: name symbol；賣出: 庫存內容
        self.quantity_field_name: str = "張數"      # 買進 or 賣出 張數
        self.quantity_field_value: str | int = "請輸入張數" # quantity
        # select status
        self.trade_type: Literal["買進", "賣出"] = None
        self.stock_select: StockSelect = None # 紀錄股票選取下拉選單
        self.selected_stock_index: int = None
    
    def status_embed(self) -> ntd.Embed:
        """用於編排嵌入訊息。
        """

        time = datetime.now()
        time = time.strftime("%I:%M%p")

        embed = ntd.Embed(
            colour=PURPLE,
            title=f"第{self.team}小隊 {self.embed_title}",
            type="rich",
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
        
    @ntd.ui.select(
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
    async def trade_select_callback(
        self,
        select: ntd.ui.StringSelect,
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
            
            self.stock_select = StockSelect(self)
            self.add_item(self.stock_select)
        elif(self.trade_type == "賣出"):
            self.embed_title = "賣出 股票交易"
            self.trade_field_name = "目前庫存"
            self.quantity_field_name = "賣出張數"

            if(self.stock_inv is None):
                self.trade_field_value = "無股票庫存"
            else:
                self.trade_field_value = inventory_to_string(
                    self.stock_inv
                )
                self.stock_select = StockSelect(self)
                self.add_item(self.stock_select)
            
        await interaction.response.edit_message(
            embed=self.status_embed(),
            view=self
        )

    @ntd.ui.button(
        label="輸入張數",
        style=ntd.ButtonStyle.blurple,
        emoji="📃",
        row=3
    )
    async def input_quantity_button_callback(
        self,
        button: ntd.ui.Button,
        interaction: ntd.Interaction
    ):
        """輸入張數按鈕callback。
        """

        await interaction.response.send_modal(InputQuantity(self))

    @ntd.ui.button(
        label="確認交易",
        style=ntd.ButtonStyle.green,
        emoji="✅",
        row=4
    )
    async def confirm_button_callback(
        self,
        button: ntd.ui.Button,
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
                content=f"**{fetch_stock_name_symbol(self.selected_stock_index)} 持有張數不足**",
                delete_after=5,
                ephemeral=True
            )
            return
        
        # stock_trade, update_log
        asset: AssetsManager = self.bot.get_cog("AssetsManager")
        await asset.stock_trade(
            team=self.team,
            trade_type=self.trade_type,
            stock=self.selected_stock_index,
            quantity=self.quantity_field_value,
            user=interaction.user.display_name
        )

        ui: DiscordUI = self.bot.get_cog("DiscordUI")
        await ui.update_asset(team=self.team)

        self.clear_items()
        await interaction.response.edit_message(
            content="**改變成功!!!**",
            embed=None,
            delete_after=5,
            view=self
        )
        self.stop()

    @ntd.ui.button(
        label="取消交易",
        style=ntd.ButtonStyle.red,
        emoji="✖️",
        row=4
    )
    async def cancel_button_callback(
        self,
        button: ntd.ui.button,
        interaction: ntd.Interaction
    ):
        """取消按鈕callback。
        """

        self.clear_items()
        await interaction.response.edit_message(
            content="**已取消交易**",
            embed=None,
            delete_after=5,
            view=self
        )
        self.stop()


class StockSelect(ntd.ui.StringSelect):
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
                custom_id="buy",
                placeholder="選擇商品",
                options=[
                    ntd.SelectOption(
                        label=fetch_stock_name_symbol(i),
                        value=str(i)
                    ) for i in range(10)
                ],
                row=2
            )
        elif(original_view.trade_type == "賣出"):
            super().__init__(
                custom_id="sell",
                placeholder="選擇庫存",
                options=[
                    ntd.SelectOption(
                        label=fetch_stock_name_symbol(int(i)),
                        value=i
                    ) for i in self.original_view.stock_inv.keys()
                ],
                row=2
            )
    
    async def callback(self, interaction: ntd.Interaction):    
        self.original_view.selected_stock_index = int(self.values[0])
        if(self.original_view.trade_type == "買進"):
            self.original_view.trade_field_value = fetch_stock_name_symbol(
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


class InputQuantity(ntd.ui.Modal):
    """按下「設定張數」按鈕後彈出的文字輸入視窗。
    """
    
    __slots__ = ("original_view", "quantity")

    def __init__(self, original_view: TradeView):
        super().__init__(title="請輸入交易張數")

        self.original_view = original_view

        self.quantity = ntd.ui.TextInput(
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


class ChangeDepositButton(ntd.ui.View):
    """變更小隊存款按鈕。
    """

    __slots__ = ("bot")

    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    def embed_message(self) -> ntd.Embed:
        """嵌入訊息。
        """

        time = datetime.now()
        time = time.strftime("%m/%d %I:%M%p")

        embed = ntd.Embed(
            color=PURPLE,
            title="變更小隊存款",
            type="rich"
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
    
    @ntd.ui.button(
        label="變更小隊存款",
        style=ntd.ButtonStyle.gray,
        emoji="⚙️"
    )
    async def change_deposit_button_callback(
        self,
        button: ntd.ui.Button,
        interaction: ntd.Interaction
    ):
        view = ChangeDepositView(
            interaction.user.display_name,
            interaction.user.display_avatar,
            self.bot
        )
        await interaction.response.send_message(
            view=view,
            embed=view.status_embed(),
            delete_after=180,
            ephemeral=True
        )
        

class ChangeDepositView(ntd.ui.View):
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

    def __init__(
            self,
            user_name: str,
            user_icon: ntd.Asset,
            bot: commands.Bot
    ):
        super().__init__(timeout=180)
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
        self.selected_mode: str | None = None
        # bot
        self.bot = bot

    def status_embed(self) -> ntd.Embed:
        """用於編排嵌入訊息。
        """

        time = datetime.now()
        time = time.strftime("%I:%M%p")

        embed = ntd.Embed(
            colour=PURPLE,
            title=self.embed_title,
            type="rich",
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

    @ntd.ui.select(
        placeholder="選擇小隊",
        min_values=1,
        max_values=1,
        options=[
            ntd.SelectOption(
                label=f"第{_t}小隊",
                value=f"{_t}"
            )
            for _t in range(1, 9)
        ]
    )
    async def team_select_callback(
        self,
        select: ntd.ui.StringSelect, 
        interaction: ntd.Interaction
    ):
        """小隊選取選單callback。
        """

        self.selected_team = int(select.values[0])
        self.embed_title = f"變更第{select.values[0]}小隊存款"
        self.selected_team_deposit = \
            access_file.read_file("team_assets")[select.values[0]]["deposit"]
        self.embed_description = \
            f"第{select.values[0]}小隊目前存款: " \
            f"{self.selected_team_deposit:,}"

        await interaction.response.edit_message(
            embed=self.status_embed()
        )
   
    @ntd.ui.select(
        placeholder="選擇變更模式",
        options=[
            ntd.SelectOption(
                label="增加存款",
                description="輸入增加的金額。",
                emoji="➕"
            ),
            ntd.SelectOption(
                label="減少存款",
                description="輸入減少的金額。",
                emoji="➖"
            ),
            ntd.SelectOption(
                label="更改存款餘額",
                description="輸入改變的餘額。",
                emoji="🔑"
            )
        ]
    )
    async def mode_select_callback(
        self,
        select: ntd.ui.StringSelect, 
        interaction: ntd.Interaction
    ):
        """模式選取選單callback。
        """

        if(select.values[0] == "增加存款"):
            self.selected_mode = "1"
        elif(select.values[0] == "減少存款"):
            self.selected_mode = "2"
        elif(select.values[0] == "更改存款餘額"):
            self.selected_mode = "3"
        
        self.mode_field_value = select.values[0]
        await interaction.response.edit_message(
            view=self,
            embed=self.status_embed()
        )

    @ntd.ui.button(
        label="輸入金額",
        style=ntd.ButtonStyle.blurple,
        emoji="🪙",
        row=2
    )
    async def input_amount_button_callback(
        self,
        button: ntd.ui.Button,
        interaction: ntd.Interaction
    ):
        """輸入金額按鈕callback。
        """

        await interaction.response.send_modal(InputAmount(self))

    @ntd.ui.button(
        label="確認送出",
        style=ntd.ButtonStyle.green,
        emoji="✅",
        row=3
    )
    async def comfirm_button_callback(
        self,
        button: ntd.ui.Button,
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
        self.selected_team_deposit = \
            access_file.read_file("team_assets")[f"{self.selected_team}"]["deposit"]
        if(self.selected_mode == "2" and
            self.selected_team_deposit < self.amount):   # 此小隊金額不足扣繳
            await interaction.response.send_message(
                content=f"**第{self.selected_team}小隊帳戶餘額不足!!!**",
                delete_after=5,
                ephemeral=True
            )
            return
        
        # 變更第n小隊存款
        asset: AssetsManager = self.bot.get_cog("AssetsManager")
        asset.update_deposit(   
            team=self.selected_team,  
            mode=self.selected_mode,
            amount=self.amount,
            user=interaction.user.display_name
        )
        # 改變成工訊息
        self.clear_items()
        await interaction.response.edit_message(
            content="**改變成功!!!**",
            embed=None,
            delete_after=5,
            view=self
        )
        # 更新小隊資產
        ui: DiscordUI = self.bot.get_cog("DiscordUI")
        await ui.update_asset(team=self.selected_team)
        # 發送即時通知
        await ui.send_notification(
            type_="AssetUpdate",
            team=self.selected_team,
            mode=self.selected_mode,
            amount=self.amount,
            user=interaction.user.display_name
        )
        # 更新收支動態
        await ui.update_alteration_log()
        self.stop()
    
    @ntd.ui.button(
        label="取消",
        style=ntd.ButtonStyle.red,
        emoji="✖️",
        row=3
    )
    async def cancel_button_callback(
        self,
        button: ntd.ui.button,
        interaction: ntd.Interaction
    ):
        """取消按鈕callback。
        """

        self.clear_items()
        await interaction.response.edit_message(
            content="**已取消變更**",
            embed=None,
            delete_after=5,
            view=self
        )
        self.stop()


class InputAmount(ntd.ui.Modal):
    """按下「輸入存款」按鈕後彈出的文字輸入視窗。
    """

    __slots__ = ("original_view", "amount")

    def __init__(
            self,
            original_view: ChangeDepositView,
            default_value: str | None = None
    ):
        super().__init__(title="請輸入金額")

        self.original_view = original_view

        self.amount = ntd.ui.TextInput(
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
                embed=self.original_view.status_embed(),
                view=self.original_view
            )
        except ValueError:  # 防呆(輸入文字或負數)
            await interaction.response.send_message(
                content="**金額請輸入正整數!!!**",
                delete_after=5,
                ephemeral=True
            )
        self.stop()


class LogEmbed(ntd.Embed):
    """收支動態 Embed Message。
    """

    def __init__(self):
        super().__init__(
            color=PURPLE,
            title="小隊收支",
            type="rich",
            description="小隊存款金額的變動紀錄以及\n買賣股票紀錄"
        )

        log: AlterationLog = access_file.read_file("alteration_log").copy()
        log.pop("serial")
        # 將所有字典展開唯一list並按照serial排序
        record_list: List[LogData] = sorted(
            [item for sublist in log.values() for item in sublist],
            key=lambda x: x["serial"]
        )
        for record in record_list:
            if(record["type"] == "AssetUpdate"):
                self.add_field(
                    name=f"{record["user"]} 在 {record["time"]}\n" \
                         f"變更第{record["team"]}小隊存款",
                    value=f"{record["original"]:,} {u"\u2192"} {record["updated"]:,}"
                )
            elif(record["type"] == "StockChange"):
                self.add_field(
                    name=f"{record["user"]} 在 {record["time"]}\n" \
                         f"{record["trade_type"]} 第{record["team"]}小隊股票",
                    value=f"商品: {record["stock"]} 張數: {record["quantity"]}"
                )
        
        self.set_footer(
            text=f"資料更新時間: {datetime.now().strftime("%m/%d %I:%M%p")}"
        )


class TeamAssetChangeNoticeEmbed(ntd.Embed):
    """小隊資產變更即時通知 Embed Message。
    """

    def __init__(
            self,
            mode: str,
            amount: int,
            user: str
    ):

        title = {
            "1": "🔔即時入帳通知🔔",
            "2": "💸F-pay消費通知💸",
            "3": "🔑帳戶額變更通知🔑"
        }[mode]
        description = {
            "1": f"關主: {user} 已將 **FP${amount:,}** 匯入帳戶!",
            "2": f"關主: {user} 已將 **FP${amount:,}** 從帳戶中扣除!",
            "3": f"關主: {user} 已改變帳戶餘額為 **$FP{amount:,}** !"
        }[mode]

        super().__init__(
            color=PURPLE,
            title=title,
            type="rich",
            description=description
        )
        self.set_footer(
            text=f"{datetime.now().strftime("%m/%d %I:%M%p")}"
        )


class TeamStockChangeNoticeEmbed(ntd.Embed):
    """小隊股票庫存變更即時通知 Embed Message。
    """

    def __init__(
            self,
            user: str,
            trade_type: Literal["買進", "賣出"],
            stock: int,
            quantity: int,
            display_value: int
    ):
        stock = fetch_stock_name_symbol(stock)
        title = "📊股票成交通知📊"
        description = {
            "買進": f"隊輔: {user} 成功買進**{stock} {quantity}張!**\n" \
                    f"投資成本: **$FP{display_value:,}**",
            "賣出": f"隊輔: {user} 成功賣出**{stock} {quantity}張!**\n" \
                    "總投資損益: " + ("**__利益__**" if display_value >= 0 else "**__損失__**") + f" **$FP{display_value:,}**"
        }[trade_type]

        super().__init__(
            color=PURPLE,
            title=title,
            type="rich",
            description=description
        )
        self.set_footer(
            text=f"{datetime.now().strftime("%m/%d %I:%M%p")}"
        )


class TeamAssetEmbed(ntd.Embed):
    """小隊資產 Embed Message。

    總資產(股票市值+存款)、存款。
    """

    def __init__(self, team: int):
        super().__init__(
            color=PURPLE,
            title=f"第{team}小隊 F-pay帳戶",
            type="rich"
        )
        asset_data: AssetDict = access_file.read_file("team_assets")[f"{team}"]
        self.add_field( # 要加市值
            name="",
            value=f"**總資產: {asset_data["deposit"]:,}** (股票市值+存款)"
        )
        self.add_field(
            name="",
            value=f"**存款: {asset_data["deposit"]:,}**"
        )


class TeamStockEmbed(ntd.Embed):
    """小隊持股狀況 Embed Message。

    持有股票、股票市值、投入成本、未實現投資損益、已實現投資損益、總收益
    """

    def __init__(self, team: int):
        super().__init__(
            color=PURPLE,
            title="股票庫存",
            type="rich"
        )
        stock_inv = fetch_stock_inventory(team)
        if(stock_inv):
            total_unrealized_gain_loss = 0
            for stock_idx, stocks in stock_inv.items():
                pice: int = len(stocks) # 持有張數
                total_cost: int = sum(stocks)   # 投資總成本
                avg_price: float = round(total_cost / (pice*1000), 2)   # 成交均價
                unrealized_gain_loss: int = (round(get_stock_price(stock_idx), 2)
                                             - avg_price) * pice * 1000
                total_unrealized_gain_loss += unrealized_gain_loss  # 未實現總損益
                self.add_field(
                    name=f"{fetch_stock_name_symbol(stock_idx)}",
                    value=f"**持有張數:** {pice}\n" \
                          f"**成交均價:** {avg_price:.2f}\n" \
                          f"**投資總成本:** {total_cost:,}\n" \
                          f"**未實現損益:** {"**__利益__** " if unrealized_gain_loss >= 0 else "**__損失__** "}" \
                          f"{unrealized_gain_loss:.0f}"
                )
            self.description = f"**未實現總損益:** " \
                               f"{"**__利益__** " if total_unrealized_gain_loss >= 0 else "**__損失__** "}" \
                               f"**{total_unrealized_gain_loss:.0f}**"
        else:
            self.description = "無股票庫存"
            

class NewsEmbed(ntd.Embed):
    """新聞 Embed Message。
    """

    def __init__(self, title: str, content: str):
        super().__init__(
            colour=PURPLE,
            title=title,
            type="rich",
            description=content,
            timestamp=datetime.now()
        )


class DiscordUI(commands.Cog):
    """控制Discord端的UI介面
    """

    __slots__ = (
        "bot",
        "CONFIG",
        "CHANNEL_IDS",
        "MESSAGE_IDS",
        "ALTERATION_LOG_MESSAGE",
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
        清除已發送的小隊即時訊息以及清除收支動態，
        並清除log資料。

        `UPDATE_ASSET`
        更新各小隊資產狀況訊息。
        """

        RESET_UI: bool = self.CONFIG["RESET_UI"]
        CLEAR_LOG: bool = self.CONFIG["CLEAR_LOG"]
        UPDATE_ASSET: bool = self.CONFIG["UPDATE_ASSET"]
        if(RESET_UI):
            await self.reset_all_ui()

        if(UPDATE_ASSET):
            await self.update_asset()
        
        if(CLEAR_LOG):
            await self.clear_log()
        else:
            await self.update_alteration_log()

        await self.fetch_alteration_log_message()
        await self.fetch_news_feed_channel()
        await self.fetch_stock_market_message()

        await self.update_market()

        print("Loaded discord_ui")

    @commands.command()
    async def test_ui_com(self, ctx: commands.Context):
        # channel = self.bot.get_channel(1218140719269810237)
        # # delete old message
        # await channel.purge(limit=1)
        # # prompt
        # embed = ntd.Embed(
        #     title="領取身分組",
        #     description="領取「資材營」身分組以開始使用。",
        #     color=0x433274
        # )
        # embed.set_footer(text="(點擊以下表情符號以領取)")
        # embed.set_thumbnail(url="http://203.72.185.5/~1091303/traveler_logo.png")
        # await channel.send(embed=embed)

        # channel = self.bot.get_channel(1238338526551212082)
        # # delete old message
        # await channel.purge(limit=1)
        # # prompt
        # embed = ntd.Embed(
        #     title="領取身分組",
        #     description="依照自己的組別領取",
        #     color=0x433274
        # )
        # embed.set_footer(text="(點擊以下表情符號以領取)")
        # embed.set_thumbnail(url="http://203.72.185.5/~1091303/traveler_logo.png")
        # await channel.send(embed=embed)

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
        view = TradeView(
            user_name=interaction.user.display_name,
            user_avatar=interaction.user.display_avatar,
            user_id=interaction.user.id
        )
        await interaction.response.send_message(
            embed=view.status_embed(),
            view=view,
            ephemeral=True
        )

        pass

    @commands.command()
    async def fetch_team_message_ids(self, ctx: commands.Context, count: int):
        """擷取所有小隊(資產)頻道的最初訊息id。

        count: 擷取幾則訊息
        """

        dict_ = self.CONFIG
        message_ids: MessageIDs = dict_["message_ids"]
        
        for t in range(1, 9):
            channel = self.bot.get_channel(
                self.CHANNEL_IDS[f"team_{t}"]["ASSET"]
            )
            message_ids.update({f"team_{t}": {}})   # 創建t小隊之訊息id字典
            for m in range(1, count+1): # 依照指定訊息數量存入訊息id字典
                if(message_ids[f"team_{t}"].get(f"msg_{m}", None) is None):
                    msg = await channel.send(f"initial message {m}")
                    message_ids[f"team_{t}"].update(
                        {f"msg_{m}": msg.id}
                    )
                
        self.save_to("game_config", dict_)

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
        view = ChangeDepositButton(self.bot)
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
        view = TradeButton(self.bot)
        await message.edit(
            view=view
        )

    async def clear_log(self):
        """|coro|
        
        清除已發送的小隊即時訊息以及清除收支動態，並清除log資料。
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
        """抓取ALTERATION_LOG_MESSAGE。
        """

        channel = self.bot.get_channel(
            self.CHANNEL_IDS["STOCK_MARKET"]
        )
        self.STOCK_MARKET_MESSAGE = await channel.fetch_message(
            self.MESSAGE_IDS["STOCK_MARKET"]
        )

    async def update_alteration_log(self):
        """|coro|

        更新收支動態。
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
            type_: Literal["AssetUpdate", "StockChange"] | None = None,
            team: int | None = None,
            mode: str | None = None,
            amount: int | None = None,
            user: str | None = None,
            trade_type: Literal["買進", "賣出"] | None = None,
            stock: int | None = None,
            quantity: int | None = None,
            display_value: int | None = None
    ):
        """|coro|

        發送即時通知。
        """

        channel = self.bot.get_channel(
            self.CHANNEL_IDS[f"TEAM_{team}"]["NOTICE"]
        )
        if(type_ == "AssetUpdate"):
            await channel.send(
                embed=TeamAssetChangeNoticeEmbed(
                    mode=mode,
                    amount=amount,
                    user=user
                )
            )
        elif(type_ == "StockChange"):
            await channel.send(
                embed=TeamStockChangeNoticeEmbed(
                    user=user,
                    trade_type=trade_type,
                    stock=stock,
                    quantity=quantity,
                    display_value=display_value
                )
            )
        
    async def update_market(self):
        """更新市場動態。
        """

        if(self.STOCK_MARKET_MESSAGE is None):
            await self.fetch_stock_market_message()

        await self.STOCK_MARKET_MESSAGE.edit(
            embed=StockMarketEmbed()
        )

    async def update_asset(self, team: int | None = None):
        """|coro|

        任一操作改變資產時更新小隊資產狀況訊息。
        """
        
        if(isinstance(team, int)):  # 更新指定小隊資產訊息
            channel = self.bot.get_channel(
                self.CHANNEL_IDS[f"TEAM_{team}"]["ASSET"]
            )
            message = await channel.fetch_message(
                self.MESSAGE_IDS["ASSET_MESSAGE_IDS"][f"TEAM_{team}"]
            )
            await message.edit(
                embeds=[
                    TeamAssetEmbed(team),
                    TeamStockEmbed(team)
                ]
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
                    content=None,
                    embeds=[
                        TeamAssetEmbed(team),
                        TeamStockEmbed(team)
                    ]
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
    