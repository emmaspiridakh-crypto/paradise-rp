from __future__ import annotations

import discord
from discord import ui, app_commands
from discord.ext import commands

import config
from emojis import emoji
from utils import storage
from utils.permissions import has_roles
from utils.components import build_base_container, add_separator, add_text, add_action_row, add_section_with_button

STORE_NAME = "applications"
LOCKS_STORE = "application_locks"


def _q_text(q) -> str:
    return q["text"] if isinstance(q, dict) else q


def _q_type(q) -> str:
    return q.get("type", "text") if isinstance(q, dict) else "text"


def _safe_name(text: str) -> str:
    text = text.lower().strip().replace(" ", "-")
    return "".join(c for c in text if c.isalnum() or c == "-")[:90]


def _is_locked(type_key: str) -> bool:
    locks = storage.get_store(LOCKS_STORE)
    return bool(locks.get(type_key, False))


APPLICATION_TYPE_CHOICES = [
    app_commands.Choice(name=data["label"], value=key)
    for key, data in config.APPLICATION_TYPES.items()
]


class DenyReasonModal(ui.Modal, title="Αιτιολογία Απόρριψης"):
    reason = ui.TextInput(label="Λόγος απόρριψης", style=discord.TextStyle.paragraph, required=True, max_length=500)

    def __init__(self, channel_id: int, cog: "Applications"):
        super().__init__()
        self.channel_id = channel_id
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        await self.cog.finalize_application(interaction, self.channel_id, accepted=False, reason=str(self.reason))


