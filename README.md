Telegram Hangman Bot

A simple Hangman game for Telegram with:
	•	✅ SQLite (игры не теряются при перезапуске)
	•	✅ /lang ru /lang en — выбор языка игроком
	•	✅ /stats — статистика побед/поражений

Установка и запуск
pip install -r requirements.txt
python bot.py

Создайте файл .env:
BOT_TOKEN=ваш_токен_из_BotFather

Команды
	•	/start — начать игру
	•	/lang ru | en — выбрать язык
	•	/stats — ваша статистика
	•	/help — подсказка
