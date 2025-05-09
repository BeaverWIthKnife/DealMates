from aiogram import F
from aiogram.types import Message
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import SwitchInlineQueryCurrentChat, Back
from aiogram_dialog.widgets.input import TextInput

from .states import MainMenuStates
from .handlers.categories.on_text_input import on_category_text_input


menu_dialog = Dialog(
    Window(
        Const("📍 Оберіть категорію потрібного товару"),
        SwitchInlineQueryCurrentChat(
            Const("🔎 Пошук категорії"),
            Const("")
        ),
        TextInput(id="categoryTextInput", on_success=on_category_text_input),
        state=MainMenuStates.main_window
    ),
    Window(
        Format("🧺 Оберіть потрібний продукт у категорії <b>{dialog_data[category]}</b>"),
        SwitchInlineQueryCurrentChat(
            Const("🔎 Пошук продукту"),
            Format("[{dialog_data[category]}] ")
        ),
        TextInput(id="productTextInput", on_success=None),
        Back(Const("‹ Назад")),
        state=MainMenuStates.search_window
    )
)