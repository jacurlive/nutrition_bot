import aiohttp

from datetime import date
from data import config

token = config.TOKEN

API = config.API

HEADERS = {
    "Auth": token
}


async def get_user_data(telegram_id):
    url = f"{API}users/telegram/{telegram_id}"

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as response:
            response_data = None
            if response.status == 200:
                response_data = await response.json()
            
            return response_data


async def create_user_data(telegram_id: int, language: str):
    url = f"{API}users/"

    data = {
        "telegram_id": telegram_id,
        "language": language
    }

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.post(url=url, data=data) as response:
            response_code = response.status
            if response_code == 201 or response_code == 200:
                data = await response.json()
                return data
            return None


async def get_language(telegram_id: int):
    url = f"{API}users/telegram/{telegram_id}"

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url=url) as response:
            response_code = response.status
            if response_code == 200:
                data = await response.json()
                language = data['language']
                return language
            return None            


async def create_meal_data(diary_id, food_name: str, grams, calories, photo_path: str, protein, fat, carbs, ai_raw_json):
    url = f"{API}meal/"

    data = {
        "food_name": food_name,
        "grams": grams,
        "calories": calories,
        "protein": protein,
        "fat": fat,
        "carbs": carbs,
        "image_url": photo_path,
        "ai_raw_json": ai_raw_json,
        "diary": diary_id
    }

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.post(url=url, data=data) as response:
            response_code = response.status
            if response_code == 201 or response_code == 200:
                data = await response.json()
                return data
            return None


async def get_settings(telegram_id):
    url = f"{API}users/telegram/{telegram_id}"

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url=url) as response:
            if response.status == 200:
                response_data = await response.json()
                return response_data
            return None


async def update_user_goal(telegram_id, goal_code):
    url = f"{API}users/telegram/{telegram_id}"

    data = {
        "goal": goal_code
    }

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.patch(url=url, data=data) as response:
            response_code = response.status
            return response_code
        
    
async def update_user_weight(telegram_id, weight):
    url = f"{API}users/telegram/{telegram_id}"

    data = {
        "weight_kg": weight
    }

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.patch(url=url, data=data) as response:
            response_code = response.status
            return response_code
        

async def update_user_language(telegram_id, language):
    url = f"{API}users/telegram/{telegram_id}"

    data = {
        "language": language
    }

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.patch(url=url, data=data) as response:
            response_code = response.status
            return response_code
        

async def update_user_reminder(telegram_id, reminder):
    url = f"{API}users/telegram/{telegram_id}"

    data = {
        "morning_summary_enabled": reminder
    }

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.patch(url=url, data=data) as response:
            response_code = response.status
            return response_code


async def get_diary_data_by_date(user_id, year, month, day):
    url = f"{API}diary/date/{user_id}/{year}/{month}/{day}"

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url=url) as response:
            if response.status == 200:
                data = await response.json()
                if isinstance(data, list) and data:
                    return data[0]
                else:
                    return None
            return None
        

async def get_or_create_diary(user_id):
    today = date.today()
    url = f"{API}diary/date/{user_id}/{today.year}/{today.month}/{today.day}"

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data:
                    return data[0]["id"]


        payload = {
            "user": user_id,
            "date": str(today)
        }
        async with session.post(f"{API}diary/", json=payload) as create_response:
            if create_response.status == 201:
                created = await create_response.json()
                return created["id"]
            else:
                return None
            

async def get_user_stats():
    url = f"{API}stats/"

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url=url) as response:
            if response.status == 200:
                response_data = await response.json()
                return response_data
            return None
