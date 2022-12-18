from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.dispatcher.filters import Text
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import TOKEN_API
from sqlite import db_start, create_time


storage = MemoryStorage()
bot = Bot(TOKEN_API)
dp = Dispatcher(bot, storage=storage)
async def on_startup(_): await db_start()


class ProfileStatesGroup(StatesGroup):

    month = State()
    date = State()
    time = State()

def get_main_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add('Описание бота', 'Добавить свободное время', 'Записаться на приём', 'Ваши записи')
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
async def cm_make_app(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add(*[str(i) for i in range(1, 13)], 'Главное меню')
    await message.answer('Выберите месяц', reply_markup=kb)
    await ProfileStatesGroup.month.set()


@dp.message_handler(lambda message: 0 < int(message.text) > 12, state=ProfileStatesGroup.month)
async def check_month(message: types.Message):
    await message.reply('Выберите месяц из клавиатуры!')


@dp.message_handler(state=ProfileStatesGroup.month)
async def add_month(message: types.Message):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(*[f'{i}.{message.text if len(message.text) == 2 else f"0{message.text}"}' for i in range(1, 32)], 'Главное меню')
    await message.answer('Выберите удобную вам дату', reply_markup=kb)
    await ProfileStatesGroup.next()


@dp.message_handler(lambda message:
                    (0 < int(message.text.split('.')[0]) > 31 or 0 < int(message.text.split('.')[1]) > 12),
                    state=ProfileStatesGroup.date)
async def check_date(message: types.Message):
    await message.reply('Выберите дату из клавиатуры!')


@dp.message_handler(state=ProfileStatesGroup.date)
async def add_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['date'] = message.text if len(message.text) == 5 else f'0{message.text}'

    kb = ReplyKeyboardMarkup(resize_keyboard=True).add(*[f'{i}:00' for i in range(9, 20)], 'Главное меню')
    await message.answer('Теперь выберите время', reply_markup=kb)
    await ProfileStatesGroup.next()


@dp.message_handler(lambda message:
                    (0 < int(message.text.split(':')[0]) > 24 or 0 < int(message.text.split(':')[1]) > 60),
                    state=ProfileStatesGroup.time)
async def check_time(message: types.Message):
    await message.reply('Выберите время из клавиатуры!')


@dp.message_handler(state=ProfileStatesGroup.time)
async def add_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['time'] = message.text if len(message.text) == 5 else f'0{message.text}'

    kb = ReplyKeyboardMarkup(resize_keyboard=True).add('Главное меню', 'Добавить свободное время')
    await create_time(state)
    await message.answer('Время добавлено', reply_markup=kb)
    await state.finish()


@dp.message_handler(Text('Записаться на приём'))
async def cm_make_app(message: types.Message):
    await message.answer('Еще не готово')


@dp.message_handler(Text('Ваши записи'))
async def cm_update_app(message: types.Message):
    pass




if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
