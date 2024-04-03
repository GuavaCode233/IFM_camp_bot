from nextcord.ext import commands
import nextcord as ntd

from datetime import datetime

from .utilities import AccessFile
from .assets_manager import AssetsManager


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
        """用於編排嵌入訊息
        """

        embed = ntd.Embed(
            colour=0x433274,
            title=self.embed_title,
            type="rich",
            description=self.embed_description,
            timestamp=datetime.now()
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
            text=self.author_name,
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
                amount=self.amount
            )
            self.clear_items()
            await interaction.response.edit_message(
                content="**改變成功!!!**",
                embed=None,
                delete_after=5,
                view=self
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


class DiscordUI(commands.Cog, AccessFile):
    """控制Discord端的UI介面
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # #連結Cog方法
    # @commands.command()
    # async def inter_com(self, ctx: commands.Context):
    #     assets: AssetsManager = self.bot.get_cog("AssetsManager") # return type: <class 'Cogs.main_bot.AssetsManager'>
    #     print(assets.team_assets[0].deposit)  # 可提示子class方便撰寫
        
    @commands.command()
    async def test_ui(self, ctx: commands.Context):
        pass

    @ntd.slash_command(
            name="test_ui",
            description="For testing UIs",
            guild_ids=[1218130958536937492]
    )
    async def test_ui(self, interaction: ntd.Interaction):
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

    async def resend_assets_ui(self):
        """|coro|

        刪除舊的資產訊息並重新發送。
        """
        pass
    
    async def update_assets(self):
        """|coro|

        任一操作改變資產時更新所有小隊資產訊息。
        """
        pass


def setup(bot: commands.Bot):
    bot.add_cog(DiscordUI(bot))