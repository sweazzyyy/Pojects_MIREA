import tkinter as tk
from tkinter import scrolledtext
import shlex
import platform
import datetime
import os
import sys
import argparse
import yaml
import csv
import getpass

# Настройка путей и параметров

def parse_args():
    parser = argparse.ArgumentParser(description="Эмулятор оболочки (Этапы 1 и 2)")
    parser.add_argument("--vfs", help="Путь к VFS (не используется в демо, но логируется)")
    parser.add_argument("--log", help="Путь к лог-файлу команд (commits.log)")
    parser.add_argument("--script", help="Путь к стартовому скрипту")
    parser.add_argument("--config", help="Путь к конфигурационному файлу YAML")
    return parser.parse_args()

def load_config(cli_args):
    # Значения по умолчанию
    config = {
        "vfs": "./vfs.tar",
        "log": "./commits.log",
        "script": "./start_script.txt"
    }

    config_path = cli_args.config or "./config.yaml"

    # Загружаем YAML, если файл существует
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                yaml_config = yaml.safe_load(f) or {}
            # Обновляем значения из YAML
            for key in config:
                if key in yaml_config:
                    config[key] = yaml_config[key]
        except Exception as e:
            print(f"Ошибка чтения конфигурационного файла {config_path}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Создаём пример конфига
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump({
                "vfs": "./vfs.tar",
                "log": "./commits.log",
                "script": "./start_script.txt"
            }, f, allow_unicode=True, default_flow_style=False)
        print(f"Создан пример конфигурационного файла: {config_path}")

    # Приоритет: CLI > YAML > default
    if cli_args.vfs:
        config["vfs"] = cli_args.vfs
    if cli_args.log:
        config["log"] = cli_args.log
    if cli_args.script:
        config["script"] = cli_args.script

    return config

# Логирование

def log_commit(command, success=True, log_path="./commits.log"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "OK" if success else "ERROR"
    user = getpass.getuser()
    log_entry = f"[{timestamp}] USER={user} {status}: {command}\n"
    os.makedirs(os.path.dirname(log_path) if os.path.dirname(log_path) else ".", exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_entry)

def log_error_to_csv(command, error_msg, csv_path="./shell_errors.csv"):
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "user", "command", "error"])
        writer.writerow([
            datetime.datetime.now().isoformat(),
            getpass.getuser(),
            command,
            error_msg
        ])

# GUI и обработка команд

class ShellEmulator:
    def __init__(self, root, config):
        self.config = config
        self.script_mode = False  # флаг: выполняется ли стартовый скрипт

        os_name = platform.system()
        root.title(f"Операционная система: {os_name}")
        root.geometry("800x600")
        self.root = root

        self.output = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled', bg="#f8f8f8", font=("Courier", 10))
        self.output.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.input_frame = tk.Frame(root)
        self.input_frame.pack(padx=10, pady=(0, 10), fill=tk.X)

        self.prompt_label = tk.Label(self.input_frame, text="> ", font=("Courier", 10))
        self.prompt_label.pack(side=tk.LEFT)

        self.entry = tk.Entry(self.input_frame, font=("Courier", 10))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry.bind("<Return>", self.process_command)
        self.entry.focus()

        self.print_output(f"Эмулятор запущен. ОС: {os_name}\n")
        self.print_output(f"Конфигурация:\n  VFS: {config['vfs']}\n  Лог: {config['log']}\n  Скрипт: {config['script']}\n\n")
        self.print_output("Команды: wtf, exit, echo, pwd\n")

        # Выполняем стартовый скрипт, если указан и существует
        if os.path.exists(config["script"]):
            self.run_startup_script(config["script"])

    def print_output(self, text):
        self.output.config(state='normal')
        self.output.insert(tk.END, text)
        self.output.config(state='disabled')
        self.output.see(tk.END)

    def process_command(self, event=None):
        if self.script_mode:
            return  # блокируем ввод во время скрипта

        raw_cmd = self.entry.get()
        self.entry.delete(0, tk.END)
        if not raw_cmd.strip():
            return

        self.print_output(f"> {raw_cmd}\n")
        self.execute_command(raw_cmd)

    def execute_command(self, raw_cmd):
        try:
            parts = shlex.split(raw_cmd)
            if not parts:
                return
            cmd = parts[0].lower()
            args = parts[1:]
        except ValueError as e:
            error_msg = f"Синтаксическая ошибка: {e}"
            self.print_output(f"❌ {error_msg}\nПример: echo \"текст\"\n")
            log_error_to_csv(raw_cmd, str(e), csv_path=os.path.dirname(self.config['log']) + "/shell_errors.csv")
            log_commit(raw_cmd, success=False, log_path=self.config["log"])
            return

        log_commit(raw_cmd, success=True, log_path=self.config["log"])

        if cmd == "exit":
            self.handle_exit(args)
        elif cmd == "wtf":
            self.handle_wtf(args)
        elif cmd == "echo":
            self.handle_echo(args)
        elif cmd == "pwd":
            self.handle_pwd(args)
        else:
            error_msg = f"Неизвестная команда: {cmd}"
            self.print_output(f"❌ {error_msg}\nПоддерживаемые команды: wtf, exit, echo, pwd\n")
            log_error_to_csv(raw_cmd, error_msg, csv_path=os.path.dirname(self.config['log']) + "/shell_errors.csv")
            log_commit(raw_cmd, success=False, log_path=self.config["log"])

    def handle_exit(self, args):
        arg_str = " ".join(args)
        self.print_output(f"exit {arg_str}\n")
        self.root.after(1000, self.root.destroy)

    def handle_wtf(self, args):
        info = "WTF? Это эмулятор оболочки (Этапы 1+2).\n"
        info += f"VFS: {self.config['vfs']}\n"
        info += f"Лог: {self.config['log']}\n"
        if args:
            info += f"Аргументы: {args}\n"
        self.print_output(info)

    def handle_echo(self, args):
        self.print_output(" ".join(args) + "\n")

    def handle_pwd(self, args):
        self.print_output(os.getcwd() + "\n")

    def run_startup_script(self, script_path):
        self.script_mode = True
        self.print_output(f"\n▶ Запуск стартового скрипта: {script_path}\n")
        try:
            with open(script_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            self.print_output(f"❌ Не удалось прочитать скрипт: {e}\n")
            return

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            self.print_output(f"> {line}\n")
            self.execute_command(line)
            # Останавливаемся при первой ошибке (условие: если последняя команда завершилась ошибкой)
            # В нашем случае — просто выходим из цикла при неизвестной команде
            # (более точную проверку можно добавить через флаг в execute_command)
            if not line.split()[0].lower() in ["wtf", "echo", "pwd", "exit"]:
                self.print_output(f"🛑 Скрипт остановлен на строке {line_num} из-за ошибки.\n")
                break
            if "exit" in line:
                break

        self.script_mode = False
        self.print_output("\n✅ Скрипт завершён.\n")

# Создание примеров файлов

def create_example_files():
    # Пример стартового скрипта
    if not os.path.exists("start_script.txt"):
        with open("start_script.txt", "w", encoding="utf-8") as f:
            f.write("# Стартовый скрипт\n")
            f.write("echo \"Привет из стартового скрипта!\"\n")
            f.write("wtf\n")
            f.write("pwd\n")
            # f.write("exit\n")  # можно раскомментировать для авто-выхода

# Запуск

if __name__ == "__main__":
    args = parse_args()
    config = load_config(args)
    create_example_files()

    root = tk.Tk()
    app = ShellEmulator(root, config)
    root.mainloop()