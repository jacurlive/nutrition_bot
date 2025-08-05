import openai
import base64
import json
from pathlib import Path
from data import config

openai.api_key = config.GPT_TOKEN


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


async def analyze_image_with_gpt(language, photo_path):
    PROMPT_TEMPLATES = {
    "ru": """
Ты — профессиональный нутрициолог и эксперт по визуальной оценке продуктов. По фотографии ты должен определить, что на ней изображено: блюдо, напиток, десерт или перекус.

Твоя задача — распознать продукт и приблизительно оценить его пищевую ценность. Даже если изображение нечеткое или еда частично скрыта, ты обязан сделать **лучшую возможную оценку**.

Ответ возвращай строго в виде **JSON**, без комментариев, пояснений или оформления. Формат:

{
  "food_name": "название блюда на русском",
  "calories": примерное число,     // ккал
  "protein": примерное число,      // граммы
  "fat": примерное число,          // граммы
  "carbs": примерное число         // граммы
}

Если определить еду невозможно, верни:
{ "error": "Невозможно распознать еду на изображении." }

⚠️ Правила:
- Используй **только русский язык**
- Верни **только JSON** — без текста, смайликов или форматирования
- Обрабатывай любые продукты: основное блюдо, напитки, десерты, снеки
- Делай **лучший возможный анализ** даже при низком качестве фото
""",
    "en": """
You are a professional nutritionist and visual food recognition expert. Your task is to identify the item in the photo — it can be a dish, drink, dessert, or snack — and estimate its nutritional content.

Even if the image is unclear or only partially shows the food, provide the **best possible estimate**.

Return your answer strictly as **JSON**, with no extra text, formatting, or comments. Use this format:

{
  "food_name": "name of the item in English",
  "calories": estimated number,
  "protein": estimated number,
  "fat": estimated number,
  "carbs": estimated number
}

If the food cannot be identified, return:
{ "error": "Unable to recognize the food in the image." }

⚠️ Rules:
- Answer in **English only**
- Return **only JSON**
- Recognize any kind of item: dish, drink, dessert, snack
- Estimate even when visibility is poor
""",
    "uz": """
Siz professional ovqatshunos va tasvir asosida ovqatni aniqlovchi mutaxassissiz. Rasmda ovqat, ichimlik, shirinlik yoki yengil tamaddi bo‘lishi mumkin — buni aniqlang va taxminiy ozuqaviy qiymatini baholang.

Agar rasm noaniq bo‘lsa yoki mahsulot to‘liq ko‘rinmasa ham, **eng yaxshi taxminingizni** kiriting.

Javobingizni faqat quyidagi **JSON** formatida bering, hech qanday qo‘shimcha matn, izoh yoki emoji bo‘lmasin:

{
  "food_name": "O‘zbek tilida nomi",
  "calories": taxminiy son,
  "protein": taxminiy son,
  "fat": taxminiy son,
  "carbs": taxminiy son
}

Agar ovqatni aniqlab bo‘lmasa, javob shunday bo‘lsin:
{ "error": "Ovqatni rasmdan aniqlab bo‘lmadi." }

⚠️ Qoidalar:
- Faqat **o‘zbek tilida** javob bering
- Faqat **JSON** qaytaring
- Har qanday mahsulotni aniqlang: taom, ichimlik, shirinlik, yengil ovqat
- Tasvir sifati past bo‘lsa ham — **eng yaxshi tahlilni** kiriting
"""
}

    def clean_json_block(text: str) -> str:
        if text.startswith("```") and text.endswith("```"):
            return "\n".join(text.strip().split("\n")[1:-1]).strip()
        return text.strip()

    if language not in PROMPT_TEMPLATES:
        language = "ru"

    if not Path(photo_path).exists():
        return { "error": f"Файл {photo_path} не найден." }

    try:
        base64_image = encode_image(photo_path)

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        { "type": "text", "text": PROMPT_TEMPLATES[language] },
                        { "type": "image_url", "image_url": { "url": f"data:image/jpeg;base64,{base64_image}" } }
                    ]
                }
            ],
            max_tokens=1000
        )

        raw_content = clean_json_block(response.choices[0].message.content)
        return json.loads(raw_content)

    except json.JSONDecodeError:
        return { "error": "Ответ не является допустимым JSON." }

    except Exception as e:
        return { "error": str(e) }