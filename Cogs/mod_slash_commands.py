"""所有機器人管理方面的Slash commands
"""
from nextcord.ext import commands, application_checks
from nextcord.interactions import Interaction
import nextcord as ntd


class SlashCommands(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Loaded mod_slash_commands")
        print()

    @ntd.slash_command(name="ping", description="Replies Pong!")
    @application_checks.has_any_role(
        1218179373522358313,    # 最強大腦活動組
        1218184965435691019     # 大神等級幹部組
    )
    async def ping(self, interaction: Interaction):
        """Replies Pong!
        """
        await interaction.response.send_message("Pong!")
        # await original_message.edit("ahahah")

    @ntd.slash_command(name="test", description="For general testing.")
    @application_checks.is_owner()
    async def test(
        self,
        interaction: Interaction,
        ):
        """Slash command for general testing.
        """
        await interaction.response.send_message("great!")


    @ping.error
    @test.error
    async def application_command_error_handler(
        self,
        interaction: Interaction,
        error: Exception
    ):
        """Application command error handler.
        """
        if(isinstance(error, ntd.ApplicationCheckFailure)):
            await interaction.response.send_message(
                "**你沒有權限使用這個指令!!!**",
                delete_after=3,
                ephemeral=True
            )


def setup(bot: commands.Bot):
    bot.add_cog(SlashCommands(bot))