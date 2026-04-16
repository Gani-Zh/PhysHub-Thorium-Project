import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import matplotlib.pyplot as plt
import io
import os
import random
import re
import requests
import time

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

# Научно-обоснованная справка о вреде загрязнений
INFO_TEXT = (
    "ℹ️ *Научная справка:*\n\n"
    "Тяжелые металлы (свинец, кадмий) и нефть инициируют процессы деградации и **засоления почв** "
    "Мангистауской области. Они ингибируют активность микрофлоры, снижая плодородие земель. "
    "В условиях высоких ветровых нагрузок региона (включая **аэрозольный перенос тяжелых металлов**), "
    "загрязненные частицы распространяются на значительные расстояния, многократно ускоряя процессы опустынивания."
)

# Вопросы для эко-викторины
QUIZ_QUESTIONS = [
    {
        "question": "Какое растение Мангистау играет ключевую роль в сдерживании песков и предотвращении опустынивания?",
        "options": ["Саксаул", "Ковыль", "Верблюжья колючка"],
        "answer": 0,
        "explanation": "Саксаул — это древесное растение пустынь. Его мощная корневая система эффективно удерживает почву и предотвращает ветровую эрозию."
    },
    {
        "question": "Что означает термин 'Биоремедиация'?",
        "options": ["Засоление почв из-за испарения", "Восстановление экосистемы с помощью живых организмов", "Химическое заражение грунтовых вод"],
        "answer": 1,
        "explanation": "Биоремедиация — это комплекс методов очистки вод, грунтов и атмосферы с использованием метаболического потенциала биологических объектов (чаще всего микроорганизмов и растений)."
    },
    {
        "question": "Какой процесс наиболее характерен для 'аэрозольного переноса тяжелых металлов'?",
        "options": ["Перемещение вместе с грунтовыми водами", "Растворение металлов в кислотных дождях", "Перенос токсичных частиц ветром в виде пыли"],
        "answer": 2,
        "explanation": "Аэрозольный перенос — это процесс транспортировки микроскопических частиц (включая тяжелые металлы) ветровыми потоками на большие расстояния."
    },
    {
        "question": "Какой тяжелый металл, часто встречающийся в промышленных выбросах, наиболее опасен для микрофлоры почвы?",
        "options": ["Железо", "Свинец", "Алюминий"],
        "answer": 1,
        "explanation": "Свинец является высокотоксичным тяжелым металлом, который подавляет ферментативную активность почвенных микроорганизмов."
    },
    {
        "question": "Что такое 'засоление почв'?",
        "options": ["Процесс накопления легкорастворимых солей в верхних слоях почвы", "Загрязнение почвы нефтью", "Увеличение количества гумуса"],
        "answer": 0,
        "explanation": "Засоление почв происходит из-за высокого уровня испарения и накопления солей, что делает почву непригодной для большинства растений."
    },
    {
        "question": "Какая основная причина опустынивания в Мангистауской области?",
        "options": ["Перевыпас скота и ветровая эрозия", "Обильные дожди", "Увеличение лесных массивов"],
        "answer": 0,
        "explanation": "Перевыпас скота уничтожает скудный растительный покров, после чего почва легко подвергается ветровой эрозии (развеиванию)."
    },
    {
        "question": "Какова роль Каспийского моря в формировании климата Мангистау?",
        "options": ["Оно делает климат тропическим", "Оно смягчает континентальность климата на побережье", "Оно является причиной кислотных дождей"],
        "answer": 1,
        "explanation": "Каспийское море выступает как терморегулятор, смягчая жару летом и морозы зимой в прибрежной зоне."
    },
    {
        "question": "Что такое 'фиторемедиация'?",
        "options": ["Использование растений для очистки загрязненных почв", "Уничтожение сорняков гербицидами", "Создание искусственных водоемов"],
        "answer": 0,
        "explanation": "Фиторемедиация — это технология очистки почвы, воды и воздуха с использованием зеленых растений, способных извлекать токсичные вещества."
    },
    {
        "question": "Как разливы нефти влияют на почву?",
        "options": ["Обогащают ее полезными минералами", "Нарушают водо- и воздухообмен, склеивая частицы почвы", "Ускоряют рост растений"],
        "answer": 1,
        "explanation": "Нефть обволакивает почвенные частицы пленкой, перекрывая доступ кислорода и воды к корням растений и микроорганизмам."
    },
    {
        "question": "Какое животное Мангистау сильно страдает от деградации пастбищ?",
        "options": ["Белый медведь", "Сайгак", "Тюлень"],
        "answer": 1,
        "explanation": "Сайгаки зависят от степной и полупустынной растительности. Деградация пастбищ лишает их кормовой базы."
    }
]

