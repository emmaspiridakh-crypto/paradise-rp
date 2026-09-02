from __future__ import annotations

import discord
from discord import ui


def build_base_container(
    *,
    title: str,
    description: str = "",
    banner_url: str | None = None,
    thumbnail_url: str | None = None,
     color: discord.Colour = discord.Colour.from_str("#593695"),
) -> ui.Container:
    container = ui.Container(accent_colour=color)

    if banner_url:
        container.add_item(ui.MediaGallery(discord.MediaGalleryItem(media=banner_url)))

    header_text = f"## {title}"
    if description:
        header_text += f"\n{description}"

    if thumbnail_url:
        section = ui.Section(accessory=ui.Thumbnail(media=thumbnail_url))
        section.add_item(ui.TextDisplay(header_text))
        container.add_item(section)
    else:
        container.add_item(ui.TextDisplay(header_text))

    return container


def add_separator(container: ui.Container, *, spacing: discord.SeparatorSpacing = discord.SeparatorSpacing.small) -> None:
    container.add_item(ui.Separator(spacing=spacing))


def add_text(container: ui.Container, text: str) -> None:
    container.add_item(ui.TextDisplay(text))


def add_action_row(container: ui.Container, *items: ui.Item) -> ui.ActionRow:

    row = ui.ActionRow()
    for item in items:
        row.add_item(item)
    container.add_item(row)
    return row


def add_section_with_button(
    container: ui.Container,
    *,
    text: str,
    button: ui.Button,
) -> ui.Section:

    section = ui.Section(accessory=button)
    section.add_item(ui.TextDisplay(text))
    container.add_item(section)
    return section


class SimpleLayoutView(ui.LayoutView):

    def __init__(self, container: ui.Container):
        super().__init__(timeout=None)
        self.add_item(container)
