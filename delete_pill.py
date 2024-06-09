from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import telegram.ext

from connect import DB
from log_for_bot import logger


db = DB()

if db.connect():
    conn = db.conn
    cursor = db.cursor


def new_delete(update, context):
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

    buttons = list()

    for row in rows:
        time = row[1]
        name = row[2]
        message = f'{name} - {time} Delete'
        buttons.append([InlineKeyboardButton(message.rstrip(' Delete'), callback_data=message)])

    reply_markup = InlineKeyboardMarkup(buttons)

    update.message.reply_text('Choose a pill to delete:', reply_markup=reply_markup)


def delete_pill(update, context):
    current_pill, current_time = update.data.rstrip(' Delete').split(' - ')
    user_id = update.message.chat_id
    cursor.execute(
        'SELECT * FROM pills_reminder WHERE user_id=? AND name=? AND time=?', 
        (user_id, current_pill, current_time)
    )
    
    if not cursor.fetchone():
        update.message.reply_text('Sorry, this pill doesnt exist!')
        return telegram.ext.ConversationHandler.END

    cursor.execute(
        'DELETE FROM pills_reminder WHERE user_id=? AND name=? AND time=?', 
        (user_id, current_pill, current_time)
    )

    conn.commit()

    update.message.reply_text(f'Pill {current_pill} removed!')

    logger.info(
        f'Пользователь {user_id} удалил таблетку {current_pill}'
    )
    
    return telegram.ext.ConversationHandler.END


pill_command_delete_handler = telegram.ext.CommandHandler('delete', new_delete)

pill_delete_handler = telegram.ext.CallbackQueryHandler(pattern='delete_pill', callback=new_delete) 
