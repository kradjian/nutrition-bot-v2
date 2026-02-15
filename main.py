"""Application entry point"""

import logging
import sys
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from config import get_settings
from database import NutritionRepository
from ai_service import NutritionAIService
from handlers import BotHandlers


def setup_logging(log_level: str = "INFO") -> None:
    """Configure application logging"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)


def main() -> None:
    """Main entry point"""
    # Load settings
    settings = get_settings()
    
    # Setup logging
    setup_logging(settings.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Nutrition Bot v2...")
    
    # Initialize services
    repository = NutritionRepository(settings.database_path)
    ai_service = NutritionAIService()
    handlers = BotHandlers(repository, ai_service)
    
    # Create bot application
    application = (
        Application.builder()
        .token(settings.bot_token)
        .build()
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", handlers.start))
    application.add_handler(CommandHandler("today", handlers.today))
    application.add_handler(CommandHandler("yesterday", handlers.yesterday))
    application.add_handler(CommandHandler("delete", handlers.delete))
    application.add_handler(CommandHandler("savefood", handlers.savefood))
    application.add_handler(CommandHandler("myfoods", handlers.myfoods))
    application.add_handler(CommandHandler("deletefood", handlers.deletefood))
    application.add_handler(CommandHandler("editfood", handlers.editfood))
    application.add_handler(CommandHandler("settings", handlers.settings))
    
    application.add_handler(MessageHandler(filters.PHOTO, handlers.handle_photo))
    application.add_handler(MessageHandler(filters.VOICE, handlers.handle_voice))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_text)
    )
    
    application.add_handler(CallbackQueryHandler(handlers.handle_callback))
    
    # Start bot
    logger.info("Bot is running!")
    print("🥗 Nutrition Bot v2 запущен!")
    print("Нажми Ctrl+C для остановки")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
