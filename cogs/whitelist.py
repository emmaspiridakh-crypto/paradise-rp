from __future__ import annotations

import discord
from discord import ui, app_commands
from discord.ext import commands

import config
from emojis import emoji
from utils import storage
from utils.permissions import member_has_any_role
from utils.components import build_base_container, add_separator, add_text, add_action_row, add_section_with_button

STORE_NAME = "whitelist"
LOCK_STORE = "whitelist_lock"


def _safe_name(text: str) -> str:
    text = text.lower().strip().replace(" ", "-")
    return "".join(c for c in text if c.isalnum() or c == "-")[:90]


def _is_locked() -> bool:
    lock = storage.get_store(LOCK_STORE)
    return bool(lock.get("locked", False))


def _is_ownership(member: discord.Member) -> bool:
    return member_has_any_role(member, [config.OWNERSHIP_ROLE_ID])


class WhitelistDenyReasonModal(ui.Modal, title="Αιτιολογία Απόρριψης"):
    reason = ui.TextInput(label="Λόγος απόρριψης", style=discord.TextStyle.paragraph, required=True, max_length=500)

    def __init__(self, channel_id: int, cog: "Whitelist"):
        super().__init__()
        self.channel_id = channel_id
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.finalize_whitelist(interaction, self.channel_id, accepted=False, reason=str(self.reason))


