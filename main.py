from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.dispatcher.filters import Text
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import TOKEN_API
from sqlite import create_time, get_time, get_date, db_start, free_check, delete_time

storage = MemoryStorage()
bot = Bot(TOKEN_API)
dp = Dispatcher(bot, storage=storage)


async def on_startup(_): await db_start()


class ProfileStatesGroup(StatesGroup):
    add_month = State()
    add_date = State()
    add_time = State()

    del_month = State()
    del_date = State()
    del_time = State()
    del_confirm = State()


def get_main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add('Описание бота', 'Добавить свободное время', 'Записаться на приём', 'Ваши записи', 'Удалить время')
    return kb


@dp.message_handler(commands='start')
async def cm_start(message: types.Message):
    await message.answer('Добро пожаловать в бота\nИспользуйте кнопки для продолжения', reply_markup=get_main_kb())


@dp.message_handler(Text('Главное меню'), state='*')
async def cm_exit(message: types.Message, state: FSMContext):
    if state is None:
        return

    await state.finish()
    await message.answer('Вы вышли в главное меню', reply_markup=get_main_kb())


@dp.message_handler(Text('Описание бота'))
async def cm_bot_description(message: types.Message):
    await message.answer('Этот бот был создан для...\nДля помощи обратитесь к ...')


# Block for adding new dates (for admins)
@dp.message_handler(Text('Добавить свободное время'))
async def cm_add_app(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add(*[str(i) for i in range(1, 13)], 'Главное меню')
    await message.answer('Выберите месяц', reply_markup=kb)
    await ProfileStatesGroup.add_month.set()


@dp.message_handler(lambda message: 0 < int(message.text) > 12, state=ProfileStatesGroup.add_month)
async def check_month(message: types.Message):
    await message.reply('Выберите месяц из клавиатуры!')


@dp.message_handler(state=ProfileStatesGroup.add_month)
async def add_month(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(*[f'{i}.{message.text if len(message.text) == 2 else f"0{message.text}"}' for i in range(1, 32)],
           'Главное меню')
    await message.answer('Выберите удобную вам дату', reply_markup=kb)
    await ProfileStatesGroup.next()


@dp.message_handler(lambda message:
                    (0 < int(message.text.split('.')[0]) > 31 or 0 < int(message.text.split('.')[1]) > 12),
                    state=ProfileStatesGroup.add_date)
async def check_date(message: types.Message):
    await message.reply('Выберите дату из клавиатуры!')


@dp.message_handler(state=ProfileStatesGroup.add_date)
async def add_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['date'] = message.text if len(message.text) == 5 else f'0{message.text}'

    kb = ReplyKeyboardMarkup(resize_keyboard=True).add(*[f'{i}:00' for i in range(9, 20)], 'Главное меню')
    await message.answer('Теперь выберите время', reply_markup=kb)
    await ProfileStatesGroup.next()


@dp.message_handler(lambda message:
                    (0 < int(message.text.split(':')[0]) > 24 or 0 < int(message.text.split(':')[1]) > 60),
                    state=ProfileStatesGroup.add_time)
async def check_time(message: types.Message):
    await message.reply('Выберите время из клавиатуры!')


@dp.message_handler(state=ProfileStatesGroup.add_time)
async def add_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['time'] = message.text if len(message.text) == 5 else f'0{message.text}'

    kb = ReplyKeyboardMarkup(resize_keyboard=True).add('Главное меню', 'Добавить свободное время')
    await create_time(state)
    await message.answer('Время добавлено', reply_markup=kb)
    await state.finish()


#  block for deleting appointments (for admins)
@dp.message_handler(Text('Удалить время'))
async def cm_delete_time(message: types.Message, state: FSMContext):
    months = set(i[3:] for i in await get_date())
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add(*sorted(months), 'Главное меню')
    await message.answer('Выберите месяц', reply_markup=kb)
    await ProfileStatesGroup.del_month.set()

    async with state.proxy() as data:
        data['months'] = months


@dp.message_handler(state=ProfileStatesGroup.del_month)
async def del_month(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        moths = data['months']
    if message.text in moths:
        dates = set(await get_date())
        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for date in sorted(dates):
            if date[3:] == message.text:
                kb.add(date)
        kb.add('Главное меню')
        await message.answer('Выберите дату', reply_markup=kb)
        await ProfileStatesGroup.next()
        async with state.proxy() as data:
            data['dates'] = dates
    else:
        await message.reply('Выберите месяц из клавиатуры!')


@dp.message_handler(state=ProfileStatesGroup.del_date)
async def del_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        dates = data['dates']
    if message.text in dates:
        times = await get_time(message.text)
        async with state.proxy() as data:
            data['date'] = message.text
            data['times'] = times
        kb = ReplyKeyboardMarkup(resize_keyboard=True).add(*sorted(times), 'Главное меню')
        await message.answer('Выберите время', reply_markup=kb)
        await ProfileStatesGroup.next()
    else:
        await message.reply('Выберите дату из клавиатуры!')


@dp.message_handler(state=ProfileStatesGroup.del_time)
async def del_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        times = data['times']
    if message.text in times:
        async with state.proxy() as data:
            data['time'] = message.text
        if await free_check(state) == 1:
            kb = ReplyKeyboardMarkup(resize_keyboard=True).add('Главное меню', 'Удалить время')
            await delete_time(state)
            await message.answer('Время было удалено', reply_markup=kb)
            await state.finish()
        elif await free_check(state) == 0:
            kb = ReplyKeyboardMarkup(resize_keyboard=True).add('Да', 'Главное меню')
            await message.answer('На это время есть запись, вы уверены в удалении?', reply_markup=kb)
            await ProfileStatesGroup.next()
    else:
        await message.reply('Выберите время из клавиатуры!')


@dp.message_handler(Text('Да'), state=ProfileStatesGroup.del_confirm)
async def del_time_confirm(message: types.Message, state: FSMContext):
    await delete_time(state)
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add('Главное меню', 'Удалить время')
    await message.answer('Время было удалено', reply_markup=kb)
    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
