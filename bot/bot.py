import asyncio
import logging
import requests

from aiogram import types, F
from aiogram.methods import DeleteWebhook
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from datetime import datetime

from data import config
from loader import bot, dp

from utils.fetch import (
    create_meal_data,
    create_user_data,
    get_diary_data_by_date,
    get_or_create_diary,
    get_settings,
    get_user_data,
    get_language,
    update_user_goal,
    update_user_language,
    update_user_reminder,
    update_user_weight,
    get_user_stats
)

from utils.keyboards import (
    calorie_goal_keyboard,
    change_language_keyboard,
    diary_navigation_keyboard,
    language_keyboard,
    main_menu_keyboard,
    settings_menu_keyboard,
    edit_meal_keyboard
)

from utils.states import (
    MealStates,
    UserSettingsStates,
)

from utils.translation.localization import get_localized_message
from utils.utils import analyze_image_with_gpt


logging.basicConfig(level=logging.INFO)

TOKEN = config.TOKEN

TEMP_RECOGNIZED_MEALS = {}


@dp.message(Command("stat"))
async def admin_stat(message: types.Message):
    user_id = message.from_user.id
    if user_id not in [819233688]:
        return
    
    stats = await get_user_stats()
    if not stats:
        await message.answer("⚠️ Не удалось получить статистику.")
        return

    text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"🟢 Активны за 7 дней: <b>{stats['active_7_days']}</b>\n"
        f"🕒 Активны за 24 часа: <b>{stats['active_1_days']}</b>"
    )

    await message.answer(text, parse_mode="html")


@dp.message(CommandStart())
async def start_command(message: types.Message):
    user_id = message.from_user.id
    
    language = await get_language(user_id)
    user_data = await get_user_data(user_id)
    
    if user_data is not None:
        main_menu_k = await main_menu_keyboard(language)
        message_answer = await get_localized_message(language, "main_menu")
        await message.answer(message_answer, reply_markup=main_menu_k)

    else:
        language_btn = await language_keyboard()
        welcoma_message = await get_localized_message("none", "welcome")
        await message.answer(welcoma_message, reply_markup=language_btn)


@dp.callback_query(lambda c: c.data in ["uz", "ru", "en"])
async def process_language(callback: types.CallbackQuery):
    await callback.answer()

    language = callback.data
    user_id = callback.from_user.id

    user = await create_user_data(user_id, language)
    main_menu_k = await main_menu_keyboard(language)

    if user is not None:
        message_answer = await get_localized_message(language, "main_menu")
        await callback.message.answer(message_answer, reply_markup=main_menu_k)
    else:
        message_answer = await get_localized_message("none", "error")
        print(1)
        await callback.message.answer(message_answer)


@dp.message(F.photo)
async def get_meal_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    language = (await get_settings(user_id)).get("language", "ru")

    processing_photo_message = await get_localized_message(language, "processing_photo")

    msg = await message.answer(processing_photo_message)
    message_id = msg.message_id

    # Сохраняем фото
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    file_path = file_info.file_path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    local_path = f"image/{user_id}-{timestamp}.jpg"

    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
    response = requests.get(file_url)

    if response.status_code != 200:
        await bot.delete_message(chat_id=message.chat.id, message_id=message_id)
        await message.answer(await get_localized_message(language, "error"))
        await state.clear()
        return

    with open(local_path, "wb") as f:
        f.write(response.content)

    # Анализируем
    gpt_data = await analyze_image_with_gpt(language, local_path)

    if "error" in gpt_data:
        await bot.delete_message(chat_id=message.chat.id, message_id=message_id)
        await message.answer(await get_localized_message(language, "food_not_recognized"))
        await state.clear()
        return
    
    await state.update_data(meal_data=gpt_data)

    # Сохраняем в RAM (временно)
    TEMP_RECOGNIZED_MEALS[user_id] = {
        "data": gpt_data,
        "photo": local_path
    }

    food_name = gpt_data["food_name"]
    calories = gpt_data["calories"]
    protein = gpt_data["protein"]
    fat = gpt_data["fat"]
    carbs = gpt_data["carbs"]

    calorie_text = await get_localized_message(language, "calorie")
    protein_text = await get_localized_message(language, "protein")
    fat_text = await get_localized_message(language, "fat")
    carbs_text = await get_localized_message(language, "carbs")

    text = (
        f"🍽️ <b>{food_name.title()}</b>\n"
        f"🔥 {calorie_text}: {calories} kkal\n"
        f"🍗 {protein_text}: {protein} g\n"
        f"🥑 {fat_text}: {fat} g\n"
        f"🍞 {carbs_text}: {carbs} g\n\n"
        f"<i>{await get_localized_message(language, 'confirm_meal_prompt')}</i>"
    )

    text_button_1 = await get_localized_message(language, "save_button")
    text_button_2 = await get_localized_message(language, "edit_grams_button")
    text_button_3 = await get_localized_message(language, "cancel_button")

    # Кнопки
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=text_button_1, callback_data="save_meal")],
        [types.InlineKeyboardButton(text=text_button_2, callback_data="edit_grams")],
        [types.InlineKeyboardButton(text=text_button_3, callback_data="cancel_meal")]
    ])

    await bot.delete_message(chat_id=message.chat.id, message_id=message_id)

    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@dp.message(F.photo, MealStates.waiting_for_photo)
