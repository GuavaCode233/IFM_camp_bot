from nextcord.ext import commands
import nextcord as ntd

from datetime import datetime
from typing import Dict, List, Any

from Cogs.utilities import AccessFile
from Cogs.assets_manager import AssetsManager


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
            color=0x433274,
            title="變更小隊存款",
            type="rich"
        )
        embed.add_field(
            name="功能介紹",
            value="➕__增加存款__\n" \
                  "增加指定小隊的存款額\n" \
                  "➖__減少存款__\n" \
                  "減少指定小隊的存款額\n" \
                  "🔑__更改存款額__\n" \
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
        "author_name",
        "author_icon",
        "selected_team",
        "selected_mode",
        "bot"
    )

    def __init__(
            self,
            author_name: str,
            author_icon: ntd.Asset,
            bot: commands.Bot
    ):
        super().__init__(timeout=180)
        # embed message
        self.embed_title: str = "變更小隊存款"  # 變更第n小隊存款
        self.embed_description: str | None = "請選擇小隊" # None
        self.mode_field_value: str = "請選擇變更模式"
        self.amount: str | int = "請輸入金額"   # 金額: int
        self.author_name = author_name
        self.author_icon = author_icon
        # slect status
        self.selected_team: int | None = None
        self.selected_mode: str | None = None
        # bot
        self.bot = bot

    def status_embed(self) -> ntd.Embed:
        """用於編排嵌入訊息。
        """

        time = datetime.now()
        time = time.strftime("%I:%M%p")

        embed = ntd.Embed(
            colour=0x433274,
            title=self.embed_title,
            type="rich",
            description=self.embed_description
        )
        embed.add_field(
            name="變更模式",
            value=self.mode_field_value
        )
        embed.add_field(
            name="變更金額",
            value=self.amount
        )
        embed.set_footer(
            text=f"{self.author_name} | Today at {time}",
            icon_url=self.author_icon
        )

        return embed

    def input_check(self) -> bool:
        """檢查資料都有填齊。
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
        self.embed_description = None

        await interaction.response.edit_message(
            embed=self.status_embed()
        )
   
    @ntd.ui.select(
        placeholder="選擇變更模式",
        min_values=1,
        max_values=1,
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
        button: ntd.ui.button,
        interaction: ntd.Interaction
    ):
        """確認送出按扭callback。
        """

        if(self.input_check()):
            asset: AssetsManager = self.bot.get_cog("AssetsManager")
            asset.update_deposit(
                team=self.selected_team,  # 變更第n小隊存款
                mode=self.selected_mode,
                amount=self.amount,
                user=interaction.user.display_name
            )
            self.clear_items()
            await interaction.response.edit_message(
                content="**改變成功!!!**",
                embed=None,
                delete_after=5,
                view=self
            )
            ui: DiscordUI = self.bot.get_cog("DiscordUI")
            await ui.update_log(
                type_="AssetUpdate",
                team=self.selected_team,
                mode=self.selected_mode,
                amount=self.amount,
                user=interaction.user.display_name
            )
            self.stop()
        else:
            await interaction.response.send_message(
                content="**輸入資料不完整!!!**",
                delete_after=5,
                ephemeral=True
            )
    
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
    """按下「輸入存款」按鈕後彈出的視窗。
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
                view=self.original_view,
                embed=self.original_view.status_embed()
            )
        except ValueError:  # 防呆(輸入文字或負數)
            await interaction.response.send_message(
                content="**金額請輸入正整數!!!**",
                delete_after=5,
                ephemeral=True
            )
        self.stop()


class FormattedLogEmbed(ntd.Embed, AccessFile):
    """收支動態 Embed Message。
    """

    def __init__(self):
        super().__init__(
            color=0x433274,
            title="小隊收支",
            type="rich",
            description="小隊存款金額的變動紀錄以及\n買賣股票紀錄"
        )

        log: Dict[str, List[Dict[str, Any]]] = self.acc_log().copy()
        log.pop("serial")
        # 將所有字典展開唯一list並按照serial排序
        record_list: List[Dict[str, Any]] = sorted(
            [item for sublist in log.values() for item in sublist],
            key=lambda x: x["serial"]
        )
        for record in record_list:
            if(record["type"] == "AssetUpdate"):
                self.add_field(
                    name=f"{record["user"]} 在 {record["time"]}\n" \
                         f"變更第{record["team"]}小隊存款",
                    value=f"{record["original"]} {u"\u2192"} {record["updated"]}"
                )
            else:
                pass
        
        self.set_footer(
            text=f"資料更新時間: {datetime.now().strftime("%m/%d %I:%M%p")}"
        )


