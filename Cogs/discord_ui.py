from nextcord.ext import commands

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


class DiscordUI(commands.Cog, AccessFile):
    """控制Discord端的UI介面
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    #連結Cog方法
    @commands.command()
    async def inter_com(self, ctx: commands.Context):
        assets: AssetsManager = self.bot.get_cog("AssetsManager") # return type: <class 'Cogs.main_bot.AssetsManager'>
        print(assets.team_assets[0].deposit)  # 可提示子class方便撰寫

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