async def get_meal_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    language = (await get_settings(user_id)).get("language", "ru")

    processing_photo_message = await get_localized_message(language, "processing_photo")

    msg = await message.answer(processing_photo_message)
    message_id = msg.message_id

    # Сохраняем фото
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    file_path = file_info.file_path
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    local_path = f"image/{user_id}-{timestamp}.jpg"

    file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
    response = requests.get(file_url)

    if response.status_code != 200:
        await bot.delete_message(chat_id=message.chat.id, message_id=message_id)
        await message.answer(await get_localized_message(language, "error"))
        await state.clear()
        return

    with open(local_path, "wb") as f:
        f.write(response.content)

    # Анализируем
    gpt_data = await analyze_image_with_gpt(language, local_path)

    if "error" in gpt_data:
        await bot.delete_message(chat_id=message.chat.id, message_id=message_id)
        await message.answer(await get_localized_message(language, "food_not_recognized"))
        await state.clear()
        return

    await state.update_data(meal_data=gpt_data)

    # Сохраняем в RAM (временно)
    TEMP_RECOGNIZED_MEALS[user_id] = {
        "data": gpt_data,
        "photo": local_path
    }

    food_name = gpt_data["food_name"]
    calories = gpt_data["calories"]
    protein = gpt_data["protein"]
    fat = gpt_data["fat"]
    carbs = gpt_data["carbs"]

    calorie_text = await get_localized_message(language, "calorie")
    protein_text = await get_localized_message(language, "protein")
    fat_text = await get_localized_message(language, "fat")
    carbs_text = await get_localized_message(language, "carbs")

    text = (
        f"🍽️ <b>{food_name.title()}</b>\n"
        f"🔥 {calorie_text}: {calories} kkal\n"
        f"🍗 {protein_text}: {protein} g\n"
        f"🥑 {fat_text}: {fat} g\n"
        f"🍞 {carbs_text}: {carbs} g\n\n"
        f"<i>{await get_localized_message(language, 'confirm_meal_prompt')}</i>"
    )

    text_button_1 = await get_localized_message(language, "save_button")
    text_button_2 = await get_localized_message(language, "edit_grams_button")
    text_button_3 = await get_localized_message(language, "cancel_button")

    # Кнопки
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=text_button_1, callback_data="save_meal")],
        [types.InlineKeyboardButton(text=text_button_2, callback_data="edit_grams")],
        [types.InlineKeyboardButton(text=text_button_3, callback_data="cancel_meal")]
    ])

    await bot.delete_message(chat_id=message.chat.id, message_id=message_id)

    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


