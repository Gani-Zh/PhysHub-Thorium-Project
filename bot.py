import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import matplotlib.pyplot as plt
import io
import os
import random

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
        "options": ["Засоление почв из-за испарения", "Восстановление экосистемы с помощью живых организмов (растений, бактерий)", "Химическое заражение грунтовых вод"],
        "answer": 1,
        "explanation": "Биоремедиация — это комплекс методов очистки вод, грунтов и атмосферы с использованием метаболического потенциала биологических объектов (чаще всего микроорганизмов и растений)."
    },
    {
        "question": "Какой процесс наиболее характерен для 'аэрозольного переноса тяжелых металлов'?",
        "options": ["Перемещение загрязнителей вместе с грунтовыми водами", "Растворение металлов в кислотных дождях", "Перенос токсичных частиц ветром в виде пыли"],
        "answer": 2,
        "explanation": "Аэрозольный перенос — это процесс транспортировки микроскопических частиц (включая тяжелые металлы) ветровыми потоками на большие расстояния."
    }
]

# Хранилище временных данных пользователей
user_data = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    """Обработчик команды /start и /help."""
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [KeyboardButton(region) for region in WIND_SPEEDS.keys()]
    buttons.append(KeyboardButton("Эко-Викторина"))
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

    # Сохраняем правильный ответ для проверки
    user_data[chat_id] = {'quiz_answer': question_data['answer'], 'quiz_explanation': question_data['explanation']}

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
        response_text = f"✅ *Правильно!*\n\n{explanation}"
    else:
        response_text = f"❌ *Неверно.*\n\n{explanation}"

    # Удаляем данные викторины
    del user_data[chat_id]['quiz_answer']
    del user_data[chat_id]['quiz_explanation']

    # Убираем инлайн клавиатуру и отправляем результат
    bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
    bot.send_message(chat_id, response_text, parse_mode='Markdown')


@bot.message_handler(func=lambda message: message.text in WIND_SPEEDS.keys())
def process_region_step(message):
    """Обработчик выбора района."""
    chat_id = message.chat.id
    region = message.text
    user_data[chat_id] = {'region': region}

    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [KeyboardButton(pollution) for pollution in POLLUTION_COEFFICIENTS.keys()]
    buttons.append(KeyboardButton("⬅️ Назад"))
    markup.add(*buttons)

    bot.send_message(
        chat_id,
        f"Вы выбрали {region}. Теперь выберите тип загрязнения:",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "⬅️ Назад")
def process_back(message):
    send_welcome(message)

@bot.message_handler(func=lambda message: message.text in POLLUTION_COEFFICIENTS.keys())
def process_pollution_step(message):
    """Обработчик выбора типа загрязнения."""
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

def calculate_degradation(area, wind_speed, pollution_coef, years):
    """Математическая модель расчета площади деградации."""
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

    # Добавление подписей данных (exact numbers)
    for i, txt in enumerate(areas):
        plt.annotate(f'{txt:.1f}', (years[i], areas[i]), textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)

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

if __name__ == '__main__':
    bot.infinity_polling()