from __future__ import annotations

import logging

import discord
from discord import ui
from discord.ext import commands

import config
from emojis import emoji
from utils.components import build_base_container, add_separator, add_text

log = logging.getLogger("support_voice")


class SupportVoice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _build_view(self, member: discord.Member, ping_role: discord.Role | None) -> ui.LayoutView:
        ping_value = ping_role.mention if ping_role else "—"

        container = build_base_container(title=f"{emoji('notifier', 'bell')} Notifier")
        if ping_role:
            add_text(container, ping_role.mention)
        add_separator(container)
        add_text(container, "**User Details:**")
        add_text(
            container,
            f"{emoji('notifier', 'hash')} **Username:** `{member.name}`\n"
            f"{emoji('notifier', 'hash')} **Mention:** {member.mention}\n"
            f"{emoji('notifier', 'person')} **ID:** `{member.id}`\n"
            f"{emoji('notifier', 'bell')} **Ping:** {ping_value}\n"
            f"{emoji('notifier', 'clock')} **Time:** {discord.utils.format_dt(discord.utils.utcnow(), style='F')}",
        )

        view = ui.LayoutView(timeout=None)
        view.add_item(container)
        return view

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        after_id = after.channel.id if after.channel else None
        log.info(f"[support_voice] voice_state_update: {member} -> after.channel={after_id}")

        if before.channel and before.channel.id == config.SUPPORT_VOICE_CHANNEL_ID:
            return
        if not after.channel or after.channel.id != config.SUPPORT_VOICE_CHANNEL_ID:
            return

        log.info(f"[support_voice] {member} μπήκε στο SUPPORT_VOICE_CHANNEL_ID={config.SUPPORT_VOICE_CHANNEL_ID}")

        guild = member.guild
        notify_channel = guild.get_channel(config.SUPPORT_VOICE_NOTIFIER_CHANNEL_ID)
        if not notify_channel:
            log.warning(
                f"[support_voice] Δεν βρέθηκε notify_channel με ID={config.SUPPORT_VOICE_NOTIFIER_CHANNEL_ID} "
                f"(guild.get_channel γύρισε None — ή λάθος ID ή το bot δεν το βλέπει)."
            )
            return

        ping_role = guild.get_role(config.SUPPORT_VOICE_PING_ROLE_ID)
        if not ping_role:
            log.warning(f"[support_voice] Δεν βρέθηκε ρόλος με ID={config.SUPPORT_VOICE_PING_ROLE_ID}.")

        view = self._build_view(member, ping_role)

        try:
            await notify_channel.send(
                view=view,
                allowed_mentions=discord.AllowedMentions(roles=True),
            )
            log.info(f"[support_voice] Στάλθηκε notify στο #{notify_channel} για {member}.")
        except discord.Forbidden:
            log.error(
                f"[support_voice] Forbidden: το bot δεν έχει δικαίωμα να στείλει μήνυμα στο "
                f"#{notify_channel} (channel ID {config.SUPPORT_VOICE_NOTIFIER_CHANNEL_ID})."
            )
        except discord.HTTPException as e:
            log.error(f"[support_voice] HTTPException κατά την αποστολή notify: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(SupportVoice(bot))
