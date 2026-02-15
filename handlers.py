"""Telegram bot handlers"""

import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import NutritionRepository, DailySummary
from ai_service import NutritionAIService, NutritionAnalysis
from i18n import get_text

logger = logging.getLogger(__name__)


class BotHandlers:
    """Telegram bot message handlers"""
    
    def __init__(self, repository: NutritionRepository, ai_service: NutritionAIService):
        self.repo = repository
        self.ai = ai_service
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        welcome_text = (
            "🥗 *Nutrition Tracker Bot*\n\n"
            "Привет! Я — умный трекер питания с AI.\n\n"
            "*Что я умею:*\n"
            "• 🍎 Считаю КБЖУ по описанию еды\n"
            "• 🎙️ Понимаю голосовые сообщения\n"
            "• 📸 *Распознаю еду на фото!* Сфотографируй тарелку — я посчитаю КБЖУ\n"
            "• 📸 *Распознаю этикетки* Nutrition Facts\n"
            "• 🧠 Понимаю естественный язык:\n"
            "  – «Покажи итоги за вчера»\n"
            "  – «Я съел два яйца и банан»\n"
            "  – «Удали последнюю запись»\n"
            "• 📊 Веду статистику по дням\n"
            "• 💾 Сохраняю часто едимые продукты\n\n"
            "*Просто сфотографируй еду* 📸\n"
            "Или сохрани продукт:\n"
            "`/savefood Название | гр | ккал | б | ж | у`\n\n"
            "Просто напиши или скажи что ты ел! 🍽️"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Сегодня", callback_data="today"),
                InlineKeyboardButton("📈 Вчера", callback_data="yesterday")
            ],
            [InlineKeyboardButton("🗑️ Удалить последнее", callback_data="delete")]
        ]
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    async def today(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /today command"""
        user_id = self._get_user_id(update)
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        summary = self.repo.get_daily_summary(user_id, today_str)
        entries = self.repo.get_day_entries(user_id, today_str)
        
        text = self._format_daily_report("Сегодня", summary, entries)
        keyboard = [[InlineKeyboardButton("🗑️ Удалить последнее", callback_data="delete")]]
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    async def yesterday(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /yesterday command"""
        user_id = self._get_user_id(update)
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        
        summary = self.repo.get_daily_summary(user_id, yesterday_str)
        
        text = (
            f"📈 *Итоги за вчера ({yesterday.strftime('%d.%m')})*\n\n"
            f"🔥 Калории: *{summary.calories}* ккал\n"
            f"🥩 Белки: *{summary.protein}* г\n"
            f"🥑 Жиры: *{summary.fat}* г\n"
            f"🍞 Углеводы: *{summary.carbs}* г\n\n"
            f"📝 Записей: {summary.entries_count}"
        )
        
        await update.message.reply_text(text, parse_mode="Markdown")
    
    async def savefood(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /savefood command to save custom food
        Usage: /savefood Название | псевдонимы | граммы | калории | белки | жиры | углеводы
        Example: /savefood Овсянка | каша,овес | 100 | 150 | 5 | 3 | 25
        """
        user_id = self._get_user_id(update)
        
        if not context.args:
            await update.message.reply_text(
                "📝 *Сохранение продукта*\n\n"
                "Формат:\n"
                "`/savefood Название | псевдонимы | гр | ккал | б | ж | у`\n\n"
                "Пример:\n"
                "`/savefood Овсянка | каша,овес | 100 | 150 | 5 | 3 | 25`\n\n"
                "Псевдонимы — через запятую (необязательно)",
                parse_mode="Markdown"
            )
            return
        
        # Parse arguments
        args_text = ' '.join(context.args)
        parts = [p.strip() for p in args_text.split('|')]
        
        if len(parts) < 6:
            await update.message.reply_text(
                "❌ Неверный формат. Нужно 6-7 значений через |\n"
                "`/savefood Название | псевдонимы | гр | ккал | б | ж | у`",
                parse_mode="Markdown"
            )
            return
        
        try:
            name = parts[0]
            aliases = parts[1] if len(parts) == 7 else ""
            grams = int(parts[2] if len(parts) == 7 else parts[1])
            calories = float(parts[3] if len(parts) == 7 else parts[2])
            protein = float(parts[4] if len(parts) == 7 else parts[3])
            fat = float(parts[5] if len(parts) == 7 else parts[4])
            carbs = float(parts[6] if len(parts) == 7 else parts[5])
            
            food_id = self.repo.save_custom_food(
                user_id=user_id,
                name=name,
                aliases=aliases,
                grams=grams,
                calories=calories,
                protein=protein,
                fat=fat,
                carbs=carbs
            )
            
            aliases_text = f"\n📌 Псевдонимы: {aliases}" if aliases else ""
            
            await update.message.reply_text(
                f"✅ *Сохранено!*\n\n"
                f"🍎 *{name}* ({grams}г)\n"
                f"🔥 {calories} ккал | "
                f"🥩 {protein}г | "
                f"🥑 {fat}г | "
                f"🍞 {carbs}г"
                f"{aliases_text}\n\n"
                f"Теперь можно просто написать «съел {name}»",
                parse_mode="Markdown"
            )
            
        except ValueError as e:
            await update.message.reply_text(
                f"❌ Ошибка в числах: {e}\n"
                "Убедись, что граммы — целое число, а КБЖУ — дробные или целые.",
                parse_mode="Markdown"
            )
    
    async def myfoods(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /myfoods command to list saved custom foods"""
        user_id = self._get_user_id(update)
        foods = self.repo.get_custom_foods(user_id)
        
        if not foods:
            await update.message.reply_text(
                "📝 *У тебя пока нет сохранённых продуктов*\n\n"
                "Добавь командой:\n"
                "`/savefood Название | псевдонимы | гр | ккал | б | ж | у`",
                parse_mode="Markdown"
            )
            return
        
        text = f"🍎 *Твои сохранённые продукты* ({len(foods)}):\n\n"
        
        for i, food in enumerate(foods, 1):
            aliases_text = f" (aka: {food.aliases})" if food.aliases else ""
            text += (
                f"{i}. *{food.name}*{aliases_text}\n"
                f"   {food.grams}г = 🔥{food.calories} | "
                f"🥩{food.protein} | 🥑{food.fat} | 🍞{food.carbs}\n\n"
            )
        
        text += "\n💡 Просто напиши «съел Название» — я найду в этом списке!"
        
        await update.message.reply_text(text, parse_mode="Markdown")
    
    async def deletefood(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /deletefood command to delete custom food by name or ID"""
        user_id = self._get_user_id(update)
        
        if not context.args:
            foods = self.repo.get_custom_foods(user_id)
            if not foods:
                await update.message.reply_text("У тебя нет сохранённых продуктов.")
                return
            
            text = "🗑️ *Удалить продукт*\n\nНапиши:\n`/deletefood Название`\n\nИли по номеру:\n`/deletefood 1`\n\nТвои продукты:\n"
            for i, food in enumerate(foods, 1):
                text += f"{i}. {food.name}\n"
            
            await update.message.reply_text(text, parse_mode="Markdown")
            return
        
        query = ' '.join(context.args).strip()
        foods = self.repo.get_custom_foods(user_id)
        
        # Try to find by number first
        try:
            num = int(query)
            if 1 <= num <= len(foods):
                food_to_delete = foods[num - 1]
                if self.repo.delete_custom_food(user_id, food_to_delete.id):
                    await update.message.reply_text(
                        f"🗑️ Удалено: *{food_to_delete.name}*",
                        parse_mode="Markdown"
                    )
                    return
        except ValueError:
            pass
        
        # Find by name
        for food in foods:
            if food.name.lower() == query.lower() or query.lower() in food.aliases.lower():
                if self.repo.delete_custom_food(user_id, food.id):
                    await update.message.reply_text(
                        f"🗑️ Удалено: *{food.name}*",
                        parse_mode="Markdown"
                    )
                    return
        
        await update.message.reply_text(
            f"❌ Продукт «{query}» не найден.\n"
            f"Проверь список: /myfoods",
            parse_mode="Markdown"
        )

    async def settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /settings command to show and modify user settings"""
        user_id = self._get_user_id(update)
        settings = self.repo.get_user_settings(user_id)
        lang = settings.get('language', 'ru')
        
        # Parse arguments if provided
        if context.args:
            args_text = ' '.join(context.args)
            
            # Check for language change: /settings lang en
            if args_text.startswith('lang ') or args_text.startswith('language '):
                new_lang = args_text.split()[-1].lower()
                if new_lang in ['ru', 'en']:
                    self.repo.update_user_settings(user_id, language=new_lang)
                    lang_names = {'ru': 'Русский', 'en': 'English'}
                    await update.message.reply_text(get_text('language_changed', new_lang, language=lang_names.get(new_lang, new_lang)))
                    return
            
            # Check for timezone change: /settings timezone Europe/Moscow
            if args_text.startswith('timezone '):
                tz = args_text.replace('timezone ', '').strip()
                self.repo.update_user_settings(user_id, timezone=tz)
                await update.message.reply_text(get_text('timezone_changed', lang, timezone=tz))
                return
            
            # Check for day_end change: /settings day_end 4
            if args_text.startswith('day_end '):
                try:
                    hour = int(args_text.split()[-1])
                    if 0 <= hour <= 23:
                        self.repo.update_user_settings(user_id, day_end_hour=hour)
                        await update.message.reply_text(get_text('day_end_changed', lang, hour=hour))
                        return
                except ValueError:
                    pass
            
            # Check for goal changes: /settings goal calories 2500
            if args_text.startswith('goal '):
                parts = args_text.split()
                if len(parts) >= 3:
                    field = parts[1]
                    value = parts[2]
                    field_map = {
                        'calories': 'goal_calories',
                        'protein': 'goal_protein',
                        'fat': 'goal_fat',
                        'carbs': 'goal_carbs'
                    }
                    if field in field_map:
                        try:
                            num_value = float(value)
                            self.repo.update_user_settings(user_id, **{field_map[field]: num_value})
                            await update.message.reply_text(get_text('goal_changed', lang, field=field, value=num_value))
                            return
                        except ValueError:
                            pass
        
        # Show current settings
        text = (
            f"⚙️ *{get_text('settings_title', lang)}*\n\n"
            f"🌐 {get_text('settings_language', lang)}: `{settings['language']}`\n"
            f"🌍 {get_text('settings_timezone', lang)}: `{settings['timezone']}`\n"
            f"🌙 {get_text('settings_day_end', lang)}: `{settings['day_end_hour']}:00`\n\n"
            f"🎯 *{get_text('settings_goals', lang)}:*\n"
            f"   🔥 {get_text('goal_calories', lang)}: {settings['goal_calories']}\n"
            f"   🥩 {get_text('goal_protein', lang)}: {settings['goal_protein']}г\n"
            f"   🥑 {get_text('goal_fat', lang)}: {settings['goal_fat']}г\n"
            f"   🍞 {get_text('goal_carbs', lang)}: {settings['goal_carbs']}г\n\n"
            f"*Change:*\n"
            f"`/settings lang ru/en` — {get_text('settings_language', lang)}\n"
            f"`/settings timezone Europe/Moscow` — {get_text('settings_timezone', lang)}\n"
            f"`/settings day_end 4` — day until 4:00\n"
            f"`/settings goal calories 2500` — {get_text('goal_calories', lang)}"
        )
        
        await update.message.reply_text(text, parse_mode="Markdown")

    async def editfood(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /editfood command to edit custom food
        Usage: /editfood Название | поле=значение | поле=значение ...
        Fields: name, aliases, grams, calories, protein, fat, carbs
        Example: /editfood Овсянка | calories=160 | protein=6
        """
        user_id = self._get_user_id(update)

        if not context.args:
            await update.message.reply_text(
                "✏️ *Редактирование продукта*\n\n"
                "Формат:\n"
                "`/editfood Название | поле=значение`\n\n"
                "Поля: `name`, `aliases`, `grams`, `calories`, `protein`, `fat`, `carbs`\n\n"
                "Примеры:\n"
                "`/editfood Овсянка | calories=160` — изменить калории\n"
                "`/editfood Банан | grams=120 | calories=105` — изменить вес и калории\n"
                "`/editfood Яйцо | name=Яйцо куриное | aliases=яичко` — изменить название и псевдонимы",
                parse_mode="Markdown"
            )
            return

        # Parse arguments
        args_text = ' '.join(context.args)
        parts = [p.strip() for p in args_text.split('|')]

        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Нужно указать название и хотя бы одно поле для изменения.\n"
                "Пример: `/editfood Овсянка | calories=160`",
                parse_mode="Markdown"
            )
            return

        food_name = parts[0].strip()

        # Find the food
        food = self.repo.find_custom_food(user_id, food_name)
        if not food:
            await update.message.reply_text(
                f"❌ Продукт «{food_name}» не найден.\n"
                f"Проверь список: /myfoods",
                parse_mode="Markdown"
            )
            return

        # Parse field updates
        updates = {}
        field_mapping = {
            'name': str,
            'aliases': str,
            'grams': int,
            'calories': float,
            'protein': float,
            'fat': float,
            'carbs': float
        }

        for part in parts[1:]:
            if '=' not in part:
                continue
            field, value = part.split('=', 1)
            field = field.strip().lower()
            value = value.strip()

            if field in field_mapping:
                try:
                    if field_mapping[field] == str:
                        updates[field] = value
                    else:
                        updates[field] = field_mapping[field](value)
                except ValueError:
                    await update.message.reply_text(
                        f"❌ Неверное значение для поля `{field}`: {value}",
                        parse_mode="Markdown"
                    )
                    return

        if not updates:
            await update.message.reply_text(
                "❌ Не указаны поля для изменения.\n"
                "Пример: `/editfood Овсянка | calories=160`",
                parse_mode="Markdown"
            )
            return

        # Update the food
        success = self.repo.update_custom_food(user_id, food.id, **updates)

        if success:
            # Get updated food to show
            updated_food = self.repo.find_custom_food(user_id, updates.get('name', food.name))
            if not updated_food:
                updated_food = food  # Fallback

            text = (
                f"✅ *Обновлено!*\n\n"
                f"🍎 *{updated_food.name}* ({updated_food.grams}г)\n"
                f"🔥 {updated_food.calories} ккал | "
                f"🥩 {updated_food.protein}г | "
                f"🥑 {updated_food.fat}г | "
                f"🍞 {updated_food.carbs}г"
            )
            if updated_food.aliases:
                text += f"\n📌 Псевдонимы: {updated_food.aliases}"

            await update.message.reply_text(text, parse_mode="Markdown")
        else:
            await update.message.reply_text(
                "❌ Не удалось обновить продукт. Попробуй ещё раз.",
                parse_mode="Markdown"
            )

    async def delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /delete command"""
        user_id = self._get_user_id(update)
        
        if self.repo.delete_last_entry(user_id):
            await update.message.reply_text("🗑️ Последняя запись удалена!")
        else:
            await update.message.reply_text("❌ Нет записей для удаления.")
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages - intelligently determine user intent"""
        if not update.message or not update.message.text:
            return
        
        user_id = self._get_user_id(update)
        text = update.message.text.strip()
        
        logger.info(f"Received text from user {user_id}: {text[:100]}...")
        
        # First, use LLM to understand user intent
        processing_msg = await update.message.reply_text("🤔 Думаю...")
        
        try:
            intent = self.ai.detect_intent(text, user_id)
            logger.info(f"Detected intent: {intent}")
            
            if intent.get("action") == "show_summary":
                # User wants to see statistics
                date_type = intent.get("date", "today")
                if date_type == "yesterday":
                    await self._show_yesterday(update, user_id, processing_msg)
                else:
                    await self._show_today(update, user_id, processing_msg)
                    
            elif intent.get("action") == "delete_last":
                # User wants to delete last entry
                await self._delete_last_entry(update, user_id, processing_msg)

            elif intent.get("action") == "show_foods":
                # User wants to see saved custom foods
                await self._show_my_foods(update, user_id, processing_msg)

            elif intent.get("action") == "edit_food":
                # User wants to edit a custom food
                edit_params = intent.get("edit_params", {})
                await self._edit_food_voice(update, user_id, edit_params, processing_msg)

            elif intent.get("action") == "show_settings":
                # User wants to see their settings
                await self._show_settings(update, user_id, processing_msg)

            elif intent.get("action") == "change_language":
                # User wants to change language
                lang_params = intent.get("language_params", {})
                language = lang_params.get("language", "ru")
                await self._change_language(update, user_id, language, processing_msg)

            elif intent.get("action") == "add_food":
                # User is describing food
                food_description = intent.get("food_description", text)
                await self._process_food_text(update, user_id, food_description, processing_msg)

            else:
                # Default: try to process as food
                await self._process_food_text(update, user_id, text, processing_msg)
                
        except Exception as e:
            logger.error(f"Intent detection error: {e}")
            # Fallback: process as food
            await self._process_food_text(update, user_id, text, processing_msg)
    
    async def _process_food_text(
        self, 
        update: Update, 
        user_id: int, 
        text: str, 
        processing_msg
    ) -> None:
        """Process food description text (used by both text and voice handlers)"""
        try:
            logger.info(f"Processing food text: {text[:100]}...")
            # Analyze with AI (with custom foods check)
            analysis = self.ai.analyze(text, self.repo, user_id)
            logger.info(f"Analysis result: error={analysis.error}, items={len(analysis.items)}")
            
            if analysis.error:
                await processing_msg.edit_text(f"❌ Ошибка: {analysis.error}")
                return
            
            # Save to database
            self.repo.save_entry(
                user_id=user_id,
                raw_input=text,
                items=[self._item_to_dict(item) for item in analysis.items],
                totals={
                    "calories": analysis.total_calories,
                    "protein": analysis.total_protein,
                    "fat": analysis.total_fat,
                    "carbs": analysis.total_carbs
                }
            )
            
            # Format response
            response = self._format_analysis_response(analysis, user_id)
            
            keyboard = [
                [
                    InlineKeyboardButton("📊 Итоги", callback_data="today"),
                    InlineKeyboardButton("🗑️ Удалить", callback_data="delete")
                ]
            ]
            
            await processing_msg.edit_text(
                response,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            
            # Store in memory
            self.ai.add_bot_response_to_memory(user_id, response[:300], {"type": "food_logged", "calories": analysis.total_calories})
            
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            error_msg = "❌ Произошла ошибка. Попробуй ещё раз."
            await processing_msg.edit_text(error_msg)
            self.ai.add_bot_response_to_memory(user_id, error_msg, {"type": "error"})
    
    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle voice messages - download, transcribe and process"""
        if not update.message or not update.message.voice:
            return
        
        user_id = self._get_user_id(update)
        voice = update.message.voice
        
        # Show processing indicator
        processing_msg = await update.message.reply_text("🎙️ Распознаю голосовое сообщение...")
        
        try:
            # Download voice file
            logger.info(f"Downloading voice file: {voice.file_id}")
            voice_file = await context.bot.get_file(voice.file_id)
            
            # Create temp file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_file:
                audio_path = tmp_file.name
            
            try:
                # Download to temp file
                logger.info(f"Downloading to {audio_path}")
                await voice_file.download_to_drive(audio_path)
                logger.info("Download complete, starting transcription")
                
                # Transcribe
                transcribed_text = self.ai.transcribe_audio(Path(audio_path))
                logger.info(f"Transcribed: {transcribed_text[:100]}...")
                
                # Clean up temp file
                os.unlink(audio_path)
                
                # Check if transcription succeeded
                if transcribed_text.startswith("[") and "Ошибка" in transcribed_text:
                    await processing_msg.edit_text(
                        f"❌ {transcribed_text}\n\n"
                        "Пожалуйста, напиши текстом что ты ел."
                    )
                    return
                
                # Show what was recognized
                await processing_msg.edit_text(
                    f"🎙️ *Распознано:*\n_{transcribed_text}_\n\n"
                    f"🔄 Думаю...",
                    parse_mode="Markdown"
                )
                
                # Process transcribed text with intelligent intent detection
                # Simulate text message processing
                intent = self.ai.detect_intent(transcribed_text, user_id)
                logger.info(f"Voice - detected intent: {intent}")
                
                if intent.get("action") == "show_summary":
                    date_type = intent.get("date", "today")
                    if date_type == "yesterday":
                        await self._show_yesterday(update, user_id, processing_msg)
                    else:
                        await self._show_today(update, user_id, processing_msg)
                elif intent.get("action") == "delete_last":
                    await self._delete_last_entry(update, user_id, processing_msg)
                elif intent.get("action") == "show_foods":
                    await self._show_my_foods(update, user_id, processing_msg)
                elif intent.get("action") == "show_settings":
                    await self._show_settings(update, user_id, processing_msg)
                elif intent.get("action") == "change_language":
                    lang_params = intent.get("language_params", {})
                    language = lang_params.get("language", "ru")
                    await self._change_language(update, user_id, language, processing_msg)
                elif intent.get("action") == "edit_food":
                    edit_params = intent.get("edit_params", {})
                    await self._edit_food_voice(update, user_id, edit_params, processing_msg)
                elif intent.get("action") == "add_food":
                    food_description = intent.get("food_description", transcribed_text)
                    await self._process_food_text(update, user_id, food_description, processing_msg)
                else:
                    await self._process_food_text(update, user_id, transcribed_text, processing_msg)
                
            except Exception as e:
                logger.error(f"Voice processing error: {e}")
                await processing_msg.edit_text(
                    "❌ Ошибка обработки голосового сообщения.\n"
                    "Попробуй отправить текстом."
                )
                
        except Exception as e:
            logger.error(f"Voice download error: {e}")
            await update.message.reply_text(
                "❌ Не удалось скачать голосовое сообщение.\n"
                "Попробуй отправить текстом."
            )

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle photo messages - analyze nutrition labels or food photos"""
        if not update.message or not update.message.photo:
            return

        user_id = self._get_user_id(update)
        
        # Check if caption indicates what to do
        caption = update.message.caption or ""
        caption_lower = caption.lower()
        
        # Determine mode based on caption or default to food analysis
        is_label_mode = any(word in caption_lower for word in ["этикетка", "label", "упаковка", "savefood", "сохрани"])
        
        # Show processing indicator
        mode_text = "📸 Анализирую этикетку..." if is_label_mode else "🍽️ Определяю еду на фото..."
        processing_msg = await update.message.reply_text(mode_text)

        try:
            # Get the largest photo
            photo = update.message.photo[-1]
            photo_file = await context.bot.get_file(photo.file_id)

            # Create temp file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
                image_path = tmp_file.name

            try:
                # Download photo
                await photo_file.download_to_drive(image_path)

                if is_label_mode:
                    # Analyze nutrition label
                    nutrition_data = self.ai.analyze_nutrition_label(Path(image_path))
                    os.unlink(image_path)
                    await self._handle_label_analysis(processing_msg, nutrition_data, context)
                else:
                    # Analyze food photo
                    analysis = self.ai.analyze_food_photo(Path(image_path))
                    os.unlink(image_path)
                    await self._handle_food_photo_analysis(processing_msg, analysis, context, user_id)

            except Exception as e:
                logger.error(f"Photo processing error: {e}")
                await processing_msg.edit_text(
                    "❌ Ошибка обработки фото.\n"
                    "Попробуй ещё раз или введи данные вручную."
                )

        except Exception as e:
            logger.error(f"Photo download error: {e}")
            await update.message.reply_text(
                "❌ Не удалось скачать фото.\n"
                "Попробуй ещё раз."
            )

    async def _handle_label_analysis(self, processing_msg, nutrition_data: dict, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle nutrition label analysis result"""
        if "error" in nutrition_data:
            await processing_msg.edit_text(
                f"❌ Ошибка распознавания: {nutrition_data['error']}\n\n"
                "Попробуй сфотографировать чётче или введи вручную через /savefood"
            )
            return

        # Store in context for potential saving
        context.user_data["last_nutrition_photo"] = nutrition_data

        # Format response
        name = nutrition_data.get("name", "Продукт")
        grams = nutrition_data.get("grams", 100)
        calories = nutrition_data.get("calories", 0)
        protein = nutrition_data.get("protein", 0)
        fat = nutrition_data.get("fat", 0)
        carbs = nutrition_data.get("carbs", 0)
        notes = nutrition_data.get("notes", "")

        text = (
            f"📸 *Распознано с этикетки:*\n\n"
            f"🍎 *{name}*\n"
            f"⚖️ Порция: {grams}г\n"
            f"🔥 {calories} ккал\n"
            f"🥩 Белки: {protein}г\n"
            f"🥑 Жиры: {fat}г\n"
            f"🍞 Углеводы: {carbs}г"
        )

        if notes:
            text += f"\n\n💡 {notes}"

        keyboard = [
            [
                InlineKeyboardButton("💾 Сохранить", callback_data="save_photo_food"),
                InlineKeyboardButton("🍽️ Съел", callback_data="eat_photo_food")
            ]
        ]

        await processing_msg.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def _handle_food_photo_analysis(self, processing_msg, analysis, context: ContextTypes.DEFAULT_TYPE, user_id: int) -> None:
        """Handle food photo analysis result"""
        if analysis.error:
            await processing_msg.edit_text(
                f"❌ Ошибка распознавания: {analysis.error}\n\n"
                "Попробуй сфотографировать чётче или опиши текстом."
            )
            return

        # Store analysis in context for buttons
        context.user_data["last_food_photo_analysis"] = {
            "items": [self._item_to_dict(item) for item in analysis.items],
            "totals": {
                "calories": analysis.total_calories,
                "protein": analysis.total_protein,
                "fat": analysis.total_fat,
                "carbs": analysis.total_carbs
            },
            "notes": analysis.notes
        }

        # Format response
        items_text = ""
        for item in analysis.items:
            items_text += f"• {item.name} ({item.grams}г)\n"

        text = (
            f"🍽️ *Распознано на фото:*\n\n"
            f"{items_text}\n"
            f"🔥 {analysis.total_calories:.0f} ккал | "
            f"🥩 {analysis.total_protein:.1f}г | "
            f"🥑 {analysis.total_fat:.1f}г | "
            f"🍞 {analysis.total_carbs:.1f}г"
        )

        if analysis.notes:
            text += f"\n\n💡 {analysis.notes}"

        text += "\n\n📝 *Что сделать?*"

        keyboard = [
            [
                InlineKeyboardButton("✅ Записать", callback_data="log_food_photo"),
                InlineKeyboardButton("💾 Сохранить продукт", callback_data="save_food_photo_item")
            ]
        ]

        await processing_msg.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_id = self._get_user_id(update)
        action = query.data
        
        if action == "today":
            await self._show_today_callback(query, user_id)
        elif action == "yesterday":
            await self._show_yesterday_callback(query, user_id)
        elif action == "delete":
            await self._handle_delete_callback(query, user_id)
        elif action == "save_photo_food":
            await self._handle_save_photo_food(query, user_id, context)
        elif action == "eat_photo_food":
            await self._handle_eat_photo_food(query, user_id, context)
        elif action == "log_food_photo":
            await self._handle_log_food_photo(query, user_id, context)
        elif action == "save_food_photo_item":
            await self._handle_save_food_photo_item(query, user_id, context)
    
    # Helper methods
    
    def _get_user_id(self, update: Update) -> int:
        """Extract user ID from update"""
        if update.callback_query:
            return update.callback_query.from_user.id
        return update.effective_user.id
    
    def _get_user_lang(self, user_id: int) -> str:
        """Get user's language setting"""
        settings = self.repo.get_user_settings(user_id)
        return settings.get('language', 'ru')
    
    def _format_daily_report(
        self,
        title: str,
        summary: DailySummary,
        entries: list
    ) -> str:
        """Format daily report text"""
        text = (
            f"📊 *Итоги за {title}*\n\n"
            f"🔥 Калории: *{summary.calories}* ккал\n"
            f"🥩 Белки: *{summary.protein}* г\n"
            f"🥑 Жиры: *{summary.fat}* г\n"
            f"🍞 Углеводы: *{summary.carbs}* г\n\n"
            f"📝 Записей: {summary.entries_count}"
        )
        
        if entries:
            text += "\n\n*Последние записи:*\n"
            for entry in entries[:5]:
                time_str = datetime.fromisoformat(entry.timestamp).strftime("%H:%M")
                items_str = ", ".join(item.get("name", "?") for item in entry.items[:2])
                if len(entry.items) > 2:
                    items_str += f" +{len(entry.items)-2}"
                text += f"• {time_str} — {items_str} ({int(entry.total_calories)} ккал)\n"
        
        return text
    
    def _format_analysis_response(self, analysis: NutritionAnalysis, user_id: int) -> str:
        """Format AI analysis response"""
        response = "✅ *Записано!*\n\n"
        
        if analysis.items:
            response += "*Распознано:*\n"
            for item in analysis.items:
                response += (
                    f"• {item.name} — {item.grams}г "
                    f"({item.calories} ккал)\n"
                )
            response += "\n"
        
        response += (
            f"🔥 *{int(analysis.total_calories)}* ккал | "
            f"🥩 *{analysis.total_protein:.1f}*г | "
            f"🥑 *{analysis.total_fat:.1f}*г | "
            f"🍞 *{analysis.total_carbs:.1f}*г"
        )
        
        if analysis.notes:
            response += f"\n\n💡 {analysis.notes}"
        
        # Add daily summary
        today_str = datetime.now().strftime("%Y-%m-%d")
        daily = self.repo.get_daily_summary(user_id, today_str)
        response += f"\n\n📊 *За день:* {daily.calories} ккал"
        
        return response
    
    def _item_to_dict(self, item) -> dict:
        """Convert NutritionItem to dict"""
        return {
            "name": item.name,
            "grams": item.grams,
            "calories": item.calories,
            "protein": item.protein,
            "fat": item.fat,
            "carbs": item.carbs
        }
    
    async def _show_today_callback(self, query, user_id: int) -> None:
        """Show today's summary in callback"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        summary = self.repo.get_daily_summary(user_id, today_str)
        entries = self.repo.get_day_entries(user_id, today_str)
        
        text = self._format_daily_report("сегодня", summary, entries)
        keyboard = [[InlineKeyboardButton("🗑️ Удалить последнее", callback_data="delete")]]
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    async def _show_yesterday_callback(self, query, user_id: int) -> None:
        """Show yesterday's summary in callback"""
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        summary = self.repo.get_daily_summary(user_id, yesterday_str)
        
        text = (
            f"📈 *Итоги за вчера ({yesterday.strftime('%d.%m')})*\n\n"
            f"🔥 Калории: *{summary.calories}* ккал\n"
            f"🥩 Белки: *{summary.protein}* г\n"
            f"🥑 Жиры: *{summary.fat}* г\n"
            f"🍞 Углеводы: *{summary.carbs}* г\n\n"
            f"📝 Записей: {summary.entries_count}"
        )
        
        await query.edit_message_text(text, parse_mode="Markdown")

    async def _handle_save_photo_food(self, query, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Save food from photo analysis to custom foods"""
        nutrition_data = context.user_data.get("last_nutrition_photo")

        if not nutrition_data:
            await query.edit_message_text(
                "❌ Данные не найдены. Сфотографируй этикетку ещё раз.",
                parse_mode="Markdown"
            )
            return

        try:
            name = nutrition_data.get("name", "Продукт")
            grams = nutrition_data.get("grams", 100)
            calories = nutrition_data.get("calories", 0)
            protein = nutrition_data.get("protein", 0)
            fat = nutrition_data.get("fat", 0)
            carbs = nutrition_data.get("carbs", 0)

            food_id = self.repo.save_custom_food(
                user_id=user_id,
                name=name,
                aliases="",
                grams=grams,
                calories=calories,
                protein=protein,
                fat=fat,
                carbs=carbs
            )

            await query.edit_message_text(
                f"✅ *Сохранено!*\n\n"
                f"🍎 *{name}* ({grams}г)\n"
                f"🔥 {calories} ккал | "
                f"🥩 {protein}г | "
                f"🥑 {fat}г | "
                f"🍞 {carbs}г\n\n"
                f"Теперь можно просто написать «съел {name}»",
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error saving photo food: {e}")
            await query.edit_message_text(
                f"❌ Ошибка сохранения: {e}",
                parse_mode="Markdown"
            )

    async def _handle_eat_photo_food(self, query, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log food from photo analysis to daily entries"""
        nutrition_data = context.user_data.get("last_nutrition_photo")

        if not nutrition_data:
            await query.edit_message_text(
                "❌ Данные не найдены. Сфотографируй этикетку ещё раз.",
                parse_mode="Markdown"
            )
            return

        try:
            name = nutrition_data.get("name", "Продукт")
            grams = nutrition_data.get("grams", 100)
            calories = nutrition_data.get("calories", 0)
            protein = nutrition_data.get("protein", 0)
            fat = nutrition_data.get("fat", 0)
            carbs = nutrition_data.get("carbs", 0)

            # Save to daily entries
            self.repo.save_entry(
                user_id=user_id,
                raw_input=f"{name} ({grams}г) — с фото этикетки",
                items=[{
                    "name": name,
                    "grams": grams,
                    "calories": calories,
                    "protein": protein,
                    "fat": fat,
                    "carbs": carbs
                }],
                totals={
                    "calories": calories,
                    "protein": protein,
                    "fat": fat,
                    "carbs": carbs
                }
            )

            # Get daily summary
            today_str = datetime.now().strftime("%Y-%m-%d")
            daily = self.repo.get_daily_summary(user_id, today_str)

            await query.edit_message_text(
                f"✅ *Записано!*\n\n"
                f"🍎 *{name}* ({grams}г)\n"
                f"🔥 {calories} ккал | "
                f"🥩 {protein}г | "
                f"🥑 {fat}г | "
                f"🍞 {carbs}г\n\n"
                f"📊 *За день:* {daily.calories} ккал",
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error logging photo food: {e}")
            await query.edit_message_text(
                f"❌ Ошибка записи: {e}",
                parse_mode="Markdown"
            )

    async def _handle_log_food_photo(self, query, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Log food from photo analysis to daily entries"""
        analysis_data = context.user_data.get("last_food_photo_analysis")

        if not analysis_data:
            await query.edit_message_text(
                "❌ Данные не найдены. Сфотографируй еду ещё раз.",
                parse_mode="Markdown"
            )
            return

        try:
            items = analysis_data.get("items", [])
            totals = analysis_data.get("totals", {})

            # Save to daily entries
            self.repo.save_entry(
                user_id=user_id,
                raw_input="С фото еды",
                items=items,
                totals=totals
            )

            # Get daily summary
            today_str = datetime.now().strftime("%Y-%m-%d")
            daily = self.repo.get_daily_summary(user_id, today_str)

            # Format items list
            items_text = ""
            for item in items:
                items_text += f"• {item.get('name', 'Еда')} ({item.get('grams', 0)}г)\n"

            await query.edit_message_text(
                f"✅ *Записано!*\n\n"
                f"{items_text}\n"
                f"🔥 {totals.get('calories', 0):.0f} ккал | "
                f"🥩 {totals.get('protein', 0):.1f}г | "
                f"🥑 {totals.get('fat', 0):.1f}г | "
                f"🍞 {totals.get('carbs', 0):.1f}г\n\n"
                f"📊 *За день:* {daily.calories} ккал",
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error logging food photo: {e}")
            await query.edit_message_text(
                f"❌ Ошибка записи: {e}",
                parse_mode="Markdown"
            )

    async def _handle_save_food_photo_item(self, query, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Save first food item from photo analysis to custom foods"""
        analysis_data = context.user_data.get("last_food_photo_analysis")

        if not analysis_data:
            await query.edit_message_text(
                "❌ Данные не найдены. Сфотографируй еду ещё раз.",
                parse_mode="Markdown"
            )
            return

        try:
            items = analysis_data.get("items", [])
            if not items:
                await query.edit_message_text(
                    "❌ На фото ничего не распознано.",
                    parse_mode="Markdown"
                )
                return

            # Save first item as custom food
            item = items[0]
            name = item.get("name", "Еда")
            grams = item.get("grams", 100)
            calories = item.get("calories", 0)
            protein = item.get("protein", 0)
            fat = item.get("fat", 0)
            carbs = item.get("carbs", 0)

            food_id = self.repo.save_custom_food(
                user_id=user_id,
                name=name,
                aliases="",
                grams=grams,
                calories=calories,
                protein=protein,
                fat=fat,
                carbs=carbs
            )

            await query.edit_message_text(
                f"✅ *Сохранено в твои продукты!*\n\n"
                f"🍎 *{name}* ({grams}г)\n"
                f"🔥 {calories} ккал | "
                f"🥩 {protein}г | "
                f"🥑 {fat}г | "
                f"🍞 {carbs}г\n\n"
                f"Теперь можно просто написать «съел {name}»",
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error saving food photo item: {e}")
            await query.edit_message_text(
                f"❌ Ошибка сохранения: {e}",
                parse_mode="Markdown"
            )

    async def _show_my_foods(self, update: Update, user_id: int, processing_msg) -> None:
        """Show user's saved custom foods (called from LLM intent detection)"""
        foods = self.repo.get_custom_foods(user_id)

        if not foods:
            await processing_msg.edit_text(
                "📝 *У тебя пока нет сохранённых продуктов*\n\n"
                "Добавь командой:\n"
                "`/savefood Название | псевдонимы | гр | ккал | б | ж | у`\n\n"
                "Или сфотографируй этикетку!",
                parse_mode="Markdown"
            )
            return

        text = f"🍎 *Твои сохранённые продукты* ({len(foods)}):\n\n"

        for i, food in enumerate(foods, 1):
            aliases_text = f" (aka: {food.aliases})" if food.aliases else ""
            text += (
                f"{i}. *{food.name}*{aliases_text}\n"
                f"   {food.grams}г = 🔥{food.calories} | "
                f"🥩{food.protein} | 🥑{food.fat} | 🍞{food.carbs}\n\n"
            )

        text += (
            "\n💡 *Команды:*\n"
            "`/deletefood Название` — удалить\n"
            "`/editfood Название | новые_данные` — изменить"
        )

        await processing_msg.edit_text(text, parse_mode="Markdown")
        
        # Store in memory
        self.ai.add_bot_response_to_memory(user_id, text, {"type": "show_foods"})

    async def _edit_food_voice(self, update: Update, user_id: int, edit_params: dict, processing_msg) -> None:
        """Edit custom food via voice/natural language"""
        food_name = edit_params.get("food_name", "")
        field = edit_params.get("field", "")
        value = edit_params.get("value", "")

        if not food_name or not field or not value:
            error_msg = (
                "❌ Не понял что изменить. Попробуй так:\n"
                "«измени овсянку на 160 калорий»\n"
                "«поменяй в банане белки на 2 грамма»"
            )
            await processing_msg.edit_text(error_msg, parse_mode="Markdown")
            self.ai.add_bot_response_to_memory(user_id, error_msg, {"type": "error"})
            return

        # Find the food
        food = self.repo.find_custom_food(user_id, food_name)
        if not food:
            not_found_msg = (
                f"❌ Продукт «{food_name}» не найден.\n"
                f"Проверь список: /myfoods"
            )
            await processing_msg.edit_text(not_found_msg, parse_mode="Markdown")
            self.ai.add_bot_response_to_memory(user_id, not_found_msg, {"type": "error", "food_name": food_name})
            return

        # Map field names
        field_mapping = {
            'калории': 'calories',
            'калорий': 'calories',
            'ккал': 'calories',
            'белки': 'protein',
            'белок': 'protein',
            'жиры': 'fat',
            'жир': 'fat',
            'углеводы': 'carbs',
            'углевод': 'carbs',
            'граммы': 'grams',
            'грамм': 'grams',
            'вес': 'grams',
            'название': 'name',
            'имя': 'name',
            'псевдонимы': 'aliases',
            'алиасы': 'aliases'
        }

        # Convert field to English if needed
        field_en = field_mapping.get(field.lower(), field.lower())

        # Validate field
        valid_fields = ['calories', 'protein', 'fat', 'carbs', 'grams', 'name', 'aliases']
        if field_en not in valid_fields:
            await processing_msg.edit_text(
                f"❌ Неизвестное поле: {field}\n"
                f"Доступные: калории, белки, жиры, углеводы, граммы, название, псевдонимы",
                parse_mode="Markdown"
            )
            return

        # Parse value based on field type
        try:
            if field_en in ['calories', 'protein', 'fat', 'carbs']:
                # Extract number from value (e.g., "160 калорий" -> 160)
                import re
                numbers = re.findall(r'\d+(?:\.\d+)?', str(value))
                if numbers:
                    parsed_value = float(numbers[0])
                else:
                    raise ValueError(f"Не найдено число в: {value}")
            elif field_en == 'grams':
                import re
                numbers = re.findall(r'\d+', str(value))
                if numbers:
                    parsed_value = int(numbers[0])
                else:
                    raise ValueError(f"Не найдено число в: {value}")
            else:
                # name, aliases - string
                parsed_value = str(value).strip()
        except ValueError as e:
            val_error_msg = f"❌ Не удалось распознать значение: {value}"
            await processing_msg.edit_text(val_error_msg, parse_mode="Markdown")
            self.ai.add_bot_response_to_memory(user_id, val_error_msg, {"type": "error"})
            return

        # Build update dict
        updates = {field_en: parsed_value}

        # Update the food
        success = self.repo.update_custom_food(user_id, food.id, **updates)

        if success:
            # Get updated food
            updated_food = self.repo.find_custom_food(user_id, food_name if field_en != 'name' else parsed_value)
            if not updated_food:
                updated_food = food

            field_names_ru = {
                'calories': 'калории',
                'protein': 'белки',
                'fat': 'жиры',
                'carbs': 'углеводы',
                'grams': 'граммы',
                'name': 'название',
                'aliases': 'псевдонимы'
            }

            success_msg = (
                f"✅ *Обновлено!*\n\n"
                f"🍎 *{updated_food.name}* ({updated_food.grams}г)\n"
                f"🔥 {updated_food.calories} ккал | "
                f"🥩 {updated_food.protein}г | "
                f"🥑 {updated_food.fat}г | "
                f"🍞 {updated_food.carbs}г\n\n"
                f"Изменено: {field_names_ru.get(field_en, field_en)} = {parsed_value}"
            )
            await processing_msg.edit_text(success_msg, parse_mode="Markdown")
            self.ai.add_bot_response_to_memory(
                user_id, success_msg, 
                {"type": "edit_food", "food_name": updated_food.name, "field": field_en, "value": parsed_value}
            )
        else:
            fail_msg = "❌ Не удалось обновить. Попробуй через команду: /editfood"
            await processing_msg.edit_text(fail_msg, parse_mode="Markdown")
            self.ai.add_bot_response_to_memory(user_id, fail_msg, {"type": "error"})

    # LLM-powered intent handlers

    async def _show_today(self, update: Update, user_id: int, processing_msg) -> None:
        """Show today's summary (called from LLM intent detection)"""
        today_str = datetime.now().strftime("%Y-%m-%d")
        summary = self.repo.get_daily_summary(user_id, today_str)
        entries = self.repo.get_day_entries(user_id, today_str)
        
        text = self._format_daily_report("сегодня", summary, entries)
        keyboard = [
            [
                InlineKeyboardButton("📈 Вчера", callback_data="yesterday"),
                InlineKeyboardButton("🗑️ Удалить", callback_data="delete")
            ]
        ]
        
        await processing_msg.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        self.ai.add_bot_response_to_memory(user_id, text[:200], {"type": "show_today"})

    async def _show_yesterday(self, update: Update, user_id: int, processing_msg) -> None:
        """Show yesterday's summary (called from LLM intent detection)"""
        yesterday = datetime.now() - timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        summary = self.repo.get_daily_summary(user_id, yesterday_str)
        
        text = (
            f"📈 *Итоги за вчера ({yesterday.strftime('%d.%m')})*\n\n"
            f"🔥 Калории: *{summary.calories}* ккал\n"
            f"🥩 Белки: *{summary.protein}* г\n"
            f"🥑 Жиры: *{summary.fat}* г\n"
            f"🍞 Углеводы: *{summary.carbs}* г\n\n"
            f"📝 Записей: {summary.entries_count}"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Сегодня", callback_data="today"),
                InlineKeyboardButton("🗑️ Удалить", callback_data="delete")
            ]
        ]
        
        await processing_msg.edit_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        self.ai.add_bot_response_to_memory(user_id, text[:200], {"type": "show_yesterday"})

    async def _show_settings(self, update: Update, user_id: int, processing_msg) -> None:
        """Show user settings (called from LLM intent detection)"""
        lang = self._get_user_lang(user_id)
        settings = self.repo.get_user_settings(user_id)
        
        text = (
            f"⚙️ *{get_text('settings_title', lang)}*\n\n"
            f"🌐 {get_text('settings_language', lang)}: `{settings['language']}`\n"
            f"🌍 {get_text('settings_timezone', lang)}: `{settings['timezone']}`\n"
            f"🌙 {get_text('settings_day_end', lang)}: `{settings['day_end_hour']}:00`\n\n"
            f"🎯 *{get_text('settings_goals', lang)}:*\n"
            f"   🔥 {get_text('goal_calories', lang)}: {settings['goal_calories']}\n"
            f"   🥩 {get_text('goal_protein', lang)}: {settings['goal_protein']}г\n"
            f"   🥑 {get_text('goal_fat', lang)}: {settings['goal_fat']}г\n"
            f"   🍞 {get_text('goal_carbs', lang)}: {settings['goal_carbs']}г\n\n"
            f"*Change:*\n"
            f"`/settings lang ru/en` — {get_text('settings_language', lang)}\n"
            f"`/settings timezone Europe/Moscow` — {get_text('settings_timezone', lang)}\n"
            f"`/settings day_end 4` — day until 4:00\n"
            f"`/settings goal calories 2500` — {get_text('goal_calories', lang)}"
        )
        
        await processing_msg.edit_text(text, parse_mode="Markdown")
        self.ai.add_bot_response_to_memory(user_id, text[:200], {"type": "show_settings"})

    async def _change_language(self, update: Update, user_id: int, language: str, processing_msg) -> None:
        """Change user language (called from LLM intent detection)"""
        current_lang = self._get_user_lang(user_id)
        
        # Validate language
        language = language.lower().strip()
        
        # Handle variations
        lang_map = {
            'ru': 'ru', 'русский': 'ru', 'рус': 'ru', 'russian': 'ru',
            'en': 'en', 'english': 'en', 'английский': 'en', 'англ': 'en'
        }
        
        normalized_lang = lang_map.get(language, language)
        
        if normalized_lang not in ['ru', 'en']:
            error_msg = get_text('language_error', current_lang)
            await processing_msg.edit_text(error_msg, parse_mode="Markdown")
            self.ai.add_bot_response_to_memory(user_id, error_msg, {"type": "error"})
            return
        
        # Update settings
        success = self.repo.update_user_settings(user_id, language=normalized_lang)
        
        if success:
            lang_names = {'ru': 'Русский', 'en': 'English'}
            success_msg = get_text('language_changed', normalized_lang, language=lang_names.get(normalized_lang, normalized_lang))
            await processing_msg.edit_text(success_msg, parse_mode="Markdown")
            self.ai.add_bot_response_to_memory(user_id, success_msg, {"type": "change_language", "language": normalized_lang})
        else:
            error_msg = get_text('error_settings', current_lang, command="/settings lang en")
            await processing_msg.edit_text(error_msg, parse_mode="Markdown")
            self.ai.add_bot_response_to_memory(user_id, error_msg, {"type": "error"})

    async def _delete_last_entry(self, update: Update, user_id: int, processing_msg) -> None:
        """Delete last entry (called from LLM intent detection)"""
        lang = self._get_user_lang(user_id)
        success = self.repo.delete_last_entry(user_id)
        
        if success:
            del_msg = get_text('delete_last_success', lang)
            await processing_msg.edit_text(del_msg, parse_mode="Markdown")
            self.ai.add_bot_response_to_memory(user_id, del_msg, {"type": "delete_last"})
        else:
            no_del_msg = get_text('delete_last_none', lang)
            await processing_msg.edit_text(no_del_msg, parse_mode="Markdown")
            self.ai.add_bot_response_to_memory(user_id, no_del_msg, {"type": "error"})
    
    async def _handle_delete_callback(self, query, user_id: int) -> None:
        """Handle delete in callback"""
        if self.repo.delete_last_entry(user_id):
            await query.edit_message_text(
                "🗑️ Последняя запись удалена!\n\n"
                "Используй /today для обновлённой статистики."
            )
        else:
            await query.edit_message_text("❌ Нет записей для удаления.")
