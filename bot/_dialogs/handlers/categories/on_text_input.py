from aiogram.types import Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import TextInput

from dialogs.states import MainMenuStates


async def on_category_text_input(message: Message, widget: TextInput, manager: DialogManager, data: str, **kwargs):
    manager.dialog_data["category"] = data
    await manager.switch_to(MainMenuStates.search_window, show_mode=ShowMode.EDIT)
    await message.delete()