import asyncio
import aiohttp

from datetime import datetime, timedelta

from loader import bot
from utils.keyboards import main_menu_keyboard
from utils.translation.localization import get_localized_message

from data import config


token = config.TOKEN

API = config.API

HEADERS = {
    "Auth": token
}


async def send_morning_summary_to_all_users():
    yesterday = datetime.now().date() - timedelta(days=1)
    year, month, day = yesterday.year, yesterday.month, yesterday.day

    url = f"{API}users/reminder"


    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url=url) as response:
            if response.status != 200:
                print("❌ Не удалось получить список пользователей")
                return
            
            users = await response.json()

        for user in users:
            user_id = user["id"]
            telegram_id = user["telegram_id"]
            language = user.get("language", "ru")

            url_diary = f"{API}diary/date/{user_id}/{year}/{month}/{day}"

            async with session.get(url=url_diary) as resp:
                if resp.status != 200:
                    continue

                diaries = await resp.json()
                if not diaries:
                    continue

                diary = diaries[0]

            calorie_text = await get_localized_message(language, "calorie")
            protein_text = await get_localized_message(language, "protein")
            fat_text = await get_localized_message(language, "fat")
            carbs_text = await get_localized_message(language, "carbs")
            summary_text = await get_localized_message(language, "summary_text")

            total_kcal = diary.get("total_calories", 0)
            total_protein = diary.get("total_protein", 0)
            total_fat = diary.get("total_fat", 0)
            total_carbs = diary.get("total_carbs", 0)

            diary_text = (
                f"<b>{summary_text}</b>\n\n"
                f"🔥 {calorie_text}: <b>{total_kcal} kkal</b>\n"
                f"🍗 {protein_text}: <b>{total_protein} g</b>\n"
                f"🥑 {fat_text}: <b>{total_fat} g</b>\n"
                f"🍞 {carbs_text}: <b>{total_carbs} g</b>"
            )

            keyboard = await main_menu_keyboard(language)

            try:
                await bot.send_message(chat_id=telegram_id, text=diary_text, reply_markup=keyboard, parse_mode="html")
                print(f"✅ Сводка отправлена {telegram_id}")
            except Exception as e:
                print(f"❌ Ошибка отправки {telegram_id}: {e}")

if __name__ == "__main__":
    asyncio.run(send_morning_summary_to_all_users())
