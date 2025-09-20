import tkinter as tk
from tkinter import scrolledtext
import os
import shlex
import sys
import platform
import getpass

class REPLEmulator:
    def __init__(self, root):
        self.root = root
        username = getpass.getuser()
        hostname = platform.node()
        self.root.title(f"Эмулятор - [{username}@{hostname}]")
        self.root.geometry("800x600")

        # Создание виджетов
        self.output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='normal')
        self.output_text.pack(expand=True, fill='both', padx=10, pady=10)
        self.output_text.config(state='disabled')

        self.input_frame = tk.Frame(root)
        self.input_frame.pack(fill='x', padx=10, pady=5)

        self.command_entry = tk.Entry(self.input_frame, width=100)
        self.command_entry.pack(side='left', fill='x', expand=True)
        self.command_entry.bind('<Return>', self.on_enter)

        self.execute_button = tk.Button(self.input_frame, text="Выполнить", command=self.on_enter)
        self.execute_button.pack(side='right')

        # История команд
        self.history = []
        self.history_index = -1
        self.command_entry.bind('<Up>', self.history_prev)
        self.command_entry.bind('<Down>', self.history_next)

        # Вывод приветственного сообщения
        self.print_output("Добро пожаловать в эмулятор командной строки! Введите команду или 'exit' для выхода.")

    def print_output(self, text, tag=None):
        self.output_text.config(state='normal')
        if tag:
            self.output_text.insert(tk.END, text + '\n', tag)
        else:
            self.output_text.insert(tk.END, text + '\n')
        self.output_text.see(tk.END)
        self.output_text.config(state='disabled')

    def on_enter(self, event=None):
        command = self.command_entry.get()
        if not command.strip():
            return

        # Добавляем в историю
        self.history.append(command)
        self.history_index = len(self.history)  # Сброс позиции
        self.command_entry.delete(0, tk.END)

        # Парсинг команды
        try:
            args = shlex.split(command)
        except Exception as e:
            self.print_output(f"Ошибка парсинга: {e}", tag='error')
            return

        # Выполнение команды
        self.process_command(args)

    def process_command(self, args):
        if not args:
            return
        cmd = args[0].lower()

        if cmd == "exit":
            self.print_output("Выход из эмулятора...", tag='success')
            self.root.quit()
        elif cmd == "ls":
            self.print_output(f"Команда: ls {' '.join(args[1:])}")
            if len(args) > 1:
                self.print_output(f"Аргументы: {' '.join(args[1:])}")
        elif cmd == "cd":
            self.print_output(f"Команда: cd {' '.join(args[1:])}")
            if len(args) > 1:
                self.print_output(f"Аргументы: {' '.join(args[1:])}")
        else:
            self.print_output(f"Ошибка: неизвестная команда '{cmd}'", tag='error')
            if args:
                self.print_output(f"Полученные аргументы: {' '.join(args)}")

    def history_prev(self, event=None):
        if self.history:
            self.history_index = max(0, self.history_index - 1)
            self.command_entry.delete(0, tk.END)
            self.command_entry.insert(0, self.history[self.history_index])

    def history_next(self, event=None):
        if self.history:
            if self.history_index < len(self.history) - 1:
                self.history_index += 1
                self.command_entry.delete(0, tk.END)
                self.command_entry.insert(0, self.history[self.history_index])
            else:
                self.command_entry.delete(0, tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = REPLEmulator(root)
    # Настройка цветов
    app.output_text.tag_config('error', foreground='red')
    app.output_text.tag_config('success', foreground='green')
    root.mainloop()