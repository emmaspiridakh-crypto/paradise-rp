from __future__ import annotations

import datetime as _dt
import re

import discord
from discord import ui
from discord.ext import commands

import config
from emojis import emoji
from utils import storage
from utils.components import build_base_container, add_separator, add_text

STORE_NAME = "compliments"

LINK_RE = re.compile(r"(https?://|www\.|discord\.gg/|discord\.com/invite/)", re.IGNORECASE)

GREEK_DAYS = ["Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή", "Σάββατο", "Κυριακή"]
GREEK_MONTHS = [
    "", "Ιανουαρίου", "Φεβρουαρίου", "Μαρτίου", "Απριλίου", "Μαΐου", "Ιουνίου",
    "Ιουλίου", "Αυγούστου", "Σεπτεμβρίου", "Οκτωβρίου", "Νοεμβρίου", "Δεκεμβρίου",
]


def _greek_date(dt: _dt.datetime) -> str:
    day_name = GREEK_DAYS[dt.weekday()]
    hour12 = dt.hour % 12 or 12
    period = "πμ" if dt.hour < 12 else "μμ"
    return f"{day_name}, {dt.day} {GREEK_MONTHS[dt.month]} {dt.year} {hour12:02d}:{dt.minute:02d} {period}"


class StaffCompliments(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _build_view(self, *, author: discord.Member, text: str, created_at: _dt.datetime) -> ui.LayoutView:
        thumb = author.display_avatar.url if author else None
        container = build_base_container(
            title=f"{emoji('compliments', 'compliment')} • Νέο Staff Compliment",
            thumbnail_url=thumb,
        )
        add_separator(container)
        bullet = emoji("compliments", "bullet") or "»"
        add_text(container, (
            f"{emoji('compliments', 'submitted')} Υποβλήθηκε από {author.mention if author else 'Άγνωστος'}\n"
            f"{bullet} {_greek_date(created_at)}"
        ))
        add_separator(container)
        add_text(container, text)

        view = ui.LayoutView(timeout=None)
        view.add_item(container)
        return view

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.channel.id != config.STAFF_COMPLIMENTS_CHANNEL_ID:
            return

        content = message.content.strip()
        author = message.author

        if LINK_RE.search(content):
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            try:
                warning = await message.channel.send(
                    f"{emoji('compliments', 'compliment') or '⚠️'} {author.mention} δεν επιτρέπονται **links** μέσα στα compliments."
                )
                await warning.delete(delay=6)
            except discord.HTTPException:
                pass
            return

        created_at = discord.utils.utcnow()

        try:
            await message.delete()
        except discord.Forbidden:
            pass

        view = self._build_view(author=author, text=content, created_at=created_at)
        log_channel = message.guild.get_channel(config.STAFF_COMPLIMENTS_LOG_CHANNEL_ID) or message.channel
        sent = await log_channel.send(view=view)

        store = storage.get_store(STORE_NAME)
        store[str(sent.id)] = {
            "author_id": author.id, "text": content, "created_at": created_at.isoformat(),
        }
        storage.save(STORE_NAME, store)


async def setup(bot: commands.Bot):
    await bot.add_cog(StaffCompliments(bot))
