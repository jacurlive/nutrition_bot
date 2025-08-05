import datetime

from aiogram import types

from utils.translation.localization import get_localized_message


async def language_keyboard():

    language_kb = [
        [
            types.InlineKeyboardButton(text="uz🇺🇿", callback_data="uz"),
            types.InlineKeyboardButton(text="ru🇷🇺", callback_data="ru"),
            types.InlineKeyboardButton(text="eng🇺🇸", callback_data="en")
        ]
    ]

    language_k = types.InlineKeyboardMarkup(inline_keyboard=language_kb)

    return language_k


async def main_menu_keyboard(language):
    button_text_1 = await get_localized_message(language, "add_meal_btn")
    button_text_2 = await get_localized_message(language, "my_diary_btn")
    button_text_3 = await get_localized_message(language, "settings_btn")
    button_text_4 = await get_localized_message(language, "help_btn")

    keyboard=[
        [
            types.KeyboardButton(text=button_text_1),
            types.KeyboardButton(text=button_text_2),
        ],
        [
            types.KeyboardButton(text=button_text_3),
            types.KeyboardButton(text=button_text_4)
        ]
    ]

    return types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, input_field_placeholder="Choose")


async def settings_menu_keyboard(language):
    text_goal = await get_localized_message(language, "change_goal")
    text_weight = await get_localized_message(language, "change_weight")
    text_lang = await get_localized_message(language, "change_language")
    text_reminder = await get_localized_message(language, "toggle_reminder")
    text_back = await get_localized_message(language, "back_to_menu")

    keyboard = [
        [
            types.KeyboardButton(text=text_goal),
            types.KeyboardButton(text=text_weight)
        ],
        [
            types.KeyboardButton(text=text_lang),
            types.KeyboardButton(text=text_reminder)
        ],
        [
            types.KeyboardButton(text=text_back)
        ]
    ]

    return types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)


async def calorie_goal_keyboard(language):
    texts = {
        "ru": ["Поддержание веса", "Набор массы", "Похудение"],
        "uz": ["Vaznni saqlash", "Vazn yig'ish", "Ozish"],
        "en": ["Maintain weight", "Gain weight", "Lose weight"]
    }
    goal_map = texts.get(language, texts['ru'])
    buttons = [[types.KeyboardButton(text=text)] for text in goal_map]
    return types.ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)


async def change_language_keyboard(language):
    keyboard = [
        [
            types.KeyboardButton(text="uz🇺🇿"),
            types.KeyboardButton(text="ru🇷🇺"),
            types.KeyboardButton(text="eng🇺🇸")
        ]
    ]

    return types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)


def diary_navigation_keyboard(date):
    prev_day = (date - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    next_day = (date + datetime.timedelta(days=1)).strftime("%Y-%m-%d")

    keyboard = [
        [
            types.InlineKeyboardButton(text="◀️", callback_data=f"diary_prev_{prev_day}"),
            types.InlineKeyboardButton(text="▶️", callback_data=f"diary_next_{next_day}")
        ]
    ]

    return types.InlineKeyboardMarkup(inline_keyboard=keyboard)
