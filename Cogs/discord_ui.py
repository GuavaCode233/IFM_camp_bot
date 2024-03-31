from nextcord.ext import commands
import nextcord as ntd

from .utilities import AccessFile
from .assets_manager import AssetsManager


# class TeamDepositView(View):
#     """小隊收支按鈕
#     """

#     @ntd.ui.button(label="加錢", style=ntd.ButtonStyle.green, emoji="➕")
#     async def deposit_button_callback(self, button: Button, interaction: Interaction):
#         await interaction.response.send_message("加錢啦", ephemeral=True, delete_after=3)

#     @ntd.ui.button(label="扣錢", style=ntd.ButtonStyle.red, emoji="➖")
#     async def withdraw_button_callback(self, button: Button, interaction: Interaction):
#         await interaction.response.send_message("扣錢啦", ephemeral=True, delete_after=3)

#     @ntd.ui.button(label="更改餘額", style=ntd.ButtonStyle.gray, emoji="🔑")
#     async def change_button_callback(self, button: Button, interaction: Interaction):
#         await interaction.response.send_message("改餘額", ephemeral=True, delete_after=3)


class TestForm(ntd.ui.Modal):

    def __init__(self):
        super().__init__(title="Title")


class ChangeDepositView(ntd.ui.View):
    """
    """
    def __init__(self):
        super().__init__()
        self.selected_team = None

    @ntd.ui.select(
        placeholder="Placehoder",
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
        await interaction.response.send_message(
            f"You choosed team: {select.values[0]}"
        )
        self.selected_team = select.values[0]

    
    @ntd.ui.select(
    placeholder="Placehoder",
    min_values=1,
    max_values=1,
    options=[
        ntd.SelectOption(
            label="增加存款",
            value="increase",
            description="輸入增加的金額。",
            emoji="➕"
        ),
        ntd.SelectOption(
            label="減少存款",
            value="decrease",
            description="輸入減少的金額。",
            emoji="➖"
        ),
        ntd.SelectOption(
            label="更改存款餘額",
            value="change",
            description="輸入改變的餘額。",
            emoji="🔑"
        )
        ]
        )
    async def type_select_callback(
        self,
        select: ntd.ui.StringSelect, 
        interaction: ntd.Interaction
    ):
        await interaction.response.send_message(
            f"You choosed to {select.values[0]}" \
            f"the deposit of team: {self.selected_team}."
        )



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
        await interaction.response.send_message(
            view=ChangeDepositView()
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