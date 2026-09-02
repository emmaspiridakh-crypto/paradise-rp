import discord
from discord.ext import commands

import config
from utils.permissions import is_staff_team


class PanelCommand(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="panel")
    @is_staff_team()
    async def panel_cmd(self, ctx: commands.Context):
        embed = discord.Embed(title="Commands Panel", color=config.EMBED_COLOR)
        if ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)

        embed.add_field(
            name="Moderation (Manager/Ownership)",
            value=(
                "`!ban @user [reason]`\n`!unban <id> [reason]`\n`!kick @user [reason]`\n"
                "`!timeout @user <10m/1h/1d> [reason]`\n`!clearmessages <amount>`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Timeout Tools (Manager/Ownership)",
            value=(
                "`/untimeout <user> [reason]`\n"
                "`/scan-timeouts`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Say (Ownership only)",
            value="`!say <text>`\n`!say2 <text>`",
            inline=False,
        )
        embed.add_field(name="DM All (Founder only)", value="`!dmall <text>`", inline=False)
        embed.add_field(name="DM User (Founder only)", value="`!dmuser <@user> <text>`", inline=False)
        embed.add_field(
            name="Slash Panels (Manager/Ownership)",
            value=(
                "`/panel-support`\n`/panel-civilian-job`\n`/panel-criminal-job`\n"
                "`/panel-donate`\n`/panel-applications`\n`/panel-staff-activity`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Applications Lock (Ownership only)",
            value=(
                "`/lockapplication <name>`\n`/unlockapplication <name>`\n"
                "`/lockallapplications`\n`/unlockallapplications`"
            ),
            inline=False,
        )
        embed.add_field(
            name="Warnings (Ownership only)",
            value="`/warn`\n`/remove-warning <user>`",
            inline=False,
        )
        embed.add_field(
            name="Giveaway (Ownership only)",
            value=(
                "`/giveaway create`\n`/giveaway delete`\n"
                "`/giveaway list`"
            ),
            inline=False,
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(PanelCommand(bot))