class FormattedTeamLogEmbed(ntd.Embed, AccessFile):
    """收支動態 Embed Message。
    """

    def __init__(
            self,
            type_: str,
            mode: str,
            amount: int,
            user: str
    ):
        if(type_ == "AssetUpdate"):
            title = {
                "1": "🔔即時入帳通知🔔",
                "2": "💸F-pay消費通知💸",
                "3": "🔑帳戶額變更通知🔑"
            }[mode]
            description = {
                "1": f"關主: {user} 已將 **FP${amount}** 匯入帳戶!",
                "2": f"關主: {user} 已將 **FP${amount}** 從帳戶中扣除!",
                "3": f"關主: {user} 已改變帳戶餘額為 **$FP{amount}** !"
            }[mode]
        else:
            pass
        
        super().__init__(
            color=0x433274,
            title=title,
            type="rich",
            description=description
        )
        self.set_footer(
            text=f"{datetime.now().strftime("%m/%d %I:%M%p")}"
        )


class DiscordUI(commands.Cog, AccessFile):
    """控制Discord端的UI介面
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.CONFIG = self.acc_game_config()
        self.CHANNEL_IDS: Dict[str, int] = self.CONFIG["channel_ids"]
        self.MESSAGE_IDS: Dict[str, int] = self.CONFIG["message_ids"]

    # #連結Cog方法
    # @commands.command()
    # async def inter_com(self, ctx: commands.Context):
    #     assets: AssetsManager = self.bot.get_cog("AssetsManager") # return type: <class 'Cogs.main_bot.AssetsManager'>
    #     print(assets.team_assets[0].deposit)  # 可提示子class方便撰寫
    # @commands.Cog.listener()
    # async def on_message(self, message: ntd.Message):
    #     await self.bot.process_commands(message)
    @commands.Cog.listener()
    async def on_ready(self):
        print("discord_ui Ready!")

        RESET_UI: bool = self.CONFIG["RESET_UI"]
        CLEAR_LOG: bool = self.CONFIG["CLEAR_LOG"]
        if(RESET_UI):
            await self.reset_all_ui()
            print("All ui elements has been reset.")
        
        if(CLEAR_LOG):
            await self.clear_log()
        else:
            await self.update_log()

    @commands.command()
    async def test_ui_com(self, ctx: commands.Context):
        channel = self.bot.get_channel(
            self.CHANNEL_IDS["ALTERATION_LOG"]
        )
        msg = await channel.send("initial log message")
        print(msg.id)

    @ntd.slash_command(
            name="test_ui",
            description="For testing UIs",
            guild_ids=[1218130958536937492]
    )
    async def test_ui(self, interaction: ntd.Interaction):
        # await interaction.response.send_message(
        #     embed=FormattedLogEmbed()
        # )
        pass

    @commands.command()
    async def fetch_team_message_ids(self, ctx: commands.Context, count: int):
        """擷取所有小隊(資產)頻道的最初訊息id。

        count: 擷取幾則訊息
        """

        dict_ = self.CONFIG
        message_ids: Dict[str: Dict[str: int]] = dict_["message_ids"]
        
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
    
    async def clear_log(self):
        """|coro|
        
        清除已發送的小隊即時訊息以及清除收支動態，並清除log資料。
        """

        log = self.acc_log()

        # 清除各小隊即時訊息
        for t in range(1, 9):
            channel = self.bot.get_channel(
                self.CHANNEL_IDS[f"team_{t}"]["NOTICE"]
            )

            if(log.get(str(t), None) is None):  # 有記錄才需要刪
                continue
            
            msg_count = len(log[f"{t}"])
            await channel.purge(limit=msg_count)
        
        # 清除log資料
        self.clear_log_data()
        # 更新log
        await self.update_log()
            
    async def update_log(
            self,
            type_: str | None = None,
            team: int | None = None,
            mode: str | None = None,
            amount: int | None = None,
            user: str | None = None
    ):
        """|coro|

        更新收支動態，或更新收支並發送即時動態訊息。
        """

        channel = self.bot.get_channel(
            self.CHANNEL_IDS["ALTERATION_LOG"]
        )
        message = await channel.fetch_message(
            self.MESSAGE_IDS["ALTERATION_LOG"]
        )
        await message.edit(
            content=None,
            embed=FormattedLogEmbed()
        )
        if(isinstance(type_, str)):
            channel = self.bot.get_channel(
                self.CHANNEL_IDS[f"team_{team}"]["NOTICE"]
            )
            await channel.send(
                embed=FormattedTeamLogEmbed(
                    type_=type_,
                    mode=mode,
                    amount=amount,
                    user=user
                )
            )

    async def update_assets(self):
        """|coro|

        任一操作改變資產時更新所有小隊資產訊息。
        """
        pass


def setup(bot: commands.Bot):
    bot.add_cog(DiscordUI(bot))