from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


async def get_services_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text='Маникюр', callback_data='service_manicure')
    builder.button(text='Педикюр', callback_data='service_pedicure')
    builder.button(text='Маникюр + Педикюр', callback_data='service_manicure+pedicure')
    builder.button(text='Другие услуги', callback_data='service_another')
    builder.button(text='Назад', callback_data='back_to_menu')
    builder.adjust(1)
    return builder.as_markup()


async def get_time_keyboard():
    builder = InlineKeyboardBuilder()
    slots = ['9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00']
    for slot in slots:
        callback_data = f'time_{slot.replace(':', '')}'
        builder.button(text=slot, callback_data=callback_data)
    builder.button(text='Назад', callback_data='back_to_dates')
    builder.adjust(4, 4, 1)
    return builder.as_markup()


async def get_confirm_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text='Подтвердить', callback_data='confirm_yes')
    builder.button(text='Отменить', callback_data='confirm_no')
    builder.adjust(1)
    return builder.as_markup()
