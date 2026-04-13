import streamlit as st
import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt

# Настройка страницы
st.set_page_config(layout="wide", page_title="Симулятор Реактора")
st.title("⚛️ Цифровой двойник: Ториевый топливный цикл")
st.markdown("Интерактивная панель управления для виртуальной лаборатории РФМШ")

# --- БОКОВАЯ ПАНЕЛЬ (Интерфейс управления) ---
st.sidebar.header("Панель управления")

# Интерактивные ползунки
phi_base = st.sidebar.slider("Поток нейтронов (x10^14)", min_value=0.0, max_value=5.0, value=1.0, step=0.1)
time_days = st.sidebar.slider("Время работы (дни)", min_value=10, max_value=1000, value=365, step=10)

# Кнопка аварийной остановки
emergency = st.sidebar.button("🚨 АВАРИЙНАЯ ОСТАНОВКА")

# Логика кнопки: если нажата, поток нейтронов равен нулю
phi = 0.0 if emergency else phi_base * 1e14

# --- ФИЗИЧЕСКОЕ ЯДРО ---
sigma_c_th = 7.4e-24
lambda_pa = np.log(2) / (27 * 24 * 3600)

def bateman(N, t):
    Th, Pa, U = N
    return [-sigma_c_th * phi * Th,
            sigma_c_th * phi * Th - lambda_pa * Pa,
            lambda_pa * Pa]

t = np.linspace(0, time_days * 24 * 3600, 500)
solution = odeint(bateman, [1.0, 0.0, 0.0], t)

# --- ВИЗУАЛИЗАЦИЯ НА САЙТЕ ---
if emergency:
    st.error("ВНИМАНИЕ: Реактор заглушен. Поток нейтронов = 0. Демонстрация пассивного распада.")

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(t / (24*3600), solution[:, 0], label='Th-232 (Торий)', color='blue')
ax.plot(t / (24*3600), solution[:, 1], label='Pa-233 (Протактиний)', color='orange')
ax.plot(t / (24*3600), solution[:, 2], label='U-233 (Уран - Топливо)', color='red')
ax.set_yscale('log')
ax.set_ylim(1e-5, 1.5)
ax.set_xlabel("Дни работы")
ax.set_ylabel("Доля от исходной массы")
ax.legend()
ax.grid(True, ls="--")

# Вывод графика на веб-страницу
st.pyplot(fig)