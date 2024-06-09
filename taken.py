from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import telegram.ext

from connect import DB
from log_for_bot import logger


db = DB()

if db.connect():
    conn = db.conn
    cursor = db.cursor


def taken(update, context):
    if update.callback_query:
        update = update.callback_query
    user_id = update.message.chat_id
    cursor.execute(
        'SELECT * FROM pills_reminder WHERE user_id=?', 
        (user_id,)
    )
    rows = cursor.fetchall()
    
    if not rows:
        update.message.reply_text('Sorry, you dont have pills!')
        return telegram.ext.ConversationHandler.END
    
    update.message.reply_text('This is your pills')
    
    buttons = list()

    for row in rows:
        time = row[1]
        name = row[2]
        message = f'{name} - {time} Taken'
        buttons.append([InlineKeyboardButton(message.rstrip(' Taken'), callback_data=message)])

    reply_markup = InlineKeyboardMarkup(buttons)

    update.message.reply_text('Choose a pill:', reply_markup=reply_markup)


def taken_pill(update, context):
    current_pill, current_time = update.data.rstrip(' Taken').split(' - ')
    user_id = update.message.chat_id
    cursor.execute(
        'UPDATE pills_reminder SET taken=1 WHERE user_id=? AND name=? AND time=?', 
        (user_id, current_pill, current_time)
    )
        
    conn.commit()

    update.message.reply_text(f'Pill {current_pill} taken!')

    logger.info(
        f'Пользователь {user_id} принял таблетку {current_pill} в {current_time}'
    )

    return telegram.ext.ConversationHandler.END


pill_command_taken_handler = telegram.ext.CommandHandler('taken', taken)

pill_taken_handler = telegram.ext.CallbackQueryHandler(pattern='taken_pill', callback=taken)