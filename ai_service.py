"""AI Service for nutrition analysis"""

import json
import logging
import requests
import tempfile
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
from config import get_settings
from database import NutritionRepository, CustomFood

logger = logging.getLogger(__name__)


@dataclass
class NutritionItem:
    """Single food item with nutrition data"""
    name: str
    grams: int
    calories: int
    protein: float
    fat: float
    carbs: float


@dataclass
class NutritionAnalysis:
    """Complete analysis result"""
    items: List[NutritionItem]
    total_calories: float
    total_protein: float
    total_fat: float
    total_carbs: float
    notes: Optional[str] = None
    error: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NutritionAnalysis":
        """Create from API response dict"""
        logger.info(f"from_dict input type: {type(data)}, data: {repr(data)[:200]}")
        
        if not isinstance(data, dict):
            logger.error(f"Expected dict, got {type(data)}: {repr(data)}")
            return cls(
                items=[], total_calories=0, total_protein=0, 
                total_fat=0, total_carbs=0,
                error=f"Invalid response format: expected dict, got {type(data).__name__}"
            )
        
        items = [
            NutritionItem(
                name=item.get("name", "Unknown"),
                grams=item.get("grams", 0),
                calories=item.get("calories", 0),
                protein=item.get("protein", 0),
                fat=item.get("fat", 0),
                carbs=item.get("carbs", 0)
            )
            for item in data.get("items", [])
        ]
        
        total = data.get("total", {})
        
        return cls(
            items=items,
            total_calories=total.get("calories", 0),
            total_protein=total.get("protein", 0),
            total_fat=total.get("fat", 0),
            total_carbs=total.get("carbs", 0),
            notes=data.get("notes"),
            error=data.get("error")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for database storage"""
        return {
            "items": [
                {
                    "name": item.name,
                    "grams": item.grams,
                    "calories": item.calories,
                    "protein": item.protein,
                    "fat": item.fat,
                    "carbs": item.carbs
                }
                for item in self.items
            ],
            "total": {
                "calories": self.total_calories,
                "protein": self.total_protein,
                "fat": self.total_fat,
                "carbs": self.total_carbs
            },
            "notes": self.notes
        }


class NutritionAIService:
    """Service for AI-powered nutrition analysis"""
    
    SYSTEM_PROMPT = (
        "Ты — эксперт по питанию. Проанализируй что съел пользователь "
        "и рассчитай калории и КБЖУ (белки, жиры, углеводы). "
        "Если не уверен в весе — делай разумные предположения."
    )
    
    USER_PROMPT_TEMPLATE = """Проанализируй питание и верни СТРОГО JSON:

{{
  "items": [
    {{"name": "название", "grams": 100, "calories": 150, "protein": 10, "fat": 5, "carbs": 20}}
  ],
  "total": {{"calories": 150, "protein": 10, "fat": 5, "carbs": 20}},
  "notes": "опциональный комментарий"
}}

Ввод: {input}"""
    
    INTENT_PROMPT = """Ты — интеллектуальный ассистент для трекера питания. Определи намерение пользователя.

ВАЖНО: Учитывай контекст предыдущих сообщений. Если пользователь говорит что-то вроде "исправь", "измени это", "поменяй", "сделай 150" — он часто ссылается на предыдущее сообщение.

Возможные действия (action):
- "add_food" — пользователь описывает что он ел (например: "я съел банан", "кофе с круассаном")
- "show_summary" — пользователь хочет увидеть статистику (например: "покажи итоги", "сколько я съел", "моя статистика")
- "show_foods" — пользователь хочет увидеть свои сохраненные продукты (например: "покажи мои продукты", "мои сохраненные продукты", "что у меня в списке", "моя библиотека еды")
- "show_settings" — пользователь хочет увидеть свои настройки (например: "покажи мои настройки", "мои настройки", "какие у меня настройки", "что у меня в настройках", "покажи цели")
- "change_language" — пользователь хочет сменить язык (например: "поменяй язык на английский", "смени язык", "язык английский", "переключись на русский", "english language")
- "edit_food" — пользователь хочет изменить сохраненный продукт (например: "измени овсянку на 160 калорий", "поменяй в банане калории на 90", "обнови белки в яйце до 7", "отредактируй мой продукт овсянка", "исправь на 150", "сделай калории 200")
- "delete_last" — пользователь хочет удалить последнюю запись (например: "удали последнее", "отмени запись")
- "help" — пользователь просит помощь

Верни СТРОГО JSON:
{{
  "action": "add_food|show_summary|show_foods|show_settings|change_language|edit_food|delete_last|help",
  "date": "today|yesterday|week" (для show_summary, по умолчанию today),
  "food_description": "описание еды если action=add_food, иначе пусто",
  "language_params": {{
    "language": "язык для установки: ru|en (извлеки из фразы)"
  }} (только для change_language),
  "edit_params": {{
    "food_name": "название продукта для редактирования (извлеки из контекста если не указано явно)",
    "field": "поле для изменения: calories|protein|fat|carbs|grams|name|aliases (извлеки из контекста если не указано)",
    "value": "новое значение (извлеки из текущего сообщения)"
  }} (только для edit_food)
}}

КОНТЕКСТ ПРЕДЫДУЩИХ СООБЩЕНИЙ:
{context}

ТЕКУЩЕЕ СООБЩЕНИЕ: {input}"""

    def __init__(self):
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.settings.openai_api_key}",
            "Content-Type": "application/json"
        })
        # Conversation memory: user_id -> list of recent messages
        self._conversation_memory: Dict[int, List[Dict[str, Any]]] = {}
        self._max_memory_size = 10  # Keep last 10 messages
    
    def _add_to_memory(self, user_id: int, role: str, content: str, extra: Dict = None):
        """Add message to conversation memory"""
        if user_id not in self._conversation_memory:
            self._conversation_memory[user_id] = []
        
        entry = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        if extra:
            entry.update(extra)
        
        self._conversation_memory[user_id].append(entry)
        
        # Trim to max size
        if len(self._conversation_memory[user_id]) > self._max_memory_size:
            self._conversation_memory[user_id] = self._conversation_memory[user_id][-self._max_memory_size:]
    
    def _get_memory_context(self, user_id: int, limit: int = 5) -> str:
        """Get recent conversation context as formatted string"""
        if user_id not in self._conversation_memory:
            return "(нет предыдущих сообщений)"
        
        messages = self._conversation_memory[user_id][-limit:]
        context_lines = []
        
        for msg in messages:
            role = "Пользователь" if msg["role"] == "user" else "Бот"
            content = msg["content"][:100]  # Truncate long messages
            context_lines.append(f"{role}: {content}")
        
        return "\n".join(context_lines) if context_lines else "(нет предыдущих сообщений)"
    
    def detect_intent(self, text: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Detect user intent from natural language with context"""
        try:
            # Get context from memory
            context = self._get_memory_context(user_id) if user_id else "(нет контекста)"
            
            response = self.session.post(
                f"{self.settings.openai_base_url}/chat/completions",
                json={
                    "model": "gpt-4.1-mini",
                    "messages": [
                        {"role": "user", "content": self.INTENT_PROMPT.format(context=context, input=text)}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 300
                },
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            content = self._extract_json(content)
            
            intent = json.loads(content)
            
            # Store user message in memory
            if user_id:
                self._add_to_memory(user_id, "user", text, {"intent": intent.get("action")})
            
            return intent
        except Exception as e:
            logger.error(f"Intent detection error: {e}")
            # Fallback: assume it's food
            return {"action": "add_food", "food_description": text}
    
    def add_bot_response_to_memory(self, user_id: int, response: str, extra: Dict = None):
        """Add bot response to conversation memory"""
        self._add_to_memory(user_id, "bot", response, extra)
    
    def analyze(self, text: str, repo: Optional[NutritionRepository] = None, user_id: Optional[int] = None) -> NutritionAnalysis:
        """Analyze food description and return nutrition data.
        If repo and user_id provided, checks for custom foods first."""
        
        # Try to find custom foods first
        custom_items = []
        if repo and user_id:
            custom_items = self._check_custom_foods(text, repo, user_id)
            if custom_items:
                logger.info(f"Found {len(custom_items)} custom foods for '{text}'")
                # Calculate totals from custom items
                totals = {
                    "calories": sum(item.calories for item in custom_items),
                    "protein": sum(item.protein for item in custom_items),
                    "fat": sum(item.fat for item in custom_items),
                    "carbs": sum(item.carbs for item in custom_items)
                }
                return NutritionAnalysis(
                    items=custom_items,
                    total_calories=totals["calories"],
                    total_protein=totals["protein"],
                    total_fat=totals["fat"],
                    total_carbs=totals["carbs"],
                    notes="Из сохранённых продуктов ✓"
                )
        
        # Fall back to AI analysis
        try:
            response = self.session.post(
                f"{self.settings.openai_base_url}/chat/completions",
                json={
                    "model": "gpt-4.1",
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": self.USER_PROMPT_TEMPLATE.format(input=text)}
                    ],
                    "temperature": self.settings.temperature,
                    "max_tokens": self.settings.max_tokens
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            logger.info(f"=== Raw LLM response ===")
            logger.info(repr(content))
            
            # Extract JSON from markdown if present
            content = self._extract_json(content)
            logger.info(f"=== After extract ===")
            logger.info(repr(content))
            
            # Try to fix common issues
            content = content.strip()
            if content.startswith('"items"'):
                # Fix: Kimi sometimes returns just the items array
                content = '{"items":' + content[7:]
                logger.info(f"=== Fixed content ===")
                logger.info(repr(content))
            
            # Parse JSON
            try:
                data = json.loads(content)
            except json.JSONDecodeError as je:
                logger.error(f"JSON parse error: {je}")
                logger.error(f"Content was: {repr(content)}")
                # Return fallback
                return NutritionAnalysis(
                    items=[NutritionItem(name=text[:50], grams=0, calories=0, protein=0, fat=0, carbs=0)],
                    total_calories=0, total_protein=0, total_fat=0, total_carbs=0,
                    error=f"JSON parse error: {je}. Raw: {content[:200]}"
                )
            
            return NutritionAnalysis.from_dict(data)
            
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return NutritionAnalysis(
                items=[], total_calories=0, total_protein=0, 
                total_fat=0, total_carbs=0,
                error=f"API error: {str(e)}"
            )
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse failed: {e}")
            return NutritionAnalysis(
                items=[], total_calories=0, total_protein=0,
                total_fat=0, total_carbs=0,
                error="Failed to parse nutrition data"
            )
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return NutritionAnalysis(
                items=[], total_calories=0, total_protein=0,
                total_fat=0, total_carbs=0,
                error=f"Error: {str(e)}"
            )
    
    def _encode_image(self, image_path: Path) -> tuple[str, str]:
        """Encode image to base64 and determine mime type"""
        import base64
        
        with open(image_path, "rb") as img_file:
            image_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        mime_type = "image/jpeg"
        if image_path.suffix.lower() == '.png':
            mime_type = "image/png"
        elif image_path.suffix.lower() == '.webp':
            mime_type = "image/webp"
        
        return image_data, mime_type
    
    def analyze_food_photo(self, image_path: Path) -> NutritionAnalysis:
        """Analyze food photo using GPT-4 Vision and estimate nutrition"""
        try:
            image_data, mime_type = self._encode_image(image_path)
            
            response = self.session.post(
                f"{self.settings.openai_base_url}/chat/completions",
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """Проанализируй фото еды. Определи:
1. Что изображено на фото (название блюда/продуктов)
2. Примерный вес порции в граммах
3. Калории
4. Белки (г)
5. Жиры (г)
6. Углеводы (г)

Делай разумные предположения о размере порции и составе.

Верни СТРОГО JSON:
{
  "items": [
    {"name": "название блюда", "grams": 250, "calories": 400, "protein": 25, "fat": 15, "carbs": 45}
  ],
  "total": {"calories": 400, "protein": 25, "fat": 15, "carbs": 45},
  "notes": "комментарий о составе блюда"
}"""
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{image_data}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 500
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            content = self._extract_json(content)
            
            data = json.loads(content)
            return NutritionAnalysis.from_dict(data)
            
        except Exception as e:
            logger.error(f"Vision food analysis error: {e}")
            return NutritionAnalysis(
                items=[], total_calories=0, total_protein=0,
                total_fat=0, total_carbs=0,
                error=f"Error analyzing food photo: {e}"
            )
    
    def analyze_nutrition_label(self, image_path: Path) -> Dict[str, Any]:
        """Analyze nutrition label image using GPT-4 Vision and extract nutrition data"""
        try:
            image_data, mime_type = self._encode_image(image_path)
            
            response = self.session.post(
                f"{self.settings.openai_base_url}/chat/completions",
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """Проанализируй этикетку Nutrition Facts. Извлеки:
1. Название продукта (если видно)
2. Размер порции в граммах
3. Калории на порцию
4. Белки (г)
5. Жиры (г)
6. Углеводы (г)

Если на этикетке указано "на 100г" — используй эти значения и укажи grams=100.
Если указан другой размер порции — используй его.

Верни СТРОГО JSON:
{
  "name": "название продукта",
  "grams": 100,
  "calories": 250,
  "protein": 10,
  "fat": 5,
  "carbs": 30,
  "notes": "дополнительная информация если есть"
}"""
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{image_data}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 500
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            content = self._extract_json(content)
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Vision API error: {e}")
            return {"error": str(e)}
    
    def _extract_json(self, content: str) -> str:
        """Extract JSON from markdown code blocks if present"""
        content = content.strip()
        
        if "```json" in content:
            return content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            return content.split("```")[1].split("```")[0].strip()
        
        return content
    
    def _check_custom_foods(self, text: str, repo: NutritionRepository, user_id: int) -> List[NutritionItem]:
        """Check if text contains any custom foods and return them"""
        custom_foods = repo.get_custom_foods(user_id)
        if not custom_foods:
            return []
        
        found_items = []
        text_lower = text.lower()
        
        for food in custom_foods:
            # Check main name
            if food.name in text_lower:
                # Check if quantity specified (e.g., "2 банана", "3 яйца")
                import re
                # Look for number before food name
                pattern = rf'(\d+)\s*{re.escape(food.name)}'
                match = re.search(pattern, text_lower)
                
                multiplier = 1
                if match:
                    quantity = int(match.group(1))
                    # Calculate multiplier based on quantity (assuming saved food is for 1 serving)
                    multiplier = quantity
                
                found_items.append(NutritionItem(
                    name=f"{food.name} ({food.grams}г × {multiplier})",
                    grams=food.grams * multiplier,
                    calories=int(food.calories * multiplier),
                    protein=round(food.protein * multiplier, 1),
                    fat=round(food.fat * multiplier, 1),
                    carbs=round(food.carbs * multiplier, 1)
                ))
            else:
                # Check aliases
                aliases = [a.strip() for a in food.aliases.split(',') if a.strip()]
                for alias in aliases:
                    if alias in text_lower:
                        import re
                        pattern = rf'(\d+)\s*{re.escape(alias)}'
                        match = re.search(pattern, text_lower)
                        
                        multiplier = 1
                        if match:
                            quantity = int(match.group(1))
                            multiplier = quantity
                        
                        found_items.append(NutritionItem(
                            name=f"{food.name} ({food.grams}г × {multiplier})",
                            grams=food.grams * multiplier,
                            calories=int(food.calories * multiplier),
                            protein=round(food.protein * multiplier, 1),
                            fat=round(food.fat * multiplier, 1),
                            carbs=round(food.carbs * multiplier, 1)
                        ))
                        break  # Found via alias, don't check other aliases
        
        return found_items
    
    def transcribe_audio(self, audio_path: Path, language: str = "ru") -> str:
        """Transcribe audio file using GROQ Whisper API (free tier)"""
        return self._transcribe_with_groq(audio_path, language)
    
    def _transcribe_with_groq(self, audio_path: Path, language: str = "ru") -> str:
        """Transcribe using GROQ free Whisper API"""
        try:
            # GROQ API key - бесплатный tier с лимитами
            groq_key = self.settings.groq_api_key
            if not groq_key:
                # Fallback к OpenAI если GROQ не настроен
                return self._transcribe_with_openai(audio_path, language)
            
            with open(audio_path, 'rb') as audio_file:
                response = requests.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {groq_key}"},
                    files={"file": (audio_path.name, audio_file, "audio/ogg")},
                    data={
                        "model": "whisper-large-v3",
                        "language": language,
                        "response_format": "text"
                    },
                    timeout=60
                )
                response.raise_for_status()
                return response.text.strip()
                
        except Exception as e:
            logger.error(f"GROQ transcription error: {e}")
            # Fallback к OpenAI
            return self._transcribe_with_openai(audio_path, language)
    
    def _transcribe_with_openai(self, audio_path: Path, language: str = "ru") -> str:
        """Fallback: transcribe using OpenAI API"""
        try:
            openai_key = self.settings.openai_api_key
            if not openai_key:
                return "[Для голосовых сообщений нужен GROQ_API_KEY или OPENAI_API_KEY]"
            
            with open(audio_path, 'rb') as audio_file:
                response = requests.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {openai_key}"},
                    files={"file": (audio_path.name, audio_file, "audio/ogg")},
                    data={
                        "model": "whisper-1",
                        "language": language,
                        "response_format": "text"
                    },
                    timeout=60
                )
                response.raise_for_status()
                return response.text.strip()
                
        except Exception as e:
            logger.error(f"OpenAI transcription error: {e}")
            return f"[Ошибка распознавания голоса: {str(e)}]"
