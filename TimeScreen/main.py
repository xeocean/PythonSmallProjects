import pyautogui
import time
from datetime import datetime
import tkinter as tk
from tkinter import filedialog
import threading

stop_flag = False
delay = 10


def log_message(message):
    """Вывод сообщения в мини-терминал"""
    terminal_text.config(state=tk.NORMAL)
    terminal_text.insert(tk.END, message + "\n")
    terminal_text.config(state=tk.DISABLED)
    terminal_text.see(tk.END)


def take_screenshot(path):
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    screenshot = pyautogui.screenshot()
    screenshot_path = f"{path}/screenshot_{current_time}.png"
    screenshot.save(screenshot_path)
    log_message(f"Скриншот сохранен: {screenshot_path}")


def auto_screenshot(interval_seconds, path):
    global stop_flag
    time.sleep(delay)
    while not stop_flag:
        take_screenshot(path)
        time.sleep(interval_seconds)
    log_message("Автоскриншот остановлен.")


def start_screenshot():
    global stop_flag
    stop_flag = False
    try:
        interval_text = interval_entry.get()
        if not interval_text:
            raise ValueError("Поле интервала не должно быть пустым")
        interval = int(interval_text)
        if interval <= 0:
            raise ValueError("Интервал должен быть больше 0")
        path = path_var.get()
        if not path:
            raise ValueError("Не выбран путь для сохранения")

        log_message(f"Автоскриншот запущен. Интервал: {interval} мин. Путь: {path}")
        start_button.config(text="Остановить", command=stop_screenshot)
        threading.Thread(target=auto_screenshot, args=(interval * 60, path)).start()
    except ValueError as e:
        log_message(f"Ошибка: {e}")


def stop_screenshot():
    global stop_flag
    stop_flag = True
    start_button.config(text="Старт", command=start_screenshot)
    log_message("Автоскриншот остановлен")


def browse_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        path_var.set(folder_selected)
        log_message(f"Выбран путь: {folder_selected}")


def on_closing():
    stop_screenshot()
    root.destroy()

root = tk.Tk()
root.title("TimeScreen")
root.geometry("500x300")
root.minsize(400, 200)

path_var = tk.StringVar()

tk.Label(root, text="Путь для сохранения:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
path_entry = tk.Entry(root, textvariable=path_var, state='readonly')
path_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

browse_button = tk.Button(root, text="Выбрать папку", command=browse_folder)
browse_button.grid(row=0, column=2, padx=10, pady=10, sticky="ew")

tk.Label(root, text="Интервал (в минутах):").grid(row=1, column=0, padx=10, pady=10, sticky="e")
interval_entry = tk.Entry(root)
interval_entry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")

start_button = tk.Button(root, text="Старт", command=start_screenshot)
start_button.grid(row=1, column=2, padx=10, pady=10, sticky="ew")

terminal_text = tk.Text(root, height=10, width=50, state=tk.DISABLED)
terminal_text.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(2, weight=1)

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
