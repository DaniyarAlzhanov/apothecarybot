import telegram.ext

from connect import DB
from log_for_bot import logger
from validators import validate_time


db = DB()

if db.connect():
    conn = db.conn
    cursor = db.cursor


def new_reminder(update, context):
    if update.callback_query:
        update = update.callback_query
    update.message.reply_text(
        'Which pill shall i remind you of?\n'
    )
    return 1


def get_name(update, context):
    global current_pill
    current_pill = update.message.text
    
    if len(current_pill.split()) > 1:
        update.message.reply_text(
            "Name of the pill shouldn't containt blanks."
        )

        logger.error(
            f'Пользователь {update.message.text} добавил пробел в название таблетки'
        )

        return telegram.ext.ConversationHandler.END
    
    update.message.reply_text('When are you planning to take pill HH:MM?')
    return 2


def get_time(update, context):
    global current_time
    global cursor

    current_time = update.message.text
    user_id = update.message.chat_id

    if not validate_time(current_time):
        update.message.reply_text('Bad form of time!')
        logger.error(
            f'Пользователь {update.message.text} ввёл некорректный формат времени'
        )
        return telegram.ext.ConversationHandler.END

    cursor.execute(
        'SELECT * FROM user WHERE id=?', (user_id,)
    )

    if not cursor.fetchone():
        cursor.execute('INSERT INTO user (id) VALUES (?)', (user_id,))
    
    cursor.execute(
        'INSERT INTO pills_reminder (user_id, name, time) VALUES (?, ?, ?)',
        (user_id, current_pill, current_time)
    )

    conn.commit()

    update.message.reply_text('I will remind you!')

    logger.info(
        f'Пользователь {user_id} успешно добавил таблетку {current_pill}'
    )

    return telegram.ext.ConversationHandler.END


def cancel():
    return telegram.ext.ConversationHandler.END


pill_reminder_handler = telegram.ext.ConversationHandler(
    entry_points=[
        telegram.ext.CommandHandler('new', new_reminder),
        telegram.ext.CallbackQueryHandler(pattern='add_pill', callback=new_reminder)
    ],
    states={
        1: [telegram.ext.MessageHandler(telegram.ext.Filters.text, get_name)],
        2: [telegram.ext.MessageHandler(telegram.ext.Filters.text, get_time)]
    },
    fallbacks=[telegram.ext.CommandHandler('cancel', cancel)]
)
