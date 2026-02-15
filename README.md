# Nutrition Bot v2

AI-powered Telegram bot for nutrition tracking with voice support, food photo analysis, and custom food database.

## Features

- 🎤 **Voice messages** — GROQ Whisper for transcription
- 📸 **Food photo analysis** — GPT-4 Vision
- 🍎 **Natural language** — "я съел 2 яйца и кофе"
- 💾 **Custom foods** — save your own meals
- 📊 **Daily summaries** — calories, protein, fat, carbs
- 🌍 **Multi-language** — Russian/English

## Tech Stack

- Python 3.11+
- python-telegram-bot
- OpenAI GPT-4.1 / GPT-4 Vision
- GROQ Whisper (free tier)
- SQLite

## Installation

```bash
cd nutrition_bot_v2
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your tokens
python3 main.py
```

## Environment Variables

```env
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk-...
```

## Commands

- `/start` — Begin
- `/settings` — Configure goals
- `/savefood` — Save custom food
- `/myfoods` — List saved foods
- `/summary` — Daily report
- `/help` — Help

Send voice or text to log food!
