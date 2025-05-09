from aiogram.fsm.state import State, StatesGroup


class States(StatesGroup):
    category_search = State()
    lobby_search = State()
    in_lobby = State()
    amount_input = State()