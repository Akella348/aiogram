#Комментирую что добавил, а то большой уже код.
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from crud_functions import initiate_db, get_all_products, add_user, is_included  # Здесь прогружаем функции по инициализации базы данных и
# получению списка продуктов
import asyncio

api = ''
bot = Bot(token = api)
storage = MemoryStorage()
dp = Dispatcher(bot, storage = storage)

initiate_db()  # Инициализируем базу данных

kb = ReplyKeyboardMarkup(resize_keyboard=True)
calc_button = KeyboardButton(text= 'Рассчитать')
info_button = KeyboardButton(text= 'Информация')
buy_button = KeyboardButton(text='Купить')
register_button = KeyboardButton(text='Регистрация')  # Добавил кнопку регистрации
kb.add(register_button)  # Добавил кнопку регистрации
kb.row(calc_button, info_button)
kb.add(buy_button)

inline_kb = InlineKeyboardMarkup()
button_calories = InlineKeyboardButton('Рассчитать норму калорий', callback_data='calories')
button_formula = InlineKeyboardButton('Формула расчета', callback_data='formulas')
inline_kb.row(button_calories, button_formula)

product_kb = InlineKeyboardMarkup()
products = get_all_products()
for product in products:  # Тут обновил итерацию по полученному списку
    product_button = InlineKeyboardButton(f'{product[1]}', callback_data='product_buying')
    product_kb.add(product_button)

class UserState(StatesGroup):
    age = State()
    growth = State()
    weight = State()

class RegistrationState(StatesGroup):
    username = State()
    email = State()
    age = State()

@dp.message_handler(commands = ['start'])
async def start_message(message):
    await message.answer('Привет! Я бот помогающий твоему здоровью. Напишите Рассчитать, чтобы начать.', reply_markup=kb)

@dp.message_handler(lambda message: message.text == 'Регистрация')
async def sing_up(message: types.Message):
    await RegistrationState.username.set()
    await message.answer("Введите имя пользователя (только латинский алфавит):")

@dp.message_handler(state=RegistrationState.username)
async def set_username(message: types.Message, state: FSMContext):
    username = message.text
    if is_included(username):
        await message.answer("Пользователь существует, введите другое имя:")
    else:
        await state.update_data(username=username)
        await RegistrationState.email.set()
        await message.answer("Введите свой email:")

@dp.message_handler(state=RegistrationState.email)
async def set_email(message: types.Message, state: FSMContext):
    email = message.text
    await state.update_data(email=email)
    await RegistrationState.age.set()
    await message.answer("Введите свой возраст:")

@dp.message_handler(state=RegistrationState.age)
async def set_age(message: types.Message, state: FSMContext):
    age = message.text
    await state.update_data(age=age)
    data = await state.get_data()
    add_user(data['username'], data['email'], age)
    await message.answer("Регистрация завершена! Вы можете теперь войти в аккаунт.")
    await state.finish()

@dp.message_handler(lambda message: message.text == 'Рассчитать')
async def main_menu(message: types.Message):
    await message.answer('Выберите опцию:', reply_markup=inline_kb)

@dp.message_handler(lambda message: message.text == 'Купить')
async def get_buying_list(message: types.Message):
    products = get_all_products()  # Получаем список продуктов
    for product in products:  # Итерируем по списку продуктов и добавляем описание по свойствам объекта
        product_description = f'Название: {product[1]} | Описание: {product[2]} | Цена: {product[3]}'
        with open(f'{product[1]}.jpg', 'rb') as img:  # По имени объекта назван файл поэтому меняем под него
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