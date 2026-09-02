from __future__ import annotations

import discord
from discord import app_commands, ui
from discord.ext import commands

import config
from utils.permissions import slash_is_staff_team

ACCENT_COLOR = discord.Colour.from_str("#593695")

RULES_PANEL_BANNER_URL = "https://i.imgur.com/qaCEDaG.jpeg"


def _section(container: ui.Container, title: str, lines: list[str]) -> None:
    text = f"### {title}\n" + "\n".join(lines)
    container.add_item(ui.TextDisplay(text))


def build_general_rules_containers() -> list[ui.Container]:
    part1 = ui.Container(accent_colour=ACCENT_COLOR)
    part1.add_item(ui.TextDisplay("## General Rules"))
    part1.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
    part1.add_item(ui.TextDisplay(
        "**Paradise Roleplay Roblox**\n"
        "Καλώς ήρθατε στον Paradise RP server.\n\n"
        "Παρακαλώ διαβάστε και τηρήστε τους παρακάτω κανόνες.\n"
        "Μη τήρηση των κανόνων θεωρείται αδυναμία role play και θα τιμωρείται ανάλογα την "
        "παράβαση με warning/kick/ban.\n\n"
        "Ο server είναι τύπου Roleplay και ζητάμε από του παίκτες να φτιάξουνε έναν χαρακτήρα με "
        "συγκεκριμένο background και ιστορικό ο οποίος θα αλληλεπιδρά με τους άλλους και με τον "
        "γύρω κόσμο."
    ))
    part1.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
    container = part1

    _section(container, "Αφορά τα μαγαζιά", [
        "Προσέχουμε πάντα για να έχουμε όπως λέει και ο λαός! Δεν χρειάζεται να χρεώνετε ένα "
        "μαγαζί με τις διάφορες κινήσεις σας. Πολλοί από σας δεν καταλαβαίνετε το ότι ένα μαγαζί "
        "θα έχει και τις επιπτώσεις του (πρόστιμο, κλείσιμο κτλ) αν η αστυνομία έχει στοιχεία που "
        "το συνδέουν με κάποιο «gang» π.χ. είστε ενεργοί σε μαγαζί με μάσκα/bandana. Οπότε το "
        "καλύτερο που έχετε να κάνετε είναι να προστατέψετε τα μαγαζιά σας και ταυτόχρονα να μην "
        "κάνετε δραστηριότητες που τα συνδέουν με την ομάδα σας.",
    ])
    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

    _section(container, "VOL", [
        "Το VOL είναι όταν κάποιος παίκτης δεν λογαριάζει τη ζωή του όπως στην πραγματικότητα. "
        "Δηλαδή το να μην φοβάστε για τη ζωή σας, όπως θα γινόταν σε ρεαλιστικά πλαίσια, όσο "
        "απειλείστε με όπλα ή άλλα μέσα που μπορεί να αντιμετωπίσετε σε μελλοντικά σενάρια.",
        "• Κατά τη διάρκεια του game θα έρθουν αρκετές περιπτώσεις όπου κάποιος θα απειλεί τη ζωή "
        "του χαρακτήρα σας. Θα πρέπει όλοι, σε όλα τα σενάρια, να έχουν στο πίσω μέρος του μυαλού "
        "τους ότι η ζωή του χαρακτήρα τους πρέπει πάντα να είναι πάνω απ' όλα. Αυτό ισχύει και για "
        "cops vs criminals, και για criminals vs criminals.",
    ])
    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

    _section(container, "Combat Log", [
        "Το COMBAT LOG αναφέρεται στο όταν κάνεις quit από το παιχνίδι ενώ είσαι πεθαμένος, "
        "λιπόθυμος η σε κάποιο σκηνικό. Είναι ένα γεγονός το οποίο απαγορεύεται ρητά.",
    ])
    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

    _section(container, "Αφορά το χαρακτηριστικό τις ομάδας σας (bandana/μάσκα)", [
        "Σταματήστε να κυκλοφορείτε μόνιμα με μια bandana στο πρόσωπο, στο παντελόνι, στο κεφάλι "
        "και στο χέρι και γενικά σταματήστε να προβάλετε το ότι ανήκετε σε κάποια criminal ομάδα. "
        "Σκοπός του criminal είναι να μην γνωρίζει κάποιος το τι κάνετε ή τις κινήσεις σας ούτε "
        "πρέπει να γνωρίζουν αν ανήκετε κάπου (αυτοί που πρέπει να το γνωρίζουν το ξέρουν ήδη και "
        "όσοι δεν το ξέρουν θα το μάθουν).",
    ])
    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

    _section(container, "Αφορά το κομμάτι απλού πολίτη", [
        "Μην ξεχνάτε πως ότι και να κάνετε ότι και να τρέχετε πάντα θα είστε πολίτες, δηλαδή, το "
        "ότι ανήκετε σε μια ομάδα, δεν σημαίνει ότι το μόνο πράγμα που θα πρέπει να κάνετε αφορά "
        "όπλα είτε αυτό αφορά κάποιο ναρκωτικό είτε λεφτά. Το κομμάτι civilian είναι το πιο "
        "δύσκολο και το πιο χρήσιμο για έναν criminal player γιατί μέσα από εκεί πρώτον μαθαίνει "
        "το τι συμβαίνει στην πόλη, δεύτερον είναι μια πολύ καλή κάλυψη σε διάφορα θέματα ή "
        "σκηνικά που μπορεί να προκύψουν και πολλά άλλα που θα τα καταλάβετε και μόνοι σας.",
    ])
    part2 = ui.Container(accent_colour=ACCENT_COLOR)
    part2.add_item(ui.TextDisplay("## General Rules"))
    part2.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
    container = part2

    _section(container, "Αφορά εσάς προς την Αστυνομία", [
        "Σταματήστε να είστε επιθετικοί απέναντι στην αστυνομία. Δεν θα είστε ΠΟΤΕ μα ΠΟΤΕ "
        "καλύτεροι ή πιο μπροστά από αυτούς σε θέμα εξοπλισμού/οικονομίας. Αυτό δεν είναι δύσκολο "
        "να καταλάβετε γιατί το λέμε (ακόμα και μια σφαίρα να χαλάσετε απέναντι στην αστυνομία "
        "είναι μείον για σας). Όταν είναι αντίπαλος σας η αστυνομία η καλύτερη λύση είναι να "
        "σκεφτείτε έξυπνα και να βρείτε έναν τρόπο να ξεφύγετε από μια κατάσταση. Τα \"σούτια\" με "
        "την αστυνομία σίγουρα θα υπάρξουν αλλά κάντε το για κάτι που θα αξίζει και μόνο όταν "
        "είναι η τελευταία επιλογή. Μην προσπαθήσετε να το παίξετε «gangsta OG» ή ότι άλλο μπορεί "
        "να θέλετε να το παίξετε, χαμένοι θα βγείτε απ' όλο αυτό. Προσπαθήστε να δώσετε αξία σε "
        "αυτό που κάνετε. Υπάρχουν τρόποι να βγείτε μπροστά από την αστυνομία σκεφτείτε σενάρια "
        "«keep that in mind».",
    ])
    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

    _section(container, "Αφορά την επιθετική συμπεριφορά", [
        "Σταματήστε να έχετε επιθετική διάθεση ακόμα και σε απλά πράγματα γιατί το μόνο που θα "
        "κερδίσετε είναι αρνητισμό. Δεν χρειάζεται να προβάλετε τον εαυτό σας ως μάγκα μπορείτε "
        "να κερδίσετε ότι προσπαθείτε να κερδίσετε με αυτό και με άλλους τρόπους. Δεν χρειάζεται "
        "να φαίνεστε παντού γιατί το αποτέλεσμα δεν θα είναι ωραίο.",
    ])
    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

    _section(container, "Αφορά τις πληροφορίες", [
        "Οι πληροφορίες ειδικά για το κομμάτι του criminal είναι ένα από τα δυνατότερα όπλα. "
        "Σταματήστε να μοιράζετε πληροφορίες δεξιά και αριστερά ή τουλάχιστον μην τις δίνετε "
        "χωρίς να έχετε κάτι να κερδίσετε και εσείς. Δεν γίνετε να βρίσκει κάποιος κάτι και μέσα "
        "σε 24 ώρες να το έχουν μάθει μέχρι και στην Αστυνομία. Αν δεν κρατάτε πληροφορίες Η τις "
        "μοιράζεται δεξιά, αριστερά χωρίς κέρδος θα δημιουργείται πάντα προβλήματα.",
    ])

    part3 = ui.Container(accent_colour=ACCENT_COLOR)
    part3.add_item(ui.TextDisplay("## General Rules"))
    part3.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))
    container = part3

    _section(container, "RDM", [
        "Το RDM είναι όταν ένας παίκτης πάει και σκοτώνει έναν άλλο παίκτη, χωρίς να έχει "
        "προηγηθεί κάποιο RP ή INTERACT.",
        "Απαγορεύεται αυστηρά να σκοτώσω κάποιον επειδή με τράκαρε η αντίστοιχα επειδή τον "
        "τράκαρα εγώ και μη έβρισε θα πρέπει να παίζετε RP και μόνο.",
    ])
    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

    _section(container, "VDM", [
        "Το VDM είναι όταν ένας παίκτης χτυπά κάποιον άλλον παίκτη με το αμάξι του και δεν "
        "σταματήσει να δει αν είναι καλά ή αν χρειάζεται ασθενοφόρο.",
    ])
    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

    _section(container, "METAGAMING", [
        "Το METAGAMING είναι όταν κάποιος παίκτης χρησιμοποιεί πληροφορίες που αποκτήθηκαν χωρίς "
        "RP. Το να χρησιμοποιείτε ή να αναμεταδίδετε, σκοπίμως, πληροφορίες που ο χαρακτήρας σας "
        "δεν έμαθε In Character (μέσω Discord channels, Twitch chats). Προσπαθήστε να αποφύγετε "
        "τη δημιουργία πολλών χαρακτήρων που εμπλέκονται στα ίδια σενάρια, λόγω του ότι ασυνείδητα "
        "θα μπορούσατε να μεταφέρετε τις πληροφορίες από τον έναν χαρακτήρα στον άλλον.",
    ])
    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

    _section(container, "New Life Rule", [
        "Όταν πεθαίνει κάποιος παίκτης σε οποιοδήποτε σκηνικό και κάνεις respawn, δεν θυμάται τι "
        "έχει γίνει στο συγκεκριμένο σκηνικό και επιπλέον δεν μπορεί να γυρίσει σε αυτό εκτός αν "
        "περάσει το χρονικό περιθώριο των 30 λεπτών και δεν τον καλέσει (INGAME η ομάδα σου) να "
        "πάει πάλι.",
    ])

    return [part1, part2, part3]


