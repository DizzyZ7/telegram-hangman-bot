import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from utils import load_words, choose_word, masked_word, is_won
import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_WRONG = 6

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот Виселица.\nКоманды:\n/new - начать новую игру\n/lang <en|ru> - выбрать язык слов\n/status - текущее состояние\n/giveup - сдаться\n/stats - статистика\n"
    )

async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args
    if not args:
        cur = db.get_lang(chat_id)
        await update.message.reply_text(f"Текущий язык: {cur}. Чтобы изменить: /lang en или /lang ru")
        return
    lang = args[0].lower()
    if lang not in ('en', 'ru'):
        await update.message.reply_text("Неправильный язык. Доступно: en, ru")
        return
    db.set_lang(chat_id, lang)
    await update.message.reply_text(f"Язык установлен: {lang}")

async def new_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    lang = db.get_lang(chat_id)
    words = load_words(lang)
    word = choose_word(words)
    guessed = ''
    wrong = 0
    db.save_game(chat_id, word, guessed, wrong, MAX_WRONG)
    await update.message.reply_text(f"Новая игра! Язык: {lang}\n{masked_word(word, set())}\nУгадайте букву или слово целиком.")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = db.load_game(chat_id)
    if not game:
        await update.message.reply_text("Нет активной игры. Напишите /new, чтобы начать.")
        return
    await update.message.reply_text(f"Слово:\n{masked_word(game['word'], game['guessed'])}\nОшибки: {game['wrong']}/{game['max_wrong']}")

async def give_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    game = db.load_game(chat_id)
    if not game:
        await update.message.reply_text("Нет активной игры.")
        return
    db.delete_game(chat_id)
    await update.message.reply_text(f"Вы сдались. Загаданное слово: {game['word']}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    wins, losses = db.get_stats(user.id)
    await update.message.reply_text(f"Статистика для {user.first_name}:\nПобед: {wins}\nПоражений: {losses}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    chat_id = update.effective_chat.id
    user = update.effective_user
    game = db.load_game(chat_id)
    if not game:
        await update.message.reply_text("Нет активной игры. Напишите /new чтобы начать.")
        return

    # полное слово
    if len(text) > 1:
        if text == game['word']:
            db.delete_game(chat_id)
            db.inc_win(user.id)
            await update.message.reply_text(f"Поздравляю! Вы угадали слово: {text}")
        else:
            game['wrong'] += 1
            if game['wrong'] >= game['max_wrong']:
                word = game['word']
                db.delete_game(chat_id)
                db.inc_loss(user.id)
                await update.message.reply_text(f"Вы проиграли. Слово было: {word}")
            else:
                db.save_game(chat_id, game['word'], ''.join(game['guessed']), game['wrong'], game['max_wrong'])
                await update.message.reply_text(f"Неправильно. Ошибки: {game['wrong']}/{game['max_wrong']}")
        return

    # буква
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
            db.delete_game(chat_id)
            db.inc_win(user.id)
            await update.message.reply_text(f"Поздравляю! Вы открыли слово: {game['word']}")
        else:
            db.save_game(chat_id, game['word'], ''.join(game['guessed']), game['wrong'], game['max_wrong'])
            await update.message.reply_text(masked_word(game['word'], game['guessed']))
    else:
        game['wrong'] += 1
        if game['wrong'] >= game['max_wrong']:
            word = game['word']
            db.delete_game(chat_id)
            db.inc_loss(user.id)
            await update.message.reply_text(f"Вы проиграли. Слово было: {word}")
        else:
            db.save_game(chat_id, game['word'], ''.join(game['guessed']), game['wrong'], game['max_wrong'])
            await update.message.reply_text(f"Нет такой буквы. Ошибки: {game['wrong']}/{game['max_wrong']}\n{masked_word(game['word'], game['guessed'])}")


def main():
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        print("Ошибка: установите переменную окружения TELEGRAM_TOKEN")
        return

    db.init_db()

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('new', new_game))
    app.add_handler(CommandHandler('status', status))
    app.add_handler(CommandHandler('giveup', give_up))
    app.add_handler(CommandHandler('stats', stats))
    app.add_handler(CommandHandler('lang', lang_cmd))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot started")
    app.run_polling()


if __name__ == '__main__':
    main()
