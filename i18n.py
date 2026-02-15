"""Localization module for multi-language support"""

from typing import Dict, Any

# Translations dictionary
TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "ru": {
        # General
        "welcome": "🥗 *Nutrition Tracker Bot*\n\nПривет! Я — умный трекер питания с AI.",
        "thinking": "🤔 Думаю...",
        "processing_photo": "📸 Анализирую фото...",
        "processing_voice": "🎙️ Распознаю голосовое сообщение...",
        
        # Commands
        "cmd_settings": "⚙️ Настройки",
        "cmd_today": "📊 Сегодня",
        "cmd_help": "❓ Помощь",
        
        # Settings
        "settings_title": "Настройки",
        "settings_language": "Язык",
        "settings_timezone": "Часовой пояс",
        "settings_day_end": "День заканчивается в",
        "settings_goals": "Цели на день",
        "settings_current": "Текущие настройки",
        
        # Goals
        "goal_calories": "Калории",
        "goal_protein": "Белки",
        "goal_fat": "Жиры",
        "goal_carbs": "Углеводы",
        
        # Daily summary
        "today_summary": "Итоги за сегодня",
        "yesterday_summary": "Итоги за вчера",
        "calories": "Калории",
        "protein": "Белки",
        "fat": "Жиры",
        "carbs": "Углеводы",
        "entries_count": "Записей",
        "of_goal": "из",
        "remaining": "Осталось",
        
        # Food logging
        "food_logged": "Записано!",
        "recognized": "Распознано",
        "daily_total": "За день",
        
        # Custom foods
        "my_foods_title": "Твои сохранённые продукты",
        "no_foods": "У тебя пока нет сохранённых продуктов",
        "food_saved": "Сохранено!",
        "food_updated": "Обновлено!",
        "food_deleted": "Удалено",
        
        # Errors
        "error_general": "❌ Произошла ошибка. Попробуй ещё раз.",
        "error_not_found": "❌ Не найдено",
        "error_parse": "❌ Не удалось распознать",
        
        # Context help
        "help_text": """*Команды:*
/myfoods — мои продукты
/savefood — сохранить продукт
/editfood — редактировать
/deletefood — удалить
/settings — настройки

*Голосом или текстом:*
• «Я съел банан» — запись еды
• «Покажи итоги» — статистика
• «Измени овсянку на 160 калорий» — редактирование""",
        
        # Voice recognition
        "voice_recognized": "🎙️ *Распознано:*\n_{text}_\n\n🔄 Думаю...",
        
        # Food items
        "food_item_line": "• {name} ({grams}г)\n",
        
        # Summary formatting
        "summary_calories": "🔥 Калории: *{value}* ккал",
        "summary_protein": "🥩 Белки: *{value}* г",
        "summary_fat": "🥑 Жиры: *{value}* г", 
        "summary_carbs": "🍞 Углеводы: *{value}* г",
        "summary_entries": "📝 Записей: {count}",
        
        # Buttons
        "btn_yesterday": "📈 Вчера",
        "btn_today": "📊 Сегодня",
        "btn_delete": "🗑️ Удалить",
        "btn_summary": "📊 Итоги",
        
        # Edit food
        "edit_food_prompt": "✏️ Что изменить в «{name}»?\n\nНапиши: `поле=значение`\nПример: `calories=160`",
        "edit_success": "✅ *Обновлено!*\n\n🍎 *{name}* ({grams}г)\n🔥 {calories} ккал | 🥩 {protein}г | 🥑 {fat}г | 🍞 {carbs}г\n\nИзменено: {field} = {value}",
        
        # Delete
        "delete_last_success": "🗑️ *Последняя запись удалена*\n\nИспользуй /today чтобы увидеть обновлённые итоги.",
        "delete_last_none": "⚠️ Нет записей для удаления.",
        
        # Language change
        "language_changed": "✅ Язык изменён на: {language}",
        "language_error": "❌ Неизвестный язык. Доступные:\n• русский / ru\n• английский / en",
        
        # Timezone
        "timezone_changed": "✅ Часовой пояс изменён на: {timezone}",
        "day_end_changed": "✅ День теперь заканчивается в {hour}:00",
        
        # Goal settings
        "goal_changed": "✅ Цель по {field} изменена на: {value}",
        
        # Errors specific
        "error_no_value": "❌ Не указаны поля для изменения.\nПример: `/editfood Овсянка | calories=160`",
        "error_invalid_field": "❌ Неверное значение для поля `{field}`: {value}",
        "error_food_not_found": "❌ Продукт «{name}» не найден.\nПроверь список: /myfoods",
        "error_food_not_found_short": "❌ Продукт не найден.",
        "error_parse_value": "❌ Не удалось распознать значение: {value}",
        "error_transcription": "❌ {error}\n\nПожалуйста, напиши текстом что ты ел.",
        "error_edit_voice": "❌ Не понял что изменить. Попробуй так:\n«измени овсянку на 160 калорий»\n«поменяй в банане белки на 2 грамма»",
        "error_settings": "❌ Не удалось изменить настройку. Попробуй команду: {command}",
        
        # Save food
        "save_food_usage": "📝 Использование:\n`/savefood Название | псевдонимы | гр | ккал | б | ж | у`\n\nПример:\n`/savefood Овсянка | овес, каша | 100 | 350 | 12 | 7 | 60`",
        "save_food_saved": "✅ *Сохранено!*\n\n🍎 *{name}* ({grams}г)\n🔥 {calories} ккал | 🥩 {protein}г | 🥑 {fat}г | 🍞 {carbs}г\n\nТеперь можно просто написать «съел {name}»",
        
        # Photo analysis
        "photo_processing": "📸 Анализирую фото...",
        "photo_label_result": "📋 *Этикетка распознана*\n\n🍎 *{name}* ({grams}г)\n🔥 {calories} ккал | 🥩 {protein}г | 🥑 {fat}г | 🍞 {carbs}г",
        "photo_food_result": "🍽️ *Распознано на фото:*\n\n{items}\n🔥 {calories} ккал | 🥩 {protein}г | 🥑 {fat}г | 🍞 {carbs}г",
        "photo_log_button": "📝 Записать в дневник",
        "photo_save_button": "💾 Сохранить продукт",
        
        # Callback results
        "callback_logged": "✅ *Записано!*\n\n🍎 *{name}* ({grams}г)\n🔥 {calories} ккал | 🥩 {protein}г | 🥑 {fat}г | 🍞 {carbs}г\n\n📊 *За день:* {daily_calories} ккал",
        "callback_deleted": "🗑️ Последняя запись удалена!\n\nИспользуй /today для обновлённой статистики.",
        "callback_no_data": "❌ Данные не найдены. Сфотографируй ещё раз.",
        "callback_nothing_found": "❌ На фото ничего не распознано.",
        
        # Commands help
        "commands_myfoods": "/myfoods — мои продукты",
        "commands_savefood": "/savefood — сохранить продукт",
        "commands_deletefood": "/deletefood — удалить продукт",
        "commands_editfood": "/editfood — редактировать продукт",
        
        # Delete food
        "deletefood_usage": "🗑️ Использование: `/deletefood Название`\n\nПример: `/deletefood Овсянка`",
        "deletefood_success": "🗑️ *Удалено:* {name}",
        "deletefood_not_found": "❌ Продукт «{name}» не найден.",
        
        # Edit food command
        "editfood_usage": "✏️ Использование:\n`/editfood Название | поле=значение`\n\nПоля: name, aliases, grams, calories, protein, fat, carbs\n\nПример:\n`/editfood Овсянка | calories=160`\n`/editfood Банан | protein=1.5 | carbs=23`",
    },
    
    "en": {
        # General
        "welcome": "🥗 *Nutrition Tracker Bot*\n\nHi! I'm a smart AI-powered nutrition tracker.",
        "thinking": "🤔 Thinking...",
        "processing_photo": "📸 Analyzing photo...",
        "processing_voice": "🎙️ Transcribing voice message...",
        
        # Commands
        "cmd_settings": "⚙️ Settings",
        "cmd_today": "📊 Today",
        "cmd_help": "❓ Help",
        
        # Settings
        "settings_title": "Settings",
        "settings_language": "Language",
        "settings_timezone": "Timezone",
        "settings_day_end": "Day ends at",
        "settings_goals": "Daily goals",
        "settings_current": "Current settings",
        
        # Goals
        "goal_calories": "Calories",
        "goal_protein": "Protein",
        "goal_fat": "Fat",
        "goal_carbs": "Carbs",
        
        # Daily summary
        "today_summary": "Today's summary",
        "yesterday_summary": "Yesterday's summary",
        "calories": "Calories",
        "protein": "Protein",
        "fat": "Fat",
        "carbs": "Carbs",
        "entries_count": "Entries",
        "of_goal": "of",
        "remaining": "Remaining",
        
        # Food logging
        "food_logged": "Logged!",
        "recognized": "Recognized",
        "daily_total": "Daily total",
        
        # Custom foods
        "my_foods_title": "Your saved foods",
        "no_foods": "You have no saved foods yet",
        "food_saved": "Saved!",
        "food_updated": "Updated!",
        "food_deleted": "Deleted",
        
        # Errors
        "error_general": "❌ An error occurred. Please try again.",
        "error_not_found": "❌ Not found",
        "error_parse": "❌ Could not parse",
        
        # Context help
        "help_text": """*Commands:*
/myfoods — my foods
/savefood — save food
/editfood — edit food  
/deletefood — delete food
/settings — settings

*Voice or text:*
• "I ate a banana" — log food
• "Show my summary" — statistics
• "Change oats to 160 calories" — editing""",
        
        # Voice recognition
        "voice_recognized": "🎙️ *Recognized:*\n_{text}_\n\n🔄 Thinking...",
        
        # Food items
        "food_item_line": "• {name} ({grams}g)\n",
        
        # Summary formatting
        "summary_calories": "🔥 Calories: *{value}* kcal",
        "summary_protein": "🥩 Protein: *{value}* g",
        "summary_fat": "🥑 Fat: *{value}* g", 
        "summary_carbs": "🍞 Carbs: *{value}* g",
        "summary_entries": "📝 Entries: {count}",
        
        # Buttons
        "btn_yesterday": "📈 Yesterday",
        "btn_today": "📊 Today",
        "btn_delete": "🗑️ Delete",
        "btn_summary": "📊 Summary",
        
        # Edit food
        "edit_food_prompt": "✏️ What to change in «{name}»?\n\nWrite: `field=value`\nExample: `calories=160`",
        "edit_success": "✅ *Updated!*\n\n🍎 *{name}* ({grams}g)\n🔥 {calories} kcal | 🥩 {protein}g | 🥑 {fat}g | 🍞 {carbs}g\n\nChanged: {field} = {value}",
        
        # Delete
        "delete_last_success": "🗑️ *Last entry deleted*\n\nUse /today to see updated totals.",
        "delete_last_none": "⚠️ No entries to delete.",
        
        # Language change
        "language_changed": "✅ Language changed to: {language}",
        "language_error": "❌ Unknown language. Available:\n• русский / ru\n• english / en",
        
        # Timezone
        "timezone_changed": "✅ Timezone changed to: {timezone}",
        "day_end_changed": "✅ Day now ends at {hour}:00",
        
        # Goal settings
        "goal_changed": "✅ Goal for {field} changed to: {value}",
        
        # Errors specific
        "error_no_value": "❌ No fields to change.\nExample: `/editfood Oats | calories=160`",
        "error_invalid_field": "❌ Invalid value for field `{field}`: {value}",
        "error_food_not_found": "❌ Food «{name}» not found.\nCheck list: /myfoods",
        "error_food_not_found_short": "❌ Food not found.",
        "error_parse_value": "❌ Could not parse value: {value}",
        "error_transcription": "❌ {error}\n\nPlease type what you ate.",
        "error_edit_voice": "❌ Didn't understand what to change. Try:\n«change oats to 160 calories»\n«update protein in banana to 2 grams»",
        "error_settings": "❌ Could not change setting. Try command: {command}",
        
        # Save food
        "save_food_usage": "📝 Usage:\n`/savefood Name | aliases | g | kcal | p | f | c`\n\nExample:\n`/savefood Oats | oatmeal | 100 | 350 | 12 | 7 | 60`",
        "save_food_saved": "✅ *Saved!*\n\n🍎 *{name}* ({grams}g)\n🔥 {calories} kcal | 🥩 {protein}g | 🥑 {fat}g | 🍞 {carbs}g\n\nNow you can just say «ate {name}»",
        
        # Photo analysis
        "photo_processing": "📸 Analyzing photo...",
        "photo_label_result": "📋 *Label recognized*\n\n🍎 *{name}* ({grams}g)\n🔥 {calories} kcal | 🥩 {protein}g | 🥑 {fat}g | 🍞 {carbs}g",
        "photo_food_result": "🍽️ *Recognized in photo:*\n\n{items}\n🔥 {calories} kcal | 🥩 {protein}g | 🥑 {fat}g | 🍞 {carbs}g",
        "photo_log_button": "📝 Log to diary",
        "photo_save_button": "💾 Save food",
        
        # Callback results
        "callback_logged": "✅ *Logged!*\n\n🍎 *{name}* ({grams}g)\n🔥 {calories} kcal | 🥩 {protein}g | 🥑 {fat}g | 🍞 {carbs}g\n\n📊 *Daily:* {daily_calories} kcal",
        "callback_deleted": "🗑️ Last entry deleted!\n\nUse /today for updated stats.",
        "callback_no_data": "❌ Data not found. Take a photo again.",
        "callback_nothing_found": "❌ Nothing recognized in photo.",
        
        # Commands help
        "commands_myfoods": "/myfoods — my foods",
        "commands_savefood": "/savefood — save food",
        "commands_deletefood": "/deletefood — delete food",
        "commands_editfood": "/editfood — edit food",
        
        # Delete food
        "deletefood_usage": "🗑️ Usage: `/deletefood Name`\n\nExample: `/deletefood Oats`",
        "deletefood_success": "🗑️ *Deleted:* {name}",
        "deletefood_not_found": "❌ Food «{name}» not found.",
        
        # Edit food command
        "editfood_usage": "✏️ Usage:\n`/editfood Name | field=value`\n\nFields: name, aliases, grams, calories, protein, fat, carbs\n\nExample:\n`/editfood Oats | calories=160`\n`/editfood Banana | protein=1.5 | carbs=23`",
    }
}


def get_text(key: str, language: str = "ru", **kwargs) -> str:
    """Get translated text by key"""
    lang = language if language in TRANSLATIONS else "ru"
    text = TRANSLATIONS[lang].get(key, TRANSLATIONS["ru"].get(key, key))
    
    # Format with kwargs if provided
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    
    return text


def get_supported_languages() -> Dict[str, str]:
    """Get list of supported languages"""
    return {
        "ru": "Русский",
        "en": "English"
    }