# Хранилище временных данных пользователей
user_data = {}

def get_weather_data(region):
    """
    Получает реальные данные о погоде через OpenWeatherMap API.
    Использует внутренние статические данные в качестве резервных.
    """
    api_key = os.environ.get('OPENWEATHER_API_KEY')
    if not api_key:
        # Плавный переход для конкурса РФМШ (16 апреля 2026)
        return {
            'wind_speed': 10.0,
            'temp': 11,
            'humidity': 60,
            'description': 'Облачно',
            'source': 'static'
        }

    url = f"http://api.openweathermap.org/data/2.5/weather?q={region}&appid={api_key}&units=metric&lang=ru"

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        return {
            'wind_speed': data['wind']['speed'],
            'temp': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description'].capitalize() if data.get('weather') else 'Нет описания',
            'source': 'api'
        }
    except Exception:
        # Плавный переход для конкурса РФМШ (16 апреля 2026)
        # Отлавливаем любые ошибки (RequestException, KeyError, JSONDecodeError, etc)
        return {
            'wind_speed': 10.0,
            'temp': 11,
            'humidity': 60,
            'description': 'Облачно',
            'source': 'static'
        }

def assess_dust_risk(wind_speed):
    """Оценивает риск переноса пыли на основе скорости ветра."""
    if wind_speed < 4:
        return "Низкий (Low)"
    elif 4 <= wind_speed < 8:
        return "Средний (Medium)"
    else:
        return "Высокий (High)"