class Whitelist(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="panel-whitelist", description="Στέλνει το Whitelist panel")
    @app_commands.checks.has_any_role(config.OWNERSHIP_ROLE_ID)
    async def panel_whitelist(self, interaction: discord.Interaction):
        locked = _is_locked()
        status_text = "κλειστές" if locked else "ανοιχτές"
        status_dot = emoji("whitelist", "status_closed") if locked else emoji("whitelist", "status_open")

        container = build_base_container(
            title="Paradise Roleplay | Whitelist Application",
            description=(
                "Υπόβαλε αίτηση whitelist για να μπεις στον server.\n"
                "**Έχεις 15 λεπτά να ολοκληρώσεις την αίτηση σου αλλιώς θα ακυρωθεί.**"
            ),
            banner_url=getattr(config, "WHITELIST_BANNER_URL", None),
        )
        add_separator(container)

        raw_apply_emoji = emoji("whitelist", "apply")
        text = f"{raw_apply_emoji} **Whitelist Application**\nΥπόβαλε την αίτησή σου για να μπεις στον server.\n\n{status_dot} Αιτήσεις **{status_text}**"
        apply_btn = ui.Button(
            label="Apply Now", style=discord.ButtonStyle.secondary,
            emoji=raw_apply_emoji if raw_apply_emoji else None,
            disabled=locked, custom_id="wl_apply",
        )
        add_section_with_button(container, text=text, button=apply_btn)

        link_url = getattr(config, "WHITELIST_LINK_URL", None)
        if link_url:
            add_separator(container)
            link_text = getattr(config, "WHITELIST_LINK_TEXT", "Για να μπορείς να μπείς στο roblox game μας θα πρέπει να είσαι μέλος στο roblox group. Πάτα το **Join Now** για να μπείς.")
            link_label = getattr(config, "WHITELIST_LINK_LABEL", "Join Now")
            link_btn = ui.Button(label=link_label, style=discord.ButtonStyle.link, url=link_url)
            add_section_with_button(container, text=link_text, button=link_btn)

        view = ui.LayoutView(timeout=None)
        view.add_item(container)
        await interaction.channel.send(view=view)
        await interaction.response.send_message("Στάλθηκε.", ephemeral=True)

    async def start_apply(self, interaction: discord.Interaction):
        if _is_locked():
            await interaction.response.send_message(
                "Οι αιτήσεις whitelist είναι κλειδωμένες αυτή τη στιγμή. Δοκίμασε ξανά αργότερα.", ephemeral=True
            )
            return

        guild = interaction.guild
        user = interaction.user

        store = storage.get_store(STORE_NAME)
        for ch_id, info in store.items():
            if info.get("user_id") == user.id and info.get("status") not in ("closed", "denied", "accepted"):
                channel = guild.get_channel(int(ch_id))
                if channel:
                    await interaction.response.send_message(f"Έχεις ήδη ανοιχτή αίτηση: {channel.mention}", ephemeral=True)
                    return

        category = guild.get_channel(getattr(config, "WHITELIST_CATEGORY_ID", None))
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        ownership_role = guild.get_role(config.OWNERSHIP_ROLE_ID)
        if ownership_role:
            overwrites[ownership_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"whitelist-{_safe_name(user.display_name)}", category=category, overwrites=overwrites
        )

        store[str(channel.id)] = {
            "user_id": user.id, "status": "pending",
            "current_step": 0, "answers": [],
        }
        storage.save(STORE_NAME, store)

        container = build_base_container(
            title="Whitelist Application",
            description=f"{user.mention}\nΠάτησε **Start Your Application** όταν είσαι έτοιμος/η. Χρόνος ολοκλήρωσης: 15 λεπτά",
        )
        add_separator(container)
        start_btn = ui.Button(label="Start Your Application", style=discord.ButtonStyle.success,
                               emoji=emoji("whitelist", "start") or None, custom_id=f"wl_start:{channel.id}")
        close_btn = ui.Button(label="Close", style=discord.ButtonStyle.danger,
                               emoji=emoji("whitelist", "close") or None, custom_id=f"wl_close:{channel.id}")
        add_action_row(container, start_btn, close_btn)

        view = ui.LayoutView(timeout=None)
        view.add_item(container)
        await channel.send(view=view)
        await interaction.response.send_message(f"Η αίτηση σου: {channel.mention}", ephemeral=True)

    async def send_question(self, channel: discord.TextChannel, step: int):
        questions = getattr(config, "WHITELIST_QUESTIONS", [])
        q = questions[step]
        q_emoji = emoji("whitelist", "question")
        container = build_base_container(
            title=f"{q_emoji} Ερώτηση {step + 1}/{len(questions)}",
            description=q + "\n\n*Γράψε την απάντηση σου στο channel.*",
        )
        view = ui.LayoutView(timeout=None)
        view.add_item(container)
        await channel.send(view=view)

    async def handle_start(self, interaction: discord.Interaction, channel_id: int):
        store = storage.get_store(STORE_NAME)
        info = store.get(str(channel_id))
        if not info or interaction.user.id != info["user_id"]:
            await interaction.response.send_message("Μόνο αυτός που έκανε την αίτηση μπορεί να την ξεκινήσει.", ephemeral=True)
            return
        info["status"] = "answering"
        store[str(channel_id)] = info
        storage.save(STORE_NAME, store)
        await interaction.response.send_message("Ξεκινάμε.", ephemeral=True)
        await self.send_question(interaction.channel, 0)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        store = storage.get_store(STORE_NAME)
        info = store.get(str(message.channel.id))
        if not info or info.get("status") != "answering" or message.author.id != info["user_id"]:
            return
        await self._advance(message.channel, info, message.content)

    async def _advance(self, channel: discord.TextChannel, info: dict, answer: str):
        store = storage.get_store(STORE_NAME)
        questions = getattr(config, "WHITELIST_QUESTIONS", [])
        info["answers"].append(answer)
        step = info["current_step"] + 1
        info["current_step"] = step

        if step < len(questions):
            store[str(channel.id)] = info
            storage.save(STORE_NAME, store)
            await self.send_question(channel, step)
        else:
            info["status"] = "ready_to_submit"
            store[str(channel.id)] = info
            storage.save(STORE_NAME, store)

            container = build_base_container(
                title="Ολοκλήρωσες τις ερωτήσεις!",
                description="Πάτησε **Send** για να στείλεις την αίτηση.",
            )
            send_btn = ui.Button(label="Send", style=discord.ButtonStyle.success,
                                  emoji=emoji("whitelist", "send") or None, custom_id=f"wl_send:{channel.id}")
            add_action_row(container, send_btn)
            view = ui.LayoutView(timeout=None)
            view.add_item(container)
            await channel.send(view=view)

    async def handle_send(self, interaction: discord.Interaction, channel_id: int):
        store = storage.get_store(STORE_NAME)
        info = store.get(str(channel_id))
        if not info or interaction.user.id != info["user_id"]:
            await interaction.response.send_message("Μόνο αυτός που έκανε την αίτηση μπορεί να τη στείλει.", ephemeral=True)
            return

        if info.get("status") != "ready_to_submit":
            await interaction.response.send_message("Η αίτηση έχει ήδη σταλθεί.", ephemeral=True)
            return

        info["status"] = "submitted"
        store[str(channel_id)] = info
        storage.save(STORE_NAME, store)

        done_container = build_base_container(
            title="Ολοκλήρωσες τις ερωτήσεις!",
            description=" Η αίτηση στάλθηκε.",
        )
        link_url = getattr(config, "WHITELIST_LINK_URL", None)
        if link_url:
            add_separator(done_container)
            link_text = getattr(config, "WHITELIST_LINK_TEXT", "Για να μπορείς να μπείς στο roblox game μας θα πρέπει να είσαι μέλος στο roblox group.  Πάτα το **Join Now** για να μπείς.")
            link_label = getattr(config, "WHITELIST_LINK_LABEL", "Join Now")
            link_btn = ui.Button(label=link_label, style=discord.ButtonStyle.link, url=link_url)
            add_section_with_button(done_container, text=link_text, button=link_btn)
        done_view = ui.LayoutView(timeout=None)
        done_view.add_item(done_container)
        await interaction.response.edit_message(view=done_view)

        guild = interaction.guild
        applicant = guild.get_member(info["user_id"])
        log_channel = guild.get_channel(getattr(config, "LOG_WHITELIST_CHANNEL_ID", None))
        questions = getattr(config, "WHITELIST_QUESTIONS", [])

        container = build_base_container(
            title="Νέα Αίτηση — Whitelist",
            description=f"User: {applicant.mention if applicant else info['user_id']}",
        )
        add_separator(container)
        for q, a in zip(questions, info["answers"]):
            add_text(container, f"**{q}**\n{a}")
        add_separator(container)
        accept_btn = ui.Button(label="Accept", style=discord.ButtonStyle.success,
                                emoji=emoji("whitelist", "accept") or None, custom_id=f"wl_accept:{channel_id}")
        deny_btn = ui.Button(label="Deny", style=discord.ButtonStyle.danger,
                              emoji=emoji("whitelist", "deny") or None, custom_id=f"wl_deny:{channel_id}")
        add_action_row(container, accept_btn, deny_btn)

        view = ui.LayoutView(timeout=None)
        view.add_item(container)
        log_message = await log_channel.send(view=view)

        info["log_message_id"] = log_message.id
        store[str(channel_id)] = info
        storage.save(STORE_NAME, store)

    async def finalize_whitelist(self, interaction: discord.Interaction, channel_id: int, *, accepted: bool, reason: str | None = None):
        store = storage.get_store(STORE_NAME)
        info = store.get(str(channel_id))
        if not info:
            await interaction.response.send_message("Δεν βρέθηκε η αίτηση.", ephemeral=True)
            return

        guild = interaction.guild
        applicant = guild.get_member(info["user_id"])

        if accepted:
            role_id = getattr(config, "WHITELIST_ACCEPTED_ROLE_ID", None)
            if role_id:
                role = guild.get_role(role_id)
                if role and applicant:
                    await applicant.add_roles(role, reason="Whitelist accepted")
            info["status"] = "accepted"
            dm_text = "Η αίτηση whitelist σου έγινε **δεκτή**!"
        else:
            info["status"] = "denied"
            dm_text = f"Η αίτηση whitelist σου **απορρίφθηκε**.\nΛόγος: {reason}"

        info["decided_by"] = interaction.user.id
        info["decision_reason"] = reason
        store[str(channel_id)] = info
        storage.save(STORE_NAME, store)

        if applicant:
            try:
                await applicant.send(dm_text)
            except discord.Forbidden:
                pass

        check_emoji = emoji("whitelist", "check")
        deny_emoji = emoji("whitelist", "deny")
        status_text = (
            f"{check_emoji} **Accepted by** {interaction.user.mention}"
            if accepted
            else f"{deny_emoji} **Denied by** {interaction.user.mention}\nΛόγος: {reason}"
        )

        container = build_base_container(
            title="Αίτηση — Whitelist",
            description=f"User: {applicant.mention if applicant else info['user_id']}",
        )
        add_separator(container)
        add_text(container, status_text)
        add_separator(container)
        show_btn = ui.Button(
            label="Show Answers", style=discord.ButtonStyle.secondary,
            custom_id=f"wl_showanswers:{channel_id}",
        )
        add_action_row(container, show_btn)

        view = ui.LayoutView(timeout=None)
        view.add_item(container)

        if interaction.response.is_done():
            await interaction.message.edit(view=view)
        else:
            await interaction.response.edit_message(view=view)

    async def handle_show_answers(self, interaction: discord.Interaction, channel_id: int):
        store = storage.get_store(STORE_NAME)
        info = store.get(str(channel_id))
        if not info:
            await interaction.response.send_message("Δεν βρέθηκε η αίτηση.", ephemeral=True)
            return

        questions = getattr(config, "WHITELIST_QUESTIONS", [])
        lines = [f"**{q}**\n{a}" for q, a in zip(questions, info.get("answers", []))]
        reason = info.get("decision_reason")
        if reason:
            lines.append(f"**Λόγος**\n{reason}")

        text = "\n\n".join(lines) if lines else "Δεν υπάρχουν απαντήσεις."
        if len(text) > 3900:
            text = text[:3900] + "\n…"

        await interaction.response.send_message(text, ephemeral=True)

    async def handle_close(self, interaction: discord.Interaction, channel_id: int):
        if not _is_ownership(interaction.user):
            await interaction.response.send_message(" Μόνο το Ownership μπορεί να κλείσει αυτό το channel.", ephemeral=True)
            return

        store = storage.get_store(STORE_NAME)
        info = store.get(str(channel_id))
        if info:
            info["status"] = "closed"
            store[str(channel_id)] = info
            storage.save(STORE_NAME, store)
        await interaction.response.send_message(" Το channel κλείνει...", ephemeral=False)
        channel = interaction.guild.get_channel(channel_id)
        if channel:
            await channel.delete(reason=f"Whitelist closed by {interaction.user}")

    @app_commands.command(name="lockwhitelist", description="Κλειδώνει τις αιτήσεις whitelist")
    @app_commands.checks.has_any_role(config.OWNERSHIP_ROLE_ID)
    async def lockwhitelist(self, interaction: discord.Interaction):
        storage.save(LOCK_STORE, {"locked": True})
        await interaction.response.send_message(" Οι αιτήσεις whitelist κλειδώθηκαν.", ephemeral=True)

    @app_commands.command(name="unlockwhitelist", description="Ξεκλειδώνει τις αιτήσεις whitelist")
    @app_commands.checks.has_any_role(config.OWNERSHIP_ROLE_ID)
    async def unlockwhitelist(self, interaction: discord.Interaction):
        storage.save(LOCK_STORE, {"locked": False})
        await interaction.response.send_message("Οι αιτήσεις whitelist ξεκλειδώθηκαν.", ephemeral=True)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")

        if custom_id == "wl_apply":
            await self.start_apply(interaction)
        elif custom_id.startswith("wl_start:"):
            await self.handle_start(interaction, int(custom_id.split(":")[1]))
        elif custom_id.startswith("wl_send:"):
            await self.handle_send(interaction, int(custom_id.split(":")[1]))
        elif custom_id.startswith("wl_close:"):
            await self.handle_close(interaction, int(custom_id.split(":")[1]))
        elif custom_id.startswith("wl_showanswers:"):
            await self.handle_show_answers(interaction, int(custom_id.split(":")[1]))
        elif custom_id.startswith("wl_accept:"):
            channel_id = int(custom_id.split(":")[1])
            if not _is_ownership(interaction.user):
                await interaction.response.send_message(" Μόνο το Ownership μπορεί να δεχτεί αιτήσεις whitelist.", ephemeral=True)
                return
            await self.finalize_whitelist(interaction, channel_id, accepted=True)
        elif custom_id.startswith("wl_deny:"):
            channel_id = int(custom_id.split(":")[1])
            if not _is_ownership(interaction.user):
                await interaction.response.send_message(" Μόνο το Ownership μπορεί να απορρίψει αιτήσεις whitelist.", ephemeral=True)
                return
            await interaction.response.send_modal(WhitelistDenyReasonModal(channel_id, self))


async def setup(bot: commands.Bot):
    await bot.add_cog(Whitelist(bot))
