import logging

logging.basicConfig(
        filename='bot.log',
        encoding='utf-8',
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
logger = logging.getLogger(__name__)


def error_handler(update, context):
    logger.error(f'Ошибка в обработчике {update}: {context.error}')