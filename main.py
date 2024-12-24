import telebot
import aiohttp
import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton


# Вставьте ваши токены
API_TOKEN = '7940620006:AAHfR3-PiN3M6ZmaK027KHGikhjMa1FbgJA'
WEATHER_API_KEY = '5fadc378bc8b4ecea64105224242412'
WEATHER_API_URL = 'http://api.weatherapi.com/v1/current.json'

bot = AsyncTeleBot(API_TOKEN)

# Класс для управления состояниями пользователей
class UserStateManager:
    def __init__(self):
        self.states = {}
        self.tracked_cities = []

    def set_state(self, chat_id, state):
        self.states[chat_id] = state

    def get_state(self, chat_id):
        return self.states.get(chat_id, 'MAIN_MENU')

    def add_city(self, city):
        if city not in self.tracked_cities:
            self.tracked_cities.append(city)
            return True
        return False

    def remove_city(self, city):
        if city in self.tracked_cities:
            self.tracked_cities.remove(city)
            return True
        return False

    def get_tracked_cities(self):
        return self.tracked_cities

# Создаем экземпляр менеджера состояний
user_state_manager = UserStateManager()

# Клавиатура для главного меню
main_menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu_keyboard.add(KeyboardButton('/add'))
main_menu_keyboard.add(KeyboardButton('/list'))
main_menu_keyboard.add(KeyboardButton('/weather'))
main_menu_keyboard.add(KeyboardButton('/remove'))

# Обработчик команды /start
@bot.message_handler(commands=['start'])
async def send_welcome(message):
    user_state_manager.set_state(message.chat.id, 'MAIN_MENU')
    await bot.send_message(message.chat.id, "Привет! Введите название города, чтобы узнать погоду.\nИспользуйте /add, "
                                            "чтобы добавить город в список отслеживаемых.\nИспользуйте /list, "
                                            "чтобы увидеть список отслеживаемых городов.\nИспользуйте /weather, "
                                            "чтобы узнать погоду во всех отслеживаемых городах.\nИспользуйте /remove, "
                                            "чтобы удалить город из списка отслеживаемых.",
                           reply_markup=main_menu_keyboard)

# Обработчик команды /add
@bot.message_handler(commands=['add'])
async def add_city_prompt(message):
    user_state_manager.set_state(message.chat.id, 'ADD_CITY')
    await bot.send_message(message.chat.id, "Введите название города, который хотите добавить в список отслеживаемых:")

# Обработчик команды /list
@bot.message_handler(commands=['list'])
async def list_cities(message):
    tracked_cities = user_state_manager.get_tracked_cities()
    if tracked_cities:
        cities_list = "\n".join(tracked_cities)
        await bot.send_message(message.chat.id, f"Отслеживаемые города:\n{cities_list}")
    else:
        await bot.send_message(message.chat.id, "Список отслеживаемых городов пуст.")

# Обработчик команды /weather
@bot.message_handler(commands=['weather'])
async def get_weather_for_all_cities(message):
    tracked_cities = user_state_manager.get_tracked_cities()
    if not tracked_cities:
        await bot.send_message(message.chat.id, "Список отслеживаемых городов пуст. Добавьте города с помощью команды /add.")
        return

    weather_report = []
    async with aiohttp.ClientSession() as session:
        for city in tracked_cities:
            async with session.get(WEATHER_API_URL, params={'q': city, 'key': WEATHER_API_KEY}) as response:
                data = await response.json()
                if response.status == 200:
                    weather = data['current']['condition']['text']
                    temp = data['current']['temp_c']
                    weather_report.append(f"Погода в {city}: {weather}, температура: {temp}°C")
                else:
                    weather_report.append(f"Не удалось получить данные о погоде для города {city}.")

    await bot.send_message(message.chat.id, "\n".join(weather_report))

# Обработчик команды /remove
@bot.message_handler(commands=['remove'])
async def remove_city_prompt(message):
    user_state_manager.set_state(message.chat.id, 'REMOVE_CITY')
    await bot.send_message(message.chat.id, "Введите название города, который хотите удалить из списка отслеживаемых:")

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
async def handle_messages(message):
    chat_id = message.chat.id
    state = user_state_manager.get_state(chat_id)

    if state == 'ADD_CITY':
        city = message.text
        if user_state_manager.add_city(city):
            await bot.send_message(chat_id, f"Город {city} добавлен в список отслеживаемых.")
        else:
            await bot.send_message(chat_id, f"Город {city} уже в списке отслеживаемых.")
        user_state_manager.set_state(chat_id, 'MAIN_MENU')

    elif state == 'REMOVE_CITY':
        city = message.text
        if user_state_manager.remove_city(city):
            await bot.send_message(chat_id, f"Город {city} удален из списка отслеживаемых.")
        else:
            await bot.send_message(chat_id, f"Город {city} не найден в списке отслеживаемых.")
        user_state_manager.set_state(chat_id, 'MAIN_MENU')

    else:
        city = message.text
        async with aiohttp.ClientSession() as session:
            async with session.get(WEATHER_API_URL, params={'q': city, 'key': WEATHER_API_KEY}) as response:
                data = await response.json()
                if response.status == 200:
                    weather = data['current']['condition']['text']
                    temp = data['current']['temp_c']
                    await bot.send_message(chat_id, f"Погода в {city}: {weather}, температура: {temp}°C")
                else:
                    await bot.send_message(chat_id, "Не удалось получить данные о погоде. Попробуйте другой город.")

# Запуск бота
if __name__ == '__main__':
    asyncio.run(bot.polling())