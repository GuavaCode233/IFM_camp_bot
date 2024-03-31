"""所有機器人管理方面的指令
"""
from nextcord.ext import commands
from nextcord.ext.commands import Bot, Context
import nextcord as ntd

import os


class ModCommands(commands.Cog):

    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self): 
        print("mod_commands Ready!")

    @commands.command()
    @commands.has_any_role(
        1218179373522358313,    # 最強大腦活動組
        1218184965435691019     # 大神等級幹部組
    )
    async def ping(self, ctx: Context):
        """Replies Pong!
        """
        await ctx.send("Pong!")

    @commands.command()
    @commands.is_owner()
    async def test(self, ctx: Context):
        """command for general testing.
        """
        pass

    @commands.command()
    @commands.is_owner()
    async def permanent_invite_link(self, ctx: Context):
        """永久邀請連結訊息
        """
        channel = self.bot.get_channel(1218194582840541245)
        # delete old message
        await channel.purge(limit=2)
        # prompt
        embed = ntd.Embed(
            title="永久邀請連結",
            description="邀請學員、工人及幹部\n請用此連結邀請。",
            color=0x433274
        )
        embed.set_footer(text="(長按以下連結以複製)")
        embed.set_thumbnail(url="http://203.72.185.5/~1091303/traveler_logo.png")
        await channel.send(embed=embed)
        # link itself
        await channel.send("https://discord.gg/hacjPr8fat")

def setup(bot: Bot):
    bot.add_cog(ModCommands(bot))