from aiogram.fsm.state import StatesGroup, State


class MealStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_new_param_value = State()


class UserSettingsStates(StatesGroup):
    choose_goal = State()
    change_weight = State()
    change_language = State()
