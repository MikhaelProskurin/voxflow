from datetime import datetime

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def tasks_confirmation_keyboard(
    titles: list[str],
    deadlines: list[datetime | None],
    exclude_indices: set[int] = None,
) -> InlineKeyboardMarkup:
    if not exclude_indices:
        exclude_indices = set()
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{title} — {deadline.strftime('%d-%m %H:%M') if deadline else 'No deadline'}",
                callback_data=f"task:confirm:{index}",
            )
        ]
        for index, (title, deadline) in enumerate(zip(titles, deadlines))
        if index not in exclude_indices
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
