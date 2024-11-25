from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

api = ''
bot = Bot(token = api)
storage = MemoryStorage()
dp = Dispatcher(bot, storage = storage)

kb = ReplyKeyboardMarkup(resize_keyboard=True)
calc_button = KeyboardButton(text= 'Рассчитать')
info_button = KeyboardButton(text= 'Информация')
buy_button = KeyboardButton(text='Купить')
kb.row(calc_button, info_button)
kb.add(buy_button)

inline_kb = InlineKeyboardMarkup()
button_calories = InlineKeyboardButton('Рассчитать норму калорий', callback_data='calories')
button_formula = InlineKeyboardButton('Формула расчета', callback_data='formulas')
inline_kb.row(button_calories, button_formula)

product_kb = InlineKeyboardMarkup()
for i in range(1, 6):
    product_button = InlineKeyboardButton(f'Product{i}', callback_data='product_buying')
    product_kb.add(product_button)

class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()

@dp.message_handler(commands = ['start'])
async def start_message(message):
    await message.answer('Привет! Я бот помогающий твоему здоровью. Напишите Рассчитать, чтобы начать.', reply_markup=kb)

@dp.message_handler(lambda message: message.text == 'Рассчитать')
async def main_menu(message: types.Message):
    await message.answer('Выберите опцию:', reply_markup=inline_kb)

@dp.message_handler(lambda message: message.text == 'Купить')
async def get_buying_list(message: types.Message):
    products_info = []
    for i in range(1,6):
        product_description = f'Название: Product{i} | Описание: описание {i} | Цена: {i * 100}'
        products_info.append(product_description)
        with open(f'Product{i}.jpg', 'rb') as img:
            await message.answer_photo(img, caption=product_description)
    await message.answer('Выберите продукт', reply_markup=product_kb)

@dp.callback_query_handler(lambda call: call.data == 'product_buying')
async def send_confirm_message(call: types.CallbackQuery):
    await call.message.answer("Вы успешно приобрели продукт!")
    await call.answer()

@dp.callback_query_handler(lambda call: call.data == 'calories')
async def set_age(call: types.CallbackQuery):
    await UserState.age.set()
    await call.message.answer('Введите свой возраст:')

@dp.callback_query_handler(lambda call: call.data == 'formulas')
async def get_formulas(call: types.CallbackQuery):
    await call.message.answer('Формула Миффлина-Сан Жеора:\nMifflin-St Jeor Equation: \n'
                              'Для мужчин:\nBMR = 10 * вес (кг) + 6.25 * рост (см) - 5 * возраст (лет) + 5\n'
                              'Для женщин:\nBMR = 10 * вес (кг) + 6.25 * рост (см) - 5 * возраст (лет) - 161')
    await call.answer()


@dp.message_handler(state=UserState.age)
async def set_growth(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)
    await UserState.growth.set()
    await message.answer('Введите свой рост:')

@dp.message_handler(state=UserState.growth)
async def set_weight(message: types.Message, state: FSMContext):
    await state.update_data(growth=message.text)
    await UserState.weight.set()
    await message.answer('Введите свой вес:')

@dp.message_handler(state=UserState.weight)
async def send_calories(message: types.Message, state: FSMContext):
    await state.update_data(weight=message.text)
    data = await state.get_data()
    calories = 10 * int(data['weight']) + 6.25 * int(data['growth']) - 5 * int(data['age']) + 5
    await message.answer(f'Ваша норма калорий: {calories}')
    await state.finish()

@dp.message_handler()
async def all_message(message):
    await message.answer('Введите команду /start, чтобы начать общение.')
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)