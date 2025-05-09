from aiogram.fsm.state import State, StatesGroup


class MainMenuStates(StatesGroup):
    main_window = State()
    search_window = State()