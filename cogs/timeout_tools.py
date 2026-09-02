from __future__ import annotations

import datetime

import discord
from discord import app_commands
from discord.ext import commands

import config
from utils.permissions import slash_is_manager_team


def _log_embed(guild: discord.Guild, *, title: str, moderator: discord.abc.User, target: str, reason: str | None) -> discord.Embed:
    embed = discord.Embed(title=title, color=config.EMBED_COLOR, timestamp=datetime.datetime.now(datetime.timezone.utc))
    embed.add_field(name="Moderator", value=f"{moderator.mention} (`{moderator.id}`)", inline=False)
    embed.add_field(name="Target", value=target, inline=False)
    embed.add_field(name="Reason", value=reason or "—", inline=False)
    embed.add_field(name="Ώρα", value=discord.utils.format_dt(datetime.datetime.now(datetime.timezone.utc), style="F"), inline=False)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    return embed


async def _send_log(guild: discord.Guild, channel_id: int, embed: discord.Embed):
    channel = guild.get_channel(channel_id)
    if channel:
        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass


async def build_scan_timeouts_embed(guild: discord.Guild) -> discord.Embed:
    if not guild.chunked:
        try:
            await guild.chunk(cache=True)
        except discord.HTTPException:
            pass

    now = datetime.datetime.now(datetime.timezone.utc)

    timed_out: list[discord.Member] = [
        m for m in guild.members if m.timed_out_until and m.timed_out_until > now
    ]

    embed = discord.Embed(title="Scan Timeouts", color=config.EMBED_COLOR, timestamp=now)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    if not timed_out:
        embed.description = "Κανένα άτομο δεν έχει timeout τώρα."
        return embed

    timed_out.sort(key=lambda m: m.timed_out_until)
    lines = [
        f"{member.mention} (`{member.id}`) — λήγει {discord.utils.format_dt(member.timed_out_until, style='R')}"
        for member in timed_out
    ]

    chunk, chunks, length = [], [], 0
    for line in lines:
        if length + len(line) + 1 > 3900:
            chunks.append("\n".join(chunk))
            chunk, length = [], 0
        chunk.append(line)
        length += len(line) + 1
    if chunk:
        chunks.append("\n".join(chunk))

    embed.description = f"**Βρέθηκαν {len(timed_out)} μέλος/η με ενεργό timeout:**\n\n{chunks[0]}"
    for extra in chunks[1:]:
        embed.add_field(name="\u200b", value=extra, inline=False)

    return embed


class TimeoutTools(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="scan-timeouts", description="Σκανάρει το server και δείχνει ποια άτομα timeout")
    @slash_is_manager_team()
    async def scan_timeouts_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        embed = await build_scan_timeouts_embed(interaction.guild)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="untimeout", description="Αφαιρεί το timeout από έναν χρήστη")
    @app_commands.describe(user="Ο χρήστης από τον οποίο θα αφαιρεθεί το timeout", reason="Λόγος (προαιρετικό)")
    @slash_is_manager_team()
    async def untimeout_cmd(self, interaction: discord.Interaction, user: discord.Member, reason: str = None):
        if not user.timed_out_until or user.timed_out_until <= datetime.datetime.now(datetime.timezone.utc):
            await interaction.response.send_message(f"Ο {user.mention} δεν έχει ενεργό timeout.", ephemeral=True)
            return

        if not interaction.guild.me.guild_permissions.moderate_members:
            await interaction.response.send_message(
                "Το bot δεν έχει το δικαίωμα **Moderate Members** στο server — πήγαινε στα "
                "Server Settings > Roles και δώσε το στον ρόλο του bot.",
                ephemeral=True,
            )
            return

        try:
            await user.timeout(None, reason=reason)
        except discord.Forbidden:
            await interaction.response.send_message(
                f"Δεν μπόρεσα να αφαιρέσω το timeout από {user.mention} — ο ρόλος του bot "
                "πρέπει να είναι πιο ψηλά από τον δικό του στην ιεραρχία ρόλων.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as e:
            await interaction.response.send_message(f"Σφάλμα `{e}`", ephemeral=True)
            return

        await interaction.response.send_message(f"Αφαιρέθηκε το timeout από {user.mention}.", ephemeral=True)

        await _send_log(interaction.guild, config.LOG_UNTIMEOUT_CHANNEL_ID,
                         _log_embed(interaction.guild, title="Untimeout", moderator=interaction.user,
                                    target=f"{user.mention} (`{user.id}`)", reason=reason))

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CheckFailure):
            msg = "Δεν έχεις δικαίωμα να χρησιμοποιήσεις αυτή την εντολή."
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        else:
            raise error


async def setup(bot: commands.Bot):
    await bot.add_cog(TimeoutTools(bot))