def build_police_ekab_container() -> ui.Container:
    container = ui.Container(accent_colour=ACCENT_COLOR)
    container.add_item(ui.TextDisplay("## Police / EKAB Rules"))
    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

    _section(container, "Ε.Λ.ΑΣ", [
        "Η Αστυνομία απαγορεύεται να διενεργήσει σωματικό έλεγχο σε τροχονομικό έλεγχο, εκτός εάν "
        "πληρούνται δύο από τις τρεις ακόλουθες προϋποθέσεις: ύπαρξη οπλοθηκής, χρήση μάσκας ή "
        "φιμέ τζάμια. Ωστόσο, αν έχει προηγηθεί καταδίωξη, αυτό από μόνο του αρκεί για τη "
        "διενέργεια σωματικού ελέγχου. ΔΕΝ εξαιρούνται οι ειδικές επιχειρησιακές ομάδες της "
        "Αστυνομίας (ΟΠΚΕ).",
        "",
        "Για να πραγματοποιηθεί Open Up η αστυνομία πρέπει να έχει ταυτοποιήσει τουλάχιστον 5 "
        "ΚΥΡΙΑ μέλη της εγκληματικής οργάνωσης και να έχει συλλέξει πληροφορίες.",
        "",
        "Όταν γίνεται μεταγωγή στις φυλακές, η Αστυνομία/Εισαγγελία είναι υποχρεωμένη να "
        "ενημερώσει ότι διεξάγεται μεταγωγή στις φυλακές και η εθνική είναι κλειστή.",
        "",
        "Το όριο της αστυνομίας για επιχείρηση είναι 12 άτομα.",
        "",
        "**Κανόνας στα Κελιά:** Σε περίπτωση που οποιοσδήποτε βρεθεί στα κελιά και δεν δείχνει "
        "την ανάλογη συμπεριφορά η ποινή του θα είναι διπλάσια καθώς δεν δείχνει το Fear Of "
        "Police & δεν κάνει Value Of Life.",
        "",
        "**Κανόνας Προσέλευσης Δικηγόρου στα κελιά:** Σε περίπτωση που δεν προσέλθει δικηγόρος σε "
        "χρονικό διάστημα 10 λεπτών, να μπορεί αυτοδίκαια η Αστυνομία να προχωρήσει στην απόδοση "
        "Κατηγοριών και χρηματικών προστίμων.",
        "",
        "Σε περίπτωση απαγωγής: Εισαγγελέας / Δήμαρχος & Υψηλόβαθμα Στελέχη της ΕΛ.ΑΣ. που σε αυτό "
        "το σενάριο μπορεί να είναι UNLIMITED!",
        "",
        "Όταν άτομα μιας criminal ομάδας έχουν \"πιαστεί\" από την αστυνομία ο μόνος λόγος για να "
        "χτυπήσετε την αστυνομία είναι ΝΑ ΧΤΥΠΗΣΕΤΕ ΤΗΝ ΜΕΤΑΓΩΓΗ.",
    ])
    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

    _section(container, "Ε.Κ.Α.Β", [
        "• Απαγορεύεται το ΕΚΑΒ να σηκώσει άτομα τα οποία έχουν πέσει από μεγάλο ύψος η έχουν "
        "πεθάνει από έκρηξη, πνιγμό.",
        "• Το ΕΚΑΒ μπορεί να δώσει τις πρώτες βοήθειες στο ίδιο άτομο μέχρι 1 φορά σε ένα σκηνικό.",
        "• Απαγορεύεται ρητά κάθε εγκληματική ενέργεια από προσωπικό του ΕΚΑΒ.",
    ])

    return container