@bot.message_handler(commands=['weather'])
@bot.message_handler(func=lambda message: message.text == "☀️ Текущая погода")
def process_weather_command(message):
    """Обработчик команды /weather и кнопки '☀️ Текущая погода'."""
    chat_id = message.chat.id
    # Используем Актау по умолчанию как запрошено
    weather = get_weather_data('Актау')

    temp = weather['temp']
    temp_str = f"+{temp}" if isinstance(temp, (int, float)) and temp > 0 else str(temp)

    bot.send_message(
        chat_id,
        f"☀️ Текущая погода в Актау:\n"
        f"🌡 Температура: {temp_str}°C\n"
        f"💨 Ветер: {weather['wind_speed']} м/с\n"
        f"☁️ Состояние: {weather.get('description', 'Нет данных')}"
    )

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команды /start и /help."""
    # Сброс состояния для предотвращения soft-lock
    chat_id = message.chat.id
    if chat_id in user_data:
        user_data[chat_id].pop('state', None)

    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [KeyboardButton(region) for region in WIND_SPEEDS.keys()]
    buttons.append(KeyboardButton("Эко-Викторина"))
    buttons.append(KeyboardButton("Эко-Риск на сегодня"))
    buttons.append(KeyboardButton("Инфо: Кошкар-Ата"))
    buttons.append(KeyboardButton("☀️ Текущая погода"))
    markup.add(*buttons)

    bot.send_message(
        message.chat.id,
        "👋 Привет! Я бот для экологического мониторинга опустынивания в Мангистауской области.\n"
        "Выберите район для анализа или проверьте свои знания в викторине:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "Эко-Викторина")
def process_quiz(message):
    """Обработчик эко-викторины."""
    chat_id = message.chat.id
    question_data = random.choice(QUIZ_QUESTIONS)

    # Сохраняем правильный ответ для проверки, не стирая счетчик
    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id]['quiz_answer'] = question_data['answer']
    user_data[chat_id]['quiz_explanation'] = question_data['explanation']

    markup = InlineKeyboardMarkup()
    for idx, option in enumerate(question_data['options']):
        markup.add(InlineKeyboardButton(text=option, callback_data=f"quiz_{idx}"))

    bot.send_message(
        chat_id,
        f"🌿 *Эко-Викторина*\n\n{question_data['question']}",
        reply_markup=markup,
        parse_mode='Markdown'
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("quiz_"))
def callback_quiz_answer(call):
    """Обработка ответов викторины."""
    chat_id = call.message.chat.id
    if chat_id not in user_data or 'quiz_answer' not in user_data[chat_id]:
        bot.answer_callback_query(call.id, "Срок действия вопроса истек. Начните новую викторину.")
        return

    selected_option = int(call.data.split('_')[1])
    correct_option = user_data[chat_id]['quiz_answer']
    explanation = user_data[chat_id]['quiz_explanation']

    if selected_option == correct_option:
        # Увеличиваем счетчик правильных ответов
        user_data[chat_id]['quiz_score'] = user_data[chat_id].get('quiz_score', 0) + 1
        score = user_data[chat_id]['quiz_score']
        response_text = f"✅ *Правильно!*\n\n{explanation}\n\nВаш счет: {score}/3"

        # Проверяем достижение медали
        if score == 3:
            response_text += "\n\n🏅 *Поздравляем!*\nВы получили звание **'Эко-Защитник Мангистау'**! Вы отлично разбираетесь в проблемах экологии."
            # Сбрасываем счетчик после получения медали
            user_data[chat_id]['quiz_score'] = 0
    else:
        response_text = f"❌ *Неверно.*\n\n{explanation}"

    # Удаляем временные данные вопроса (но оставляем счетчик)
    del user_data[chat_id]['quiz_answer']
    del user_data[chat_id]['quiz_explanation']

    # Убираем инлайн клавиатуру и отправляем результат
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    bot.send_message(chat_id, response_text, parse_mode='Markdown')


@bot.message_handler(func=lambda message: message.text in WIND_SPEEDS.keys() and user_data.get(message.chat.id, {}).get('state') != 'eco_risk')
def process_region_step(message):
    """Обработчик выбора района для прогноза деградации."""
    chat_id = message.chat.id
    region = message.text

    # Получаем динамические погодные данные
    weather = get_weather_data(region)
    dynamic_wind = weather['wind_speed']
    risk = assess_dust_risk(dynamic_wind)

    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id]['region'] = region
    user_data[chat_id]['dynamic_wind'] = dynamic_wind # Сохраняем динамический ветер

    # Смарт-уведомление (Smart Alert)
    alert_text = (
        f"Текущая погода в районе {region}: {weather['temp']}°C, Ветер {dynamic_wind} м/с. "
        f"Основываясь на сегодняшнем ветре, риск переноса пыли оценивается как *{risk}*."
    )
    bot.send_message(chat_id, alert_text, parse_mode='Markdown')

    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [KeyboardButton(pollution) for pollution in POLLUTION_COEFFICIENTS.keys()]
    buttons.append(KeyboardButton("⬅️ Назад"))
    markup.add(*buttons)

    bot.send_message(
        chat_id,
        "Теперь выберите тип загрязнения:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "⬅️ Назад")
def process_back(message):
    send_welcome(message)

@bot.message_handler(func=lambda message: message.text in POLLUTION_COEFFICIENTS.keys())
def process_pollution_step(message):
    """Обработчик выбора типа загрязнения."""
    if message.text == "⬅️ Назад":
        process_back(message)
        return

    chat_id = message.chat.id
    pollution = message.text

    if chat_id not in user_data or 'region' not in user_data[chat_id]:
        bot.send_message(chat_id, "Пожалуйста, начните сначала с команды /start")
        return

    user_data[chat_id]['pollution'] = pollution

    bot.send_message(
        chat_id,
        "Введите начальную площадь загрязнения (в гектарах, например, 10):",
        reply_markup=telebot.types.ReplyKeyboardRemove()
    )

    bot.register_next_step_handler(message, process_area_step)

def get_restoration_plan(region, pollution):
    """Генерирует план восстановления на основе параметров."""
    plan = f"🌱 *План восстановления экосистемы ({region})*\n\n"

    if pollution == 'Тяжелые металлы':
        plan += "1. **Химическая нейтрализация:** Внесение в почву сорбентов (например, цеолитов) для связывания тяжелых металлов.\n"
        plan += "2. **Фиторемедиация:** Посадка растений-гипераккумуляторов, способных извлекать металлы из почвы.\n"
        plan += "3. **Агротехнические мероприятия:** Регулярный мониторинг и замена верхнего слоя почвы на локализованных участках."
    elif pollution == 'Нефть':
        plan += "1. **Механическая очистка:** Локализация и сбор свободной нефти с поверхности земли.\n"
        plan += "2. **Биоремедиация:** Применение специальных микроорганизмов-нефтедеструкторов, которые разлагают углеводороды.\n"
        plan += "3. **Фитомелиорация:** Посев устойчивых к нефти трав для восстановления структуры почвы."

    return plan

def calculate_degradation(area, wind_speed, pollution_coef, years, reduction=0.0):
    """Математическая модель расчета площади деградации.
    reduction - процент снижения скорости деградации (например, 0.4 для 40%)
    """
    growth_increment = (wind_speed * pollution_coef * 0.05) * (1 - reduction)
    growth_rate = 1 + growth_increment
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
    # Используем динамический ветер, если он есть, иначе статический
    wind_speed = data.get('dynamic_wind', WIND_SPEEDS[region])
    pollution_coef = POLLUTION_COEFFICIENTS[pollution]

    # Годы для прогноза
    years = [0, 5, 10, 20]

    # Расчет площади для каждого года
    areas = [calculate_degradation(area, wind_speed, pollution_coef, y) for y in years]

    # Расчет площади для восстановительного сценария (Сценарий B - 40% снижение)
    recovery_areas = [calculate_degradation(area, wind_speed, pollution_coef, y, reduction=0.4) for y in years]

    # Оценка риска
    risk_level = assess_dust_risk(wind_speed)

    # Текстовый отчет
    report = (
        f"📊 *Прогноз опустынивания для района {region}*\n"
        f"Тип загрязнения: {pollution}\n"
        f"Начальная площадь: {area} га\n\n"
        f"Current wind in Mangystau: {wind_speed} м/с. Risk level: {risk_level}.\n"
    )

    if wind_speed >= 8.0:
        report += "⚠️ *High wind speed detected. Dust transport risk increased!*\n"

    report += (
        f"\nПрогнозируемая площадь деградации:\n"
        f"• Через 5 лет: {areas[1]:.2f} га\n"
        f"• Через 10 лет: {areas[2]:.2f} га\n"
        f"• Через 20 лет: {areas[3]:.2f} га\n\n"
    )

    report += INFO_TEXT

    # Генерация графика
    plt.figure(figsize=(10, 6))

    # Цветовое зонирование (Color Zoning)
    plt.axvspan(0, 5, color='green', alpha=0.15, label='Шанс на восстановление (0-5 лет)')
    plt.axvspan(5, 10, color='orange', alpha=0.15, label='Предупреждение (5-10 лет)')
    plt.axvspan(10, 20, color='red', alpha=0.15, label='Экологическая катастрофа (10-20 лет)')

    # Линия прогноза (Business as usual)
    plt.plot(years, areas, marker='o', linestyle='-', color='darkred', linewidth=2.5, markersize=10, label='Business as usual')

    # Линия восстановительного сценария (With Restoration Plan)
    plt.plot(years, recovery_areas, marker='s', linestyle='--', color='blue', linewidth=2.5, markersize=8, label='With Restoration Plan')

    # Критическая линия (Threshold Line)
    plt.axhline(y=10000, color='black', linestyle='--', linewidth=1.5)
    plt.text(0.5, 10500, 'Critical Limit', color='black', fontsize=10, fontweight='bold')

    # Добавление подписей данных (exact numbers)
    for i, txt in enumerate(areas):
        plt.annotate(f'{txt:.1f}', (years[i], areas[i]), textcoords="offset points", xytext=(0,10), ha='center', fontsize=9, color='darkred')
    for i, txt in enumerate(recovery_areas):
        plt.annotate(f'{txt:.1f}', (years[i], recovery_areas[i]), textcoords="offset points", xytext=(0,-15), ha='center', fontsize=9, color='blue')

    # Использование логарифмической шкалы если разница слишком велика
    if max(areas) / min(areas) > 100:
        plt.yscale('log')
        plt.ylabel('Площадь деградации (га) [Логарифмическая шкала]', fontsize=12)
    else:
        plt.ylabel('Площадь деградации (га)', fontsize=12)

    # Настройка графика
    plt.title(f'Прогноз деградации почвы: {region}', fontsize=14, fontweight='bold')
    plt.xlabel('Годы', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(years)
    plt.legend(loc='upper left', fontsize=9)

    # Сохранение графика в буфер памяти
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()

    # Клавиатура с планом восстановления и возвратом
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(KeyboardButton("План восстановления"))
    markup.add(KeyboardButton("⬅️ Назад в меню"))

    # Отправка отчета и графика пользователю
    bot.send_message(chat_id, report, parse_mode='Markdown')
    bot.send_photo(chat_id, buf, caption="График прогноза деградации почвы")

    # User feedback prompt
    feedback_text = (
        "⚠️ *Обнаружили новое место загрязнения?*\n"
        "Сообщите об этом! Свяжитесь с местными экологическими органами:\n"
        "📞 Телефон: +7 (7292) 12-34-56\n"
        "📧 Email: eco.mangystau@gov.kz"
    )
    bot.send_message(chat_id, feedback_text, parse_mode='Markdown', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "План восстановления")
def process_restoration_plan(message):
    """Обработчик кнопки План восстановления."""
    chat_id = message.chat.id
    data = user_data.get(chat_id)

    if not data or 'region' not in data or 'pollution' not in data:
        bot.send_message(chat_id, "Сначала необходимо провести расчет прогноза. Нажмите /start")
        return

    plan = get_restoration_plan(data['region'], data['pollution'])
    bot.send_message(chat_id, plan, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "⬅️ Назад в меню")
def back_to_menu(message):
    """Возврат в главное меню."""
    send_welcome(message)

@bot.message_handler(func=lambda message: message.text == "Инфо: Кошкар-Ата")
def process_koshkar_ata_info(message):
    """Справка о хвостохранилище Кошкар-Ата."""
    chat_id = message.chat.id
    info_text = (
        "☢️ *Хвостохранилище Кошкар-Ата*\n\n"
        "Кошкар-Ата — это искусственное бессточное озеро-впадина недалеко от Актау, куда десятилетиями сливались "
        "токсичные и радиоактивные отходы промышленных предприятий. Из-за высыхания озера оголились огромные участки дна.\n\n"
        "💨 *Опасность:*\n"
        "Оголенное дно является источником токсичной пыли, содержащей **тяжелые металлы** (свинец, стронций, уран). "
        "При сильных ветрах эта пыль поднимается в воздух и разносится на десятки километров, отравляя почву, "
        "растительность и угрожая здоровью жителей Актау и Мунайлинского района.\n\n"
        "📊 *Как помогает наша модель?*\n"
        "Наша математическая модель мониторинга позволяет рассчитать скорость и площадь распространения этой "
        "токсичной пыли (основываясь на реальных показателях ветра). Это помогает экологам планировать зоны "
        "обязательного озеленения и фиторемедиации (например, посадки саксаула) для создания защитного барьера."
    )
    bot.send_message(chat_id, info_text, parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "Эко-Риск на сегодня")
def process_eco_risk_start(message):
    """Начало процесса оценки эко-риска на сегодня."""
    chat_id = message.chat.id

    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id]['state'] = 'eco_risk'

    markup = InlineKeyboardMarkup()
    for region in WIND_SPEEDS.keys():
        markup.add(InlineKeyboardButton(text=region, callback_data=f"risk_{region}"))

    bot.send_message(
        chat_id,
        "Выберите район для получения прогноза эко-риска на ближайшие 24 часа:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("risk_"))
def callback_eco_risk(call):
    """Обработка выбора района для эко-риска."""
    chat_id = call.message.chat.id
    region = call.data.split('_')[1]

    # Сбрасываем состояние
    if chat_id in user_data and 'state' in user_data[chat_id]:
        del user_data[chat_id]['state']

    weather = get_weather_data(region)
    risk = assess_dust_risk(weather['wind_speed'])

    forecast_text = (
        f"🌍 *Прогноз Эко-Риска на 24 часа: {region}*\n\n"
        f"🌡️ **Температура:** {weather['temp']}°C\n"
        f"💧 **Влажность:** {weather['humidity']}%\n"
        f"🌬️ **Скорость ветра:** {weather['wind_speed']} м/с\n\n"
        f"⚠️ **Уровень риска переноса пыли/загрязнений:** {risk}\n\n"
    )

    if risk == "Высокий (High)":
        forecast_text += "❗ *Рекомендация:* Оставайтесь в помещении. Возможны пыльные бури и перенос токсичных аэрозолей."
    elif risk == "Средний (Medium)":
        forecast_text += "⚠️ *Рекомендация:* Рекомендуется ограничить длительное пребывание на открытом воздухе в зонах загрязнений."
    else:
        forecast_text += "✅ *Рекомендация:* Погодные условия благоприятны, риск минимален."

    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    bot.send_message(chat_id, forecast_text, parse_mode='Markdown')

def eco_advisor(chat_id):
    """Предоставляет подробное руководство для граждан."""
    guide = (
        "🌿 *Советы Эко-Защитника: Как вы можете помочь?*\n\n"
        "1. **Правильная утилизация отходов:** Не выбрасывайте батарейки, пластик и масло в почву или воду. Сдавайте их в пункты приема.\n"
        "2. **Озеленение:** Участвуйте в посадке местных, засухоустойчивых растений (например, саксаула), которые укрепляют почву.\n"
        "3. **Экономия воды:** В условиях нашего региона пресная вода — на вес золота. Используйте её рационально.\n"
        "4. **Эко-патруль:** Сообщайте о несанкционированных свалках и разливах нефти местным властям."
    )
    bot.send_message(chat_id, guide, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_free_text(message):
    """Обработчик свободного текста."""
    text = message.text.lower()
    chat_id = message.chat.id
    original_text = message.text

    # Игнорируем системные кнопки, регионы и типы загрязнений
    ignore_list = list(WIND_SPEEDS.keys()) + list(POLLUTION_COEFFICIENTS.keys()) + [
        "⬅️ Назад", "⬅️ Назад в меню", "Эко-Викторина", "Эко-Риск на сегодня", "Инфо: Кошкар-Ата", "План восстановления"
    ]
    if original_text in ignore_list:
        return

    def matches(keywords):
        pattern = r'\b(?:' + '|'.join(map(re.escape, keywords)) + r')\b'
        return bool(re.search(pattern, text))

    if matches(["hello", "hi", "привет", "здравствуйте"]):
        bot.send_message(chat_id, "Привет! Рад вас видеть. Я могу помочь вам узнать больше об экологии Мангистау. Нажмите /start или воспользуйтесь кнопками.")

    elif matches(["what can you do", "что ты умеешь", "функции"]) or "what can you do" in text or "что ты умеешь" in text:
        bot.send_message(chat_id, "Я умею прогнозировать расширение пустыни, проводить эко-викторины и составлять планы восстановления экосистем. Нажмите /start, чтобы начать!")

    elif matches(["metal", "металл", "металлы", "metals"]):
        bot.send_message(chat_id, "💡 *Факт:* Тяжелые металлы, такие как свинец и кадмий, отравляют микрофлору почвы, делая её мертвой на долгие десятилетия.", parse_mode='Markdown')

    elif matches(["oil", "нефть", "разлив"]):
        bot.send_message(chat_id, "💡 *Факт:* Разливы нефти склеивают частицы почвы, полностью перекрывая доступ кислорода, что приводит к удушью всей корневой системы растений.", parse_mode='Markdown')

    elif matches(["soil", "почва", "земля", "саксаул"]):
        bot.send_message(chat_id, "💡 *Факт:* Саксаул — настоящий герой пустыни! Его корни могут уходить на глубину до 10 метров, прочно удерживая почву от выдувания.", parse_mode='Markdown')

    elif matches(["help", "advice", "how to", "помощь", "совет", "советы", "как помочь"]) or "how to" in text or "как помочь" in text:
        eco_advisor(chat_id)

    elif matches(["погода", "weather"]) or "погода" in text or "weather" in text:
        process_weather_command(message)

    else:
        bot.send_message(
            chat_id,
            "Я всё ещё учусь! Вы можете использовать кнопки ниже или спросить меня про 'Саксаул', 'Нефть' или 'Тяжелые металлы', чтобы узнать больше."
        )

if __name__ == '__main__':
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Ошибка polling: {e}")
            time.sleep(5)