import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from utils import load_words, choose_word, masked_word, is_won

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Структура хранения игр в памяти: chat_id -> game_state
# game_state: { 'word': str, 'guessed': set, 'wrong': int, 'max_wrong': int }
GAMES = {}

WORDS = load_words()
MAX_WRONG = 6

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот Виселица. Напиши /new чтобы начать новую игру.")

async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    word = choose_word(WORDS)
    GAMES[chat_id] = { 'word': word, 'guessed': set(), 'wrong': 0, 'max_wrong': MAX_WRONG }
    await update.message.reply_text(f"Новая игра! Слово:\n{masked_word(word, set())}\nУгадайте букву или слово целиком.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = GAMES.get(chat_id)
    if not game:
        await update.message.reply_text("Нет активной игры. Напишите /new чтобы начать.")
        return
    await update.message.reply_text(f"Слово:\n{masked_word(game['word'], game['guessed'])}\nОшибки: {game['wrong']}/{game['max_wrong']}")

async def give_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = GAMES.pop(chat_id, None)
    if not game:
        await update.message.reply_text("Нет активной игры.")
    else:
        await update.message.reply_text(f"Вы сдались. Загаданное слово: {game['word']}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    chat_id = update.effective_chat.id
    game = GAMES.get(chat_id)
    if not game:
        await update.message.reply_text("Нет активной игры. Напишите /new чтобы начать.")
        return

    # угадывание целого слова
    if len(text) > 1:
        if text == game['word']:
            GAMES.pop(chat_id, None)
            await update.message.reply_text(f"Поздравляю! Вы угадали слово: {text}")
        else:
            game['wrong'] += 1
            if game['wrong'] >= game['max_wrong']:
                word = game['word']
                GAMES.pop(chat_id, None)
                await update.message.reply_text(f"Вы проиграли. Слово было: {word}")
            else:
                await update.message.reply_text(f"Неправильно. Ошибки: {game['wrong']}/{game['max_wrong']}")
        return

    # угадывание буквы
    ch = text[0]
    if not ch.isalpha():
        await update.message.reply_text("Пожалуйста, отправляйте только буквы или слова.")
        return

    if ch in game['guessed']:
        await update.message.reply_text(f"Вы уже называли '{ch}'.\n{masked_word(game['word'], game['guessed'])}")
        return

    if ch in game['word']:
        game['guessed'].add(ch)
        if is_won(game['word'], game['guessed']):
            GAMES.pop(chat_id, None)
            await update.message.reply_text(f"Поздравляю! Вы открыли слово: {game['word']}")
        else:
            await update.message.reply_text(masked_word(game['word'], game['guessed']))
    else:
        game['wrong'] += 1
        if game['wrong'] >= game['max_wrong']:
            word = game['word']
            GAMES.pop(chat_id, None)
            await update.message.reply_text(f"Вы проиграли. Слово было: {word}")
        else:
            await update.message.reply_text(f"Нет такой буквы. Ошибки: {game['wrong']}/{game['max_wrong']}\n{masked_word(game['word'], game['guessed'])}")


def main():
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("Ошибка: установите переменную окружения TELEGRAM_TOKEN")
        return

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('new', new_game))
    app.add_handler(CommandHandler('status', status))
    app.add_handler(CommandHandler('giveup', give_up))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started")
    app.run_polling()


if __name__ == '__main__':
    main()