class Applications(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="panel-applications", description="Στέλνει το Applications panel")
    @app_commands.checks.has_any_role(config.OWNERSHIP_ROLE_ID)
    async def panel_applications(self, interaction: discord.Interaction):
        container = build_base_container(
            title="Paradise Roleplay | Applications",
            description="Επίλεξε την ομάδα που σε ενδιαφέρει και υπόβαλε αίτηση.\n **Απαγορεύετε αυστηρά η χρήση του AI.**. **Έχεις 30 λεπτά να ολοκληρώσεις την αίτηση σου αλλιώς θα ακυρωθεί.** .",
            banner_url=config.APPLICATIONS_BANNER_URL,
        )
        add_separator(container)

        _app_info = {
            "elas":    {"description": "Προστάτεψε τους συμπολίτες σου. Διατήρησε την τάξη και κράτα την πόλη ασφαλή.",             "emoji_key": "elas"},
            "ekab":    {"description": "Γίνε ο ήρωας σε κάθε επείγον περιστατικό. Στήριξε τους ανθρώπους όταν σε χρειάζονται περισσότερο.", "emoji_key": "ekab"},
            "dikastiko": {"description": "Δούλεψε στο δικαστικό μέγαρο και κράτα την πόλη ασφαλή.", "emoji_key": "dikastiko"},
            "staff":   {"description": "Γίνε η δύναμη πίσω από την τάξη. Στήριξε την κοινότητα, βοήθησε τους παίκτες και κράτα τον server ασφαλή.", "emoji_key": "staff"},
            "manager": {"description": "Θέση υψηλής ευθύνης — διαχειρίσου server & ομάδα staff.",               "emoji_key": "manager"},
        }

        for key, data in config.APPLICATION_TYPES.items():
            info = _app_info.get(key, {"description": "", "emoji_key": "apply"})
            raw_emoji = emoji("applications", info["emoji_key"])
            locked = _is_locked(key)
            status_dot = emoji("applications", "status_closed") if locked else emoji("applications", "status_open")
            status_text = "κλειστές" if locked else "ανοιχτές"

            text = f"{raw_emoji} **{data['label']}**\n{info['description']}\n\n{status_dot} Αιτήσεις **{status_text}**"
            apply_btn = ui.Button(
                label="Apply Now", style=discord.ButtonStyle.secondary,
                emoji=raw_emoji if raw_emoji else None, disabled=locked,
                custom_id=f"app_apply:{key}",
            )
            add_section_with_button(container, text=text, button=apply_btn)
            add_separator(container)

        view = ui.LayoutView(timeout=None)
        view.add_item(container)
        await interaction.channel.send(view=view)
        await interaction.response.send_message("Στάλθηκε.", ephemeral=True)

    async def start_apply(self, interaction: discord.Interaction, type_key: str):
        data = config.APPLICATION_TYPES.get(type_key)
        if not data:
            await interaction.response.send_message("Άγνωστος τύπος αίτησης.", ephemeral=True)
            return

        if _is_locked(type_key):
            await interaction.response.send_message(
                f"Οι αιτήσεις για **{data['label']}** είναι κλειδωμένες αυτή τη στιγμή. Δοκίμασε ξανά αργότερα.",
                ephemeral=True,
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

        await interaction.response.defer(ephemeral=True)

        category = guild.get_channel(config.APPLICATIONS_CATEGORY_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        for role_id in config.STAFF_TEAM_ROLE_IDS:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"application-{type_key}-{_safe_name(user.display_name)}", category=category, overwrites=overwrites
        )

        store[str(channel.id)] = {
            "type": type_key, "user_id": user.id, "status": "pending",
            "current_step": 0, "answers": [],
        }
        storage.save(STORE_NAME, store)

        container = build_base_container(
            title=f"{data['label']} Application",
            description=f"{user.mention}\nΠάτησε **Start Your Application** όταν είσαι έτοιμος/η. Χρόνος ολοκλήρωσης: 30 λεπτά",
        )
        add_separator(container)
        start_btn = ui.Button(label="Start Your Application", style=discord.ButtonStyle.success, custom_id=f"app_start:{channel.id}")
        close_btn = ui.Button(label="Close", style=discord.ButtonStyle.danger, custom_id=f"app_close:{channel.id}")
        ping_btn = ui.Button(label="Ping User", style=discord.ButtonStyle.secondary,
                              emoji=emoji("tickets", "ping"), custom_id=f"app_ping_user:{channel.id}")
        add_action_row(container, start_btn, close_btn, ping_btn)

        view = ui.LayoutView(timeout=None)
        view.add_item(container)
        await channel.send(user.mention)
        await channel.send(view=view)
        await interaction.followup.send(f"Η αίτηση σου: {channel.mention}", ephemeral=True)

    async def send_question(self, channel: discord.TextChannel, type_key: str, step: int):
        questions = config.APPLICATION_TYPES[type_key]["questions"]
        q = questions[step]
        q_type = _q_type(q)

        if q_type == "yesno":
            container = build_base_container(
                title=f"Ερώτηση {step + 1}/{len(questions)}",
                description=_q_text(q),
            )
            yes_btn = ui.Button(label="Ναι", style=discord.ButtonStyle.success,
                                 emoji=emoji("applications", "yes"), custom_id=f"app_yn:{channel.id}:yes")
            no_btn = ui.Button(label="Όχι", style=discord.ButtonStyle.danger,
                                emoji=emoji("applications", "no"), custom_id=f"app_yn:{channel.id}:no")
            add_action_row(container, yes_btn, no_btn)
        else:
            container = build_base_container(
                title=f"Ερώτηση {step + 1}/{len(questions)}",
                description=_q_text(q) + "\n\n*Γράψε την απάντηση σου στο channel.*",
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
        await self.send_question(interaction.channel, info["type"], 0)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        store = storage.get_store(STORE_NAME)
        info = store.get(str(message.channel.id))
        if not info or info.get("status") != "answering" or message.author.id != info["user_id"]:
            return

        questions = config.APPLICATION_TYPES[info["type"]]["questions"]
        current_q = questions[info["current_step"]]
        if _q_type(current_q) == "yesno":
            return

        await self._advance(message.channel, info, message.content)

    async def _advance(self, channel: discord.TextChannel, info: dict, answer: str):
        store = storage.get_store(STORE_NAME)
        questions = config.APPLICATION_TYPES[info["type"]]["questions"]
        info["answers"].append(answer)
        step = info["current_step"] + 1
        info["current_step"] = step

        if step < len(questions):
            store[str(channel.id)] = info
            storage.save(STORE_NAME, store)
            await self.send_question(channel, info["type"], step)
        else:
            info["status"] = "ready_to_submit"
            store[str(channel.id)] = info
            storage.save(STORE_NAME, store)

            container = build_base_container(
                title="Ολοκλήρωσες τις ερωτήσεις",
                description="Πάτησε **Send** για να στείλεις την αίτηση.",
            )
            send_btn = ui.Button(label="Send", style=discord.ButtonStyle.success,
                                  emoji=emoji("applications", "send"), custom_id=f"app_send:{channel.id}")
            add_action_row(container, send_btn)
            view = ui.LayoutView(timeout=None)
            view.add_item(container)
            await channel.send(view=view)

    async def handle_yesno(self, interaction: discord.Interaction, channel_id: int, answer: str):
        store = storage.get_store(STORE_NAME)
        info = store.get(str(channel_id))
        if not info or interaction.user.id != info["user_id"] or info.get("status") != "answering":
            await interaction.response.send_message("Μόνο αυτός που έκανε την αίτηση μπορεί να απαντήσει.", ephemeral=True)
            return

        questions = config.APPLICATION_TYPES[info["type"]]["questions"]
        current_q = questions[info["current_step"]]
        if _q_type(current_q) != "yesno":
            await interaction.response.send_message("Αυτή η ερώτηση δεν απαντιέται με Ναι/Όχι.", ephemeral=True)
            return

        await interaction.response.defer()
        label = "Ναι" if answer == "yes" else "Όχι"
        await self._advance(interaction.channel, info, label)

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
            title="Ολοκλήρωσες τις ερωτήσεις",
            description=" Η αίτηση σου στάλθηκε. Θα βγεί announcement για τα αποτελέσματα και θα σου σταλθεί και DM, φρόντισε να μην τα έχεις κλειστά.",
        )
        done_view = ui.LayoutView(timeout=None)
        done_view.add_item(done_container)
        await interaction.response.edit_message(view=done_view)

        guild = interaction.guild
        applicant = guild.get_member(info["user_id"])
        log_channel_id = config.LOG_APPLICATIONS_CHANNEL_IDS.get(info["type"], config.LOG_APPLICATIONS_CHANNEL_ID)
        log_channel = guild.get_channel(log_channel_id)

        type_label = config.APPLICATION_TYPES[info["type"]]["label"]
        questions = config.APPLICATION_TYPES[info["type"]]["questions"]

        container = build_base_container(
            title=f"Νέα Αίτηση — {type_label}",
            description=f"User: {applicant.mention if applicant else info['user_id']}",
        )
        add_separator(container)
        for q, a in zip(questions, info["answers"]):
            add_text(container, f"**{_q_text(q)}**\n{a}")
        add_separator(container)
        accept_btn = ui.Button(label="Accept", style=discord.ButtonStyle.success,
                                emoji=emoji("applications", "accept"), custom_id=f"app_accept:{channel_id}")
        deny_btn = ui.Button(label="Deny", style=discord.ButtonStyle.danger,
                              emoji=emoji("applications", "deny"), custom_id=f"app_deny:{channel_id}")
        add_action_row(container, accept_btn, deny_btn)

        view = ui.LayoutView(timeout=None)
        view.add_item(container)
        if applicant:
            await log_channel.send(applicant.mention)
        log_message = await log_channel.send(view=view)

        info["log_message_id"] = log_message.id
        store[str(channel_id)] = info
        storage.save(STORE_NAME, store)

    async def finalize_application(self, interaction: discord.Interaction, channel_id: int, *, accepted: bool, reason: str | None = None):
        store = storage.get_store(STORE_NAME)
        info = store.get(str(channel_id))
        if not info:
            await interaction.response.send_message("Δεν βρέθηκε η αίτηση.", ephemeral=True)
            return

        if not interaction.response.is_done():
            await interaction.response.defer()

        guild = interaction.guild
        applicant = guild.get_member(info["user_id"])

        if accepted:
            role_id = config.APPLICATION_ACCEPTED_ROLES.get(info["type"])
            if role_id:
                role = guild.get_role(role_id)
                if role and applicant:
                    await applicant.add_roles(role, reason="Application accepted")
            info["status"] = "accepted"
            if info["type"] in ("staff", "manager"):
                dm_text = (
                    f"Η αίτηση σου ({config.APPLICATION_TYPES[info['type']]['label']}) έγινε **δεκτή**! "
                    f"Ενημέρωσε στο αντίστοιχο channel πότε μπορείς για το interview σου."
                )
            else:
                dm_text = f"Η αίτηση σου ({config.APPLICATION_TYPES[info['type']]['label']}) έγινε **δεκτή**!"
        else:
            info["status"] = "denied"
            dm_text = f"Η αίτηση σου ({config.APPLICATION_TYPES[info['type']]['label']}) **απορρίφθηκε**.\nΛόγος: {reason}"

        info["decided_by"] = interaction.user.id
        info["decision_reason"] = reason
        store[str(channel_id)] = info
        storage.save(STORE_NAME, store)

        if applicant:
            try:
                await applicant.send(dm_text)
            except discord.Forbidden:
                pass

        type_label = config.APPLICATION_TYPES[info["type"]]["label"]

        if accepted:
            await self._send_accept_announcement(guild, info["type"], applicant, info, dm_text, type_label)

        status_text = (
            f" **Accepted by** {interaction.user.mention}"
            if accepted
            else f" **Denied by** {interaction.user.mention}\nΛόγος: {reason}"
        )

        container = build_base_container(
            title=f"Αίτηση — {type_label}",
            description=f"User: {applicant.mention if applicant else info['user_id']}",
        )
        add_separator(container)
        add_text(container, status_text)
        add_separator(container)
        show_btn = ui.Button(
            label="Show Answers", style=discord.ButtonStyle.secondary,
            custom_id=f"app_showanswers:{channel_id}",
        )
        add_action_row(container, show_btn)

        view = ui.LayoutView(timeout=None)
        view.add_item(container)
        await interaction.message.edit(view=view)

    async def _send_accept_announcement(self, guild: discord.Guild, type_key: str, applicant, info: dict, dm_text: str, type_label: str):
        announce_channel_id = config.APPLICATION_ANNOUNCE_CHANNEL_IDS.get(type_key)
        if not announce_channel_id:
            return
        announce_channel = guild.get_channel(int(announce_channel_id))
        if not announce_channel:
            return

        mention = applicant.mention if applicant else f"<@{info['user_id']}>"

        if type_key == "staff":
            mention_channel = guild.get_channel(int(config.APPLICATION_ANNOUNCE_STAFF_MENTION_CHANNEL_ID))
            mention_text = mention_channel.mention if mention_channel else ""
            text = f"{mention} Η αίτηση σου ({type_label}) έγινε **δεκτή**! Ενημέρωσε στο {mention_text} πότε μπορείς για το interview σου."
        else:
            mention_channel = guild.get_channel(int(config.APPLICATION_ANNOUNCE_MENTION_CHANNEL_ID))
            mention_text = mention_channel.mention if mention_channel else ""
            text = f"Η αίτηση του {mention} έγινε δεκτή για **{type_label}**. Δες το {mention_text} για τον κατάλληλο server ώστε να κάνεις interview."

        try:
            await announce_channel.send(text)
        except discord.Forbidden:
            pass

    async def handle_show_answers(self, interaction: discord.Interaction, channel_id: int):
        store = storage.get_store(STORE_NAME)
        info = store.get(str(channel_id))
        if not info:
            await interaction.response.send_message("Δεν βρέθηκε η αίτηση.", ephemeral=True)
            return

        questions = config.APPLICATION_TYPES[info["type"]]["questions"]
        lines = [f"**{_q_text(q)}**\n{a}" for q, a in zip(questions, info.get("answers", []))]
        reason = info.get("decision_reason")
        if reason:
            lines.append(f"**Λόγος**\n{reason}")

        text = "\n\n".join(lines) if lines else "Δεν υπάρχουν απαντήσεις."
        if len(text) > 3900:
            text = text[:3900] + "\n…"

        await interaction.response.send_message(text, ephemeral=True)

    async def handle_close(self, interaction: discord.Interaction, channel_id: int):
        store = storage.get_store(STORE_NAME)
        info = store.get(str(channel_id))
        if info:
            info["status"] = "closed"
            store[str(channel_id)] = info
            storage.save(STORE_NAME, store)
        await interaction.response.send_message(" Το channel κλείνει...", ephemeral=False)
        channel = interaction.guild.get_channel(channel_id)
        if channel:
            await channel.delete(reason=f"Application closed by {interaction.user}")

    async def handle_ping_user(self, interaction: discord.Interaction, channel_id: int):
        store = storage.get_store(STORE_NAME)
        info = store.get(str(channel_id))
        if not info:
            await interaction.response.send_message("Δεν βρέθηκε η αίτηση.", ephemeral=True)
            return

        if not has_roles(interaction.user, config.STAFF_TEAM_ROLE_IDS):
            await interaction.response.send_message(" Μόνο το staff team μπορεί να κάνει ping τον χρήστη.", ephemeral=True)
            return

        guild = interaction.guild
        applicant = guild.get_member(info["user_id"])
        await interaction.response.send_message(f" {applicant.mention if applicant else ''}", ephemeral=False)
        if applicant:
            try:
                await applicant.send(f" Έχεις ειδοποίηση στην αίτηση σου: {interaction.channel.mention}")
            except discord.Forbidden:
                pass

    @app_commands.command(name="lockapplication", description="Κλειδώνει έναν τύπο αίτησης")
    @app_commands.describe(name="Ο τύπος αίτησης προς κλείδωμα")
    @app_commands.choices(name=APPLICATION_TYPE_CHOICES)
    @app_commands.checks.has_any_role(config.OWNERSHIP_ROLE_ID)
    async def lockapplication(self, interaction: discord.Interaction, name: app_commands.Choice[str]):
        locks = storage.get_store(LOCKS_STORE)
        locks[name.value] = True
        storage.save(LOCKS_STORE, locks)
        await interaction.response.send_message(f" Οι αιτήσεις **{name.name}** κλειδώθηκαν.", ephemeral=True)

    @app_commands.command(name="unlockapplication", description="Ξεκλειδώνει έναν τύπο αίτησης")
    @app_commands.describe(name="Ο τύπος αίτησης προς ξεκλείδωμα")
    @app_commands.choices(name=APPLICATION_TYPE_CHOICES)
    @app_commands.checks.has_any_role(config.OWNERSHIP_ROLE_ID)
    async def unlockapplication(self, interaction: discord.Interaction, name: app_commands.Choice[str]):
        locks = storage.get_store(LOCKS_STORE)
        locks[name.value] = False
        storage.save(LOCKS_STORE, locks)
        await interaction.response.send_message(f"Οι αιτήσεις **{name.name}** ξεκλειδώθηκαν.", ephemeral=True)

    @app_commands.command(name="lockallapplications", description="Κλειδώνει ΟΛΟΥΣ τους τύπους αιτήσεων μαζί")
    @app_commands.checks.has_any_role(config.OWNERSHIP_ROLE_ID)
    async def lockallapplications(self, interaction: discord.Interaction):
        locks = {key: True for key in config.APPLICATION_TYPES}
        storage.save(LOCKS_STORE, locks)
        await interaction.response.send_message(" Όλες οι αιτήσεις κλειδώθηκαν.", ephemeral=True)

    @app_commands.command(name="unlockallapplications", description="Ξεκλειδώνει ΟΛΟΥΣ τους τύπους αιτήσεων μαζί")
    @app_commands.checks.has_any_role(config.OWNERSHIP_ROLE_ID)
    async def unlockallapplications(self, interaction: discord.Interaction):
        locks = {key: False for key in config.APPLICATION_TYPES}
        storage.save(LOCKS_STORE, locks)
        await interaction.response.send_message("Όλες οι αιτήσεις ξεκλειδώθηκαν.", ephemeral=True)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")

        if custom_id.startswith("app_apply:"):
            value = custom_id.split(":", 1)[1]
            await self.start_apply(interaction, value)
        elif custom_id.startswith("app_start:"):
            await self.handle_start(interaction, int(custom_id.split(":")[1]))
        elif custom_id.startswith("app_yn:"):
            _, ch_id, answer = custom_id.split(":")
            await self.handle_yesno(interaction, int(ch_id), answer)
        elif custom_id.startswith("app_send:"):
            await self.handle_send(interaction, int(custom_id.split(":")[1]))
        elif custom_id.startswith("app_close:"):
            await self.handle_close(interaction, int(custom_id.split(":")[1]))
        elif custom_id.startswith("app_ping_user:"):
            await self.handle_ping_user(interaction, int(custom_id.split(":")[1]))
        elif custom_id.startswith("app_showanswers:"):
            await self.handle_show_answers(interaction, int(custom_id.split(":")[1]))
        elif custom_id.startswith("app_accept:"):
            channel_id = int(custom_id.split(":")[1])
            if not self._can_review(interaction.user, channel_id):
                await interaction.response.send_message("Δεν έχεις δικαίωμα.", ephemeral=True)
                return
            await self.finalize_application(interaction, channel_id, accepted=True)
        elif custom_id.startswith("app_deny:"):
            channel_id = int(custom_id.split(":")[1])
            if not self._can_review(interaction.user, channel_id):
                await interaction.response.send_message(" Δεν έχεις δικαίωμα.", ephemeral=True)
                return
            await interaction.response.send_modal(DenyReasonModal(channel_id, self))

    def _can_review(self, member: discord.Member, channel_id: int) -> bool:
        store = storage.get_store(STORE_NAME)
        info = store.get(str(channel_id))
        if not info:
            return False
        review_roles = config.APPLICATION_REVIEW_ROLES.get(info["type"], [])
        return has_roles(member, review_roles)


async def setup(bot: commands.Bot):
    await bot.add_cog(Applications(bot))