@dp.callback_query(F.data == "save_meal")
async def process_save_meal(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    await state.clear()

    user_id = callback.from_user.id
    language = await get_language(user_id)
    user_id_from_api = await get_settings(user_id)
    user_id_from_api = user_id_from_api.get("id")

    main_menu_k = await main_menu_keyboard(language)
    error_text = await get_localized_message("none", "error")

    meal_data = TEMP_RECOGNIZED_MEALS.get(user_id)
    if not meal_data:
        await callback.message.answer(error_text, reply_markup=main_menu_k)
        return

    data = meal_data.get("data")
    photo_path = meal_data.get("photo")

    diary_id = await get_or_create_diary(user_id_from_api)
    if not diary_id:
        await callback.message.answer(error_text, reply_markup=main_menu_k)
        return


    result = await create_meal_data(
        diary_id=diary_id,
        food_name=data["food_name"],
        grams=data.get("grams", 100),
        calories=data["calories"],
        protein=data["protein"],
        fat=data["fat"],
        carbs=data["carbs"],
        ai_raw_json=data,
        photo_path=photo_path
    )

    if result:
        success_text = await get_localized_message(language, "meal_saved")
        await callback.message.answer(success_text, reply_markup=main_menu_k)
        TEMP_RECOGNIZED_MEALS.pop(user_id, None)
    else:
        await callback.message.answer(error_text)


@dp.callback_query(F.data == "cancel_meal")
async def process_cancel_meal(callback: types.CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id
    language = await get_language(user_id)

    main_menu_k = await main_menu_keyboard(language)

    TEMP_RECOGNIZED_MEALS.pop(user_id, None)

    cancel_text = await get_localized_message(language, "meal_canceled")
    await callback.message.answer(cancel_text, reply_markup=main_menu_k)


@dp.callback_query(F.data == "edit_grams")
async def edit_meal_callback(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    user_id = callback.from_user.id
    language = await get_language(user_id)

    edit_keyboard = await edit_meal_keyboard(language)
    choose_message = await get_localized_message(language, "choose_message")

    await callback.message.answer(choose_message, reply_markup=edit_keyboard)


@dp.callback_query(lambda c: c.data.startswith("edit_param:"))
async def start_edit_param(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_id = callback.from_user.id
    language = await get_language(user_id)
    param = callback.data.split(":")[1]
    await state.update_data(editing_param=param)
    await state.set_state(MealStates.waiting_for_new_param_value)

    new_param_message = await get_localized_message(language, "type_new_param")

    await callback.message.answer(new_param_message)


@dp.message(MealStates.waiting_for_new_param_value)
async def handle_new_value(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    language = await get_language(user_id)

    try:
        new_value = float(message.text)
        if new_value <= 0:
            raise ValueError
    except ValueError:
        invalid_number_message = await get_localized_message(language, "invalid_number")
        await message.answer(invalid_number_message)
        return

    data = await state.get_data()
    meal_data = data.get("meal_data", {})
    editing_param = data.get("editing_param")

    meal_data[editing_param] = round(new_value, 2)
    await state.update_data(meal_data=meal_data)

    calorie_text = await get_localized_message(language, "calorie")
    protein_text = await get_localized_message(language, "protein")
    fat_text = await get_localized_message(language, "fat")
    carbs_text = await get_localized_message(language, "carbs")


    text = (
        f"{meal_data['food_name']}\n"
        f"🔥 {calorie_text}: {meal_data['calories']} kkal\n"
        f"🍗 {protein_text}: {meal_data['protein']} g\n"
        f"🥑 {fat_text}: {meal_data['fat']} g\n"
        f"🍞 {carbs_text}: {meal_data['carbs']} g"
    )

    text_button_1 = await get_localized_message(language, "save_button")
    text_button_2 = await get_localized_message(language, "edit_grams_button")
    text_button_3 = await get_localized_message(language, "cancel_button")

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=text_button_1, callback_data="save_meal")],
        [types.InlineKeyboardButton(text=text_button_2, callback_data="edit_grams")],
        [types.InlineKeyboardButton(text=text_button_3, callback_data="cancel_meal")]
    ])

    param_updated_message = await get_localized_message(language, "param_updated")
    await message.answer(param_updated_message)
    await message.answer(text, reply_markup=keyboard)


@dp.message(UserSettingsStates.choose_goal)
async def process_goal_choose(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    language = await get_language(user_id)

    user_message = message.text.strip().lower()

    goals_map = {
        "ru": {
            "похудение": "lose",
            "поддержание веса": "maintain",
            "набор массы": "gain"
        },
        "en": {
            "lose weight": "lose",
            "maintain weight": "maintain",
            "gain weight": "gain"
        },
        "uz": {
            "ozish": "lose",
            "vaznni saqlash": "maintain",
            "vazn yig'ish": "gain"
        }
    }

    lang_goals = goals_map.get(language, {})
    goal_code = lang_goals.get(user_message.lower())

    if goal_code:
        result = await update_user_goal(user_id, goal_code)

        if result == 200:
            await state.clear()
            keyboard = await settings_menu_keyboard(language)
            confirmation = await get_localized_message(language, "goal_update")
            await message.answer(confirmation, reply_markup=keyboard)

        else:
            prompt = await get_localized_message(language, "choose_goal_prompt")
            keyboard = await calorie_goal_keyboard(language)

            await message.answer(prompt, reply_markup=keyboard)

    else:
        prompt = await get_localized_message(language, "choose_goal_prompt")
        keyboard = await calorie_goal_keyboard(language)

        await message.answer(prompt, reply_markup=keyboard)


@dp.message(UserSettingsStates.change_weight)
async def process_weight_input(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    language = await get_language(user_id)
    user_message = message.text.strip().replace(",", ".")

    try:
        weight = float(user_message)
        if weight <= 0 or weight > 500:
            raise ValueError

        result = await update_user_weight(user_id, weight)

        if result == 200:
            keyboard = await settings_menu_keyboard(language)
            await state.clear()
            confirmation = await get_localized_message(language, "weight_update")
            await message.answer(confirmation, reply_markup=keyboard)

        else:
            error_text = await get_localized_message(language, "invalid_weight")
            await message.answer(error_text)

    except Exception as e:
        error_text = await get_localized_message(language, "invalid_weight")
        await message.answer(error_text)


@dp.message(UserSettingsStates.change_language)
async def change_language_process(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_message = message.text

    lang_map = {
        "uz🇺🇿": "uz",
        "ru🇷🇺": "ru",
        "eng🇺🇸": "en"
    }
    selected = lang_map.get(user_message)

    if not selected:
        current_lang = await get_language(user_id)
        err = await get_localized_message(current_lang, "invalid_language")
        await message.answer(err)
        return
    
    result = await update_user_language(user_id, selected)

    if result == 200:
        confirmation = await get_localized_message(selected, "language_update")
        keyboard = await settings_menu_keyboard(selected)
        await message.answer(confirmation, reply_markup=keyboard)
    
    else:
        error = await get_localized_message("none", "error")
        await message.answer(error)

    await state.clear()


@dp.callback_query(lambda c: c.data.startswith("diary_prev_") or c.data.startswith("diary_next_"))
async def handle_diary_navigation(callback: types.CallbackQuery):
    await callback.answer()

    user_id = callback.from_user.id
    language = await get_language(user_id)
    user_id_from_api = await get_settings(user_id)
    user_id_from_api = user_id_from_api.get("id")

    error_message = await get_localized_message("none", "error")
    main_menu_k = await main_menu_keyboard(language)

    date_str = callback.data.split("_")[-1]
    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        await callback.message.answer(error_message, reply_markup=main_menu_k)
        return

    diary_data = await get_diary_data_by_date(user_id_from_api, date.year, date.month, date.day)
    if not diary_data:
        no_data_text = await get_localized_message(language, "no_diary_data")
        await callback.message.answer(no_data_text, reply_markup=main_menu_k)
        return

    total_kcal = diary_data.get("total_calories", 0)
    total_protein = diary_data.get("total_protein", 0)
    total_fat = diary_data.get("total_fat", 0)
    total_carbs = diary_data.get("total_carbs", 0)

    calorie_text = await get_localized_message(language, "calorie")
    protein_text = await get_localized_message(language, "protein")
    fat_text = await get_localized_message(language, "fat")
    carbs_text = await get_localized_message(language, "carbs")

    diary_text = (
        f"<b>📔 {date.strftime('%d.%m.%Y')}</b>\n\n"
        f"🔥 {calorie_text}: <b>{total_kcal} kkal</b>\n"
        f"🍗 {protein_text}: <b>{total_protein} g</b>\n"
        f"🥑 {fat_text}: <b>{total_fat} g</b>\n"
        f"🍞 {carbs_text}: <b>{total_carbs} g</b>"
    )

    diary_navigation = await diary_navigation_keyboard(date)

    await callback.message.edit_text(
        diary_text,
        reply_markup=diary_navigation,
        parse_mode="html"
    )


@dp.message()
async def process_message(message: types.Message, state: FSMContext):
    user_message = message.text
    user_id = message.from_user.id

    language = await get_language(user_id)

    settings_keyboard = await settings_menu_keyboard(language)
    main_menu_k = await main_menu_keyboard(language)

    match user_message:
        case "📸 Добавить еду" | "📸 Add meal" | "📸 Ovqat qoshish":
            await state.set_state(MealStates.waiting_for_photo)
            text = await get_localized_message(language, "send_photo_meal")
            await message.answer(text)

        case "⚙️ Настройки" | "⚙️ Settings" | "⚙️ Sozlamalar":
            settings = await get_settings(user_id)
            if not settings:
                error_message = await get_localized_message("none", "error")
                await message.answer(error_message)

            # Локализация целей
            goal_map = {
                "maintain": {
                    "ru": "Поддержание веса",
                    "uz": "Vaznni saqlash",
                    "en": "Maintain weight"
                },
                "gain": {
                    "ru": "Набор массы",
                    "uz": "Vazn yig'ish",
                    "en": "Gain weight"
                },
                "lose": {
                    "ru": "Похудение",
                    "uz": "Ozish",
                    "en": "Lose weight"
                }
            }

            goal_key = settings.get("goal")
            goal_localized = goal_map.get(goal_key, {}).get(language, "-")

            weight = settings.get("weight_kg")
            weight_display = f"{weight} kg" if weight else "-"

            reminder_display = "✅ ON" if settings.get("morning_summary_enabled") else "❌ OFF"

            choose_text = await get_localized_message(language, "choose_button")

            text = (
                f"{await get_localized_message(language, 'settings_menu')}\n\n"
                f"{await get_localized_message(language, 'change_goal')}: {goal_localized}\n"
                f"{await get_localized_message(language, 'change_weight')}: {weight_display}\n"
                f"{await get_localized_message(language, 'change_language')}: {language.upper()}\n"
                f"{await get_localized_message(language, 'toggle_reminder')}: {reminder_display}\n\n"
                f"{choose_text}"
            )

            await message.answer(text, reply_markup=settings_keyboard)

        case "🎯 Цель калорий" | "🎯 Calorie goal" | "🎯 Kaloriya maqsadi":
            await state.set_state(UserSettingsStates.choose_goal)
            prompt = await get_localized_message(language, "choose_goal_prompt")
            keyboard = await calorie_goal_keyboard(language)

            await message.answer(prompt, reply_markup=keyboard)

        case "🌐 Язык" | "🌐 Language" | "🌐 Til":
            await state.set_state(UserSettingsStates.change_language)
            prompt = await get_localized_message(language, "choose_language_prompt")
            keyboard = await change_language_keyboard(language)
            await message.answer(prompt, reply_markup=keyboard)

        case "⚖️ Вес" | "⚖️ Weight" | "⚖️ Vazn":
            await state.set_state(UserSettingsStates.change_weight)
            prompt = await get_localized_message(language, "enter_weight_prompt")
            await message.answer(prompt)

        case "🔔 Вкл/выкл утреннее напоминание" | "🔔 Toggle morning reminder" | "🔔 Ertalabgi eslatmani yoqish/o‘chirish":
            settings = await get_settings(user_id)
            reminder = False if settings.get("morning_summary_enabled") else True
            result = await update_user_reminder(user_id, reminder)
            if result == 200:
                confirmation = await get_localized_message(language, "reminder_update")
                await message.answer(confirmation, reply_markup=settings_keyboard)
            
            else:
                error_text = await get_localized_message("none", "error")
                await message.answer(error_text, reply_markup=settings_keyboard)

        case "📔 Мой дневник" | "📔 My diary" | "📔 Meni kundaligim":
            user_id_from_api = await get_settings(user_id)
            user_id_from_api = user_id_from_api.get("id")

            today = datetime.now().date()
            year, month, day = today.year, today.month, today.day

            diary_data = await get_diary_data_by_date(user_id_from_api, year, month, day)

            if not diary_data:
                no_data_text = await get_localized_message(language, "no_diary_data")
                await message.answer(no_data_text, reply_markup=main_menu_k)
                return

            date_str = today.strftime("%d.%m.%Y")
            total_kcal = diary_data.get("total_calories", 0)
            total_protein = diary_data.get("total_protein", 0)
            total_fat = diary_data.get("total_fat", 0)
            total_carbs = diary_data.get("total_carbs", 0)

            calorie_text = await get_localized_message(language, "calorie")
            protein_text = await get_localized_message(language, "protein")
            fat_text = await get_localized_message(language, "fat")
            carbs_text = await get_localized_message(language, "carbs")

            diary_text = (
                f"<b>📔 {date_str}</b>\n\n"
                f"🔥 {calorie_text}: <b>{total_kcal} kkal</b>\n"
                f"🍗 {protein_text}: <b>{total_protein} g</b>\n"
                f"🥑 {fat_text}: <b>{total_fat} g</b>\n"
                f"🍞 {carbs_text}: <b>{total_carbs} g</b>"
            )

            diary_navigation = await diary_navigation_keyboard(today)

            await message.answer(
                diary_text,
                reply_markup=diary_navigation,
                parse_mode="html"
            )

        case "❓ Помощь" | "❓ Help" | "❓ Yordam":
            await message.answer("Help button")

        case "⬅️ Назад" | "⬅️ Back" | "⬅️ Ortga":
            message_answer = await get_localized_message(language, "main_menu")
            await message.answer(message_answer, reply_markup=main_menu_k)

        case _:
            default_message = await get_localized_message(language, "default_message")
            await message.answer(default_message, reply_markup=main_menu_k)


async def main():
    await bot(DeleteWebhook(drop_pending_updates=True))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.info("Start Service")
    asyncio.run(main())
    logging.info("Stop Service")