def build_zones_container() -> ui.Container:
    container = ui.Container(accent_colour=ACCENT_COLOR)
    container.add_item(ui.TextDisplay("## Zones"))
    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

    _section(container, "Greenzone", [
        "Green Zone είναι οι περιοχές οι οποίες δεν μπορείτε να πυροβολήσετε.",
        "",
        "**Τα Green Zone είναι:**",
        "• ΕΚΑΒ",
        "• Ελληνική Αστυνομία",
        "• Δικαστικό μέγαρο",
        "• Πλατεία",
    ])
    container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

    _section(container, "Neutral Zone", [
        "Neutral Zone δεν μπορείτε να πυροβολήσετε πουθενά εκτός κι αν έχει προηγηθεί θούν 5 "
        "λεπτά σκηνικό.",
        "",
        "Όλο το υπόλοιπο Map.",
    ])

    return container


class RulesPanel(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def build_panel_view(self) -> ui.LayoutView:
        container = ui.Container(accent_colour=ACCENT_COLOR)

        if RULES_PANEL_BANNER_URL:
            container.add_item(ui.MediaGallery(discord.MediaGalleryItem(media=RULES_PANEL_BANNER_URL)))
            container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        container.add_item(ui.TextDisplay(
            "# Κανόνες Paradise Roleplay\nΠατήστε ένα από τα παρακάτω κουμπιά για να δείτε τους "
            "αντίστοιχους κανόνες. Είναι αναγκαστηκή η γνώση των κανόνων."
        ))
        container.add_item(ui.Separator(spacing=discord.SeparatorSpacing.small))

        row = ui.ActionRow()
        row.add_item(ui.Button(
            label="General Rules",
            style=discord.ButtonStyle.secondary,
            custom_id="rules_panel_general",
        ))
        row.add_item(ui.Button(
            label="Police / EKAB Rules",
            style=discord.ButtonStyle.secondary,
            custom_id="rules_panel_police_ekab",
        ))
        row.add_item(ui.Button(
            label="Zones",
            style=discord.ButtonStyle.secondary,
            custom_id="rules_panel_zones",
        ))
        container.add_item(row)

        view = ui.LayoutView(timeout=None)
        view.add_item(container)
        return view

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")

        if custom_id == "rules_panel_general":
            containers = build_general_rules_containers()
            view1 = ui.LayoutView(timeout=None)
            view1.add_item(containers[0])
            await interaction.response.send_message(view=view1, ephemeral=True)
            for extra in containers[1:]:
                view = ui.LayoutView(timeout=None)
                view.add_item(extra)
                await interaction.followup.send(view=view, ephemeral=True)
        elif custom_id == "rules_panel_police_ekab":
            view = ui.LayoutView(timeout=None)
            view.add_item(build_police_ekab_container())
            await interaction.response.send_message(view=view, ephemeral=True)
        elif custom_id == "rules_panel_zones":
            view = ui.LayoutView(timeout=None)
            view.add_item(build_zones_container())
            await interaction.response.send_message(view=view, ephemeral=True)

    @app_commands.command(name="panel-rules", description="Στέλνει το panel με τους κανόνες του server")
    @slash_is_staff_team()
    async def panel_rules(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        view = self.build_panel_view()
        await interaction.channel.send(view=view)
        await interaction.followup.send("Το rules panel στάλθηκε.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(RulesPanel(bot))
    
