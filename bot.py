import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import matplotlib.pyplot as plt
import io
import os

# Токен для доступа к API Telegram получаем из переменной окружения
API_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not API_TOKEN:
    raise ValueError("Пожалуйста, установите переменную окружения TELEGRAM_BOT_TOKEN")

# Инициализация бота
bot = telebot.TeleBot(API_TOKEN)

# Словари с данными для математической модели
WIND_SPEEDS = {
    'Актау': 7,
    'Жанаозен': 5,
    'Бейнеу': 6,
    'Шетпе': 4
}

POLLUTION_COEFFICIENTS = {
    'Тяжелые металлы': 1.5,
    'Нефть': 1.2
}

# Краткая справка о вреде тяжелых металлов
INFO_TEXT = (
    "ℹ️ *Справка о вреде загрязнений:*\n\n"
    "Тяжелые металлы (свинец, кадмий) и нефть наносят непоправимый ущерб почве "
    "Мангистауской области. Они уничтожают микрофлору, делая землю бесплодной. "
    "В условиях сильных ветров загрязненная пыль разносится на огромные расстояния, "
    "ускоряя процессы опустынивания."
)

# Хранилище временных данных пользователей (для простоты используем словарь)
user_data = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команды /start и /help."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for region in WIND_SPEEDS.keys():
        markup.add(KeyboardButton(region))

    bot.send_message(
        message.chat.id,
        "👋 Привет! Я бот для экологического мониторинга опустынивания в Мангистауской области.\n"
        "Пожалуйста, выберите район для анализа:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text in WIND_SPEEDS.keys())
def process_region_step(message):
    """Обработчик выбора района."""
    chat_id = message.chat.id
    region = message.text
    user_data[chat_id] = {'region': region}

    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for pollution in POLLUTION_COEFFICIENTS.keys():
        markup.add(KeyboardButton(pollution))

    bot.send_message(
        chat_id,
        f"Вы выбрали {region}. Теперь выберите тип загрязнения:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text in POLLUTION_COEFFICIENTS.keys())
def process_pollution_step(message):
    """Обработчик выбора типа загрязнения."""
    chat_id = message.chat.id
    pollution = message.text

    if chat_id not in user_data or 'region' not in user_data[chat_id]:
        bot.send_message(chat_id, "Пожалуйста, начните сначала с команды /start")
        return

    user_data[chat_id]['pollution'] = pollution

    # Убираем клавиатуру при запросе площади
    bot.send_message(
        chat_id,
        "Введите начальную площадь загрязнения (в гектарах, например, 10):",
        reply_markup=telebot.types.ReplyKeyboardRemove()
    )

    bot.register_next_step_handler(message, process_area_step)

def calculate_degradation(area, wind_speed, pollution_coef, years):
    """
    Математическая модель расчета площади деградации.
    Формула: S = S0 * (1 + (v * k / 100)) ^ t
    где:
    S0 - начальная площадь
    v - скорость ветра
    k - коэффициент загрязнения
    t - годы
    """
    # Упрощенная модель для демонстрации.  Зона расширяется пропорционально скорости ветра и коэф. загрязнения.
    # В реальности модель может быть сложнее (например, учитывая радиус).
    # Здесь мы считаем прирост площади в гектарах.
    growth_rate = 1 + (wind_speed * pollution_coef * 0.05)
    return area * (growth_rate ** years)

def process_area_step(message):
    """Обработчик ввода площади загрязнения и генерация отчета."""
    chat_id = message.chat.id
    try:
        area_str = message.text.replace(',', '.')
        area = float(area_str)
        if area <= 0:
            raise ValueError("Площадь должна быть больше нуля.")
    except ValueError:
        bot.send_message(chat_id, "Ошибка! Пожалуйста, введите корректное число для площади.")
        bot.register_next_step_handler(message, process_area_step)
        return

    data = user_data.get(chat_id)
    if not data:
        bot.send_message(chat_id, "Произошла ошибка. Начните сначала: /start")
        return

    region = data['region']
    pollution = data['pollution']
    wind_speed = WIND_SPEEDS[region]
    pollution_coef = POLLUTION_COEFFICIENTS[pollution]

    # Годы для прогноза
    years = [0, 5, 10, 20]

    # Расчет площади для каждого года
    areas = [calculate_degradation(area, wind_speed, pollution_coef, y) for y in years]

    # Текстовый отчет
    report = (
        f"📊 *Прогноз опустынивания для района {region}*\n"
        f"Тип загрязнения: {pollution}\n"
        f"Начальная площадь: {area} га\n\n"
        f"Прогнозируемая площадь деградации:\n"
        f"• Через 5 лет: {areas[1]:.2f} га\n"
        f"• Через 10 лет: {areas[2]:.2f} га\n"
        f"• Через 20 лет: {areas[3]:.2f} га\n\n"
    )

    report += INFO_TEXT

    # Генерация графика
    plt.figure(figsize=(10, 6))
    plt.plot(years, areas, marker='o', linestyle='-', color='red', linewidth=2, markersize=8)

    # Настройка графика
    plt.title(f'Прогноз деградации почвы: {region}', fontsize=14, fontweight='bold')
    plt.xlabel('Годы', fontsize=12)
    plt.ylabel('Площадь деградации (га)', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(years)

    # Сохранение графика в буфер памяти (чтобы не создавать файл на диске)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()

    # Отправка отчета и графика пользователю
    bot.send_message(chat_id, report, parse_mode='Markdown')
    bot.send_photo(chat_id, buf, caption="График прогноза деградации почвы")

    # Предлагаем начать заново
    bot.send_message(chat_id, "Хотите проверить другие параметры? Нажмите /start")

if __name__ == '__main__':
    bot.infinity_polling()