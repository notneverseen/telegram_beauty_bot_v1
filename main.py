import asyncio
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback, get_user_locale

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from states import BookingStates
from keyboards import get_services_keyboard, get_time_keyboard, get_confirm_keyboard

from dotenv import load_dotenv, find_dotenv
from datetime import datetime
import logging
import aiosqlite
import os


load_dotenv(find_dotenv())
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
router = Router()
dp = Dispatcher(storage=storage)
dp.include_router(router)

logging.basicConfig(level=logging.INFO)


async def get_connect_and_add_users_to_db(telegram_id: int, username: str, fullname: str):
    try:
        async with aiosqlite.connect('tg_users.db') as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    username TEXT,
                    fullname TEXT
                )
            ''')

            await db.execute('INSERT OR IGNORE INTO users (telegram_id, username, fullname) VALUES (?, ?, ?)', (telegram_id, username, fullname))
            await db.commit()
    
    except Exception as e:
        logging.error(e)

        
async def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text='Записаться на приём', callback_data='order')
    builder.button(text='Наши услуги', callback_data='services')
    builder.button(text='Контакты', callback_data='contacts')
    builder.button(text='Админ панель', callback_data='admin')

    builder.adjust(1)
    return builder.as_markup()


@dp.message(CommandStart())
async def start_command(message: Message):
    await message.answer(
        f'Здравствуйте {message.from_user.full_name}!\n'
        'Это бот для записи на маникюр.',
        reply_markup=await get_main_keyboard())
    
    telegram_id = message.from_user.id
    username = message.from_user.username
    fullname = message.from_user.full_name
    await get_connect_and_add_users_to_db(telegram_id, username, fullname)


@router.callback_query(F.data == 'order')
async def start_booking_order(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        'Выберите услугу:',
        reply_markup=await get_services_keyboard()
    )
    await state.set_state(BookingStates.choosing_service)
    await callback.answer()


@router.callback_query(BookingStates.choosing_service, F.data.startswith('service_'))
async def process_service(callback: CallbackQuery, state: FSMContext):
    service = callback.data.split('_')[1]
    await state.update_data(service=service)
    await callback.message.edit_text(
        'Выберите дату:',
        reply_markup=await SimpleCalendar(locale=await get_user_locale(callback.from_user)).start_calendar()
    )
    await state.set_state(BookingStates.choosing_service)
    await callback.answer()


@router.callback_query(BookingStates.choosing_date, SimpleCalendarCallback.filter())
async def process_date(callback: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    selected, date=await SimpleCalendar(locale=await get_user_locale(callback.from_user)).process_selection(callback, callback_data)
    if selected:
        date_str = date.strftime('%Y-%m-%d') # format iso for db
        date_display = date.strftime('%d.%m.%Y') # format for display to users
        await state.update_data(date=date_str)
        await callback.message.edit_text(
            f'Выбрана дата: {date_display}\nТеперь выберите время:',
            reply_markup=await get_time_keyboard()
        )
        await state.set_state(BookingStates.choosing_time)
    await callback.answer()


@router.callback_query(BookingStates.choosing_time, F.data.startswith('time_'))
async def process_time(callback: CallbackQuery, state: FSMContext):
    time = callback.data.split('_')[1]
    if len(time) == 3: time_formatted = f'{time[0]}:{time[1:]}' # 900 - 9:00
    elif len(time) == 4: time_formatted = f'{time[:2]}:{time[2:]}' # 1000 - 10:00
    await state.update_data(service=time_formatted)
    data = await state.get_data()
    await callback.message.edit_text(
        f'Проверьте данные:\n'
        f'Услуга: {data['service']}\n'
        f'Дата: {data['date']}\n'
        f'Время: {time_formatted}\n\n'
        'Все верно?',
        reply_markup=await get_confirm_keyboard()
    )
    await state.set_state(BookingStates.confirming)
    await callback.answer()


@dp.callback_query(F.data == 'admin')
async def admin_callback(callback: CallbackQuery):
    admin_ids = [8628523762]
    if callback.from_user.id in admin_ids:
        await callback.message.answer('admin is valid!')
    else:
        await callback.message.answer('admin is invalid!')
    await callback.answer()


@dp.callback_query(F.data == 'services')
async def services_callback(callback: CallbackQuery):
    text = ('services')
    await callback.message.answer(text)
    await callback.answer()


@dp.callback_query(F.data == 'contacts')
async def contact_callback(callback: CallbackQuery):
    text = ('contacts')
    await callback.message.answer(text)
    await callback.answer()


async def main():
    logging.info('The bot is working')
    await dp.start_polling(bot) # run_polling


if __name__ == "__main__":
    asyncio.run(main())