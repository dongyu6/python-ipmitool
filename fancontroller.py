import json
import os
import threading
import logging
from logging.handlers import TimedRotatingFileHandler

from fanController.dell730_controller import Dell730FanController


def main():
    # --- 路径设置 ---
    current_directory = os.path.dirname(os.path.abspath(__file__))
    log_directory = os.path.join(current_directory, 'logs')
    os.makedirs(log_directory, exist_ok=True)
    log_file_path = os.path.join(log_directory, 'fancontroller.log')

    # --- 读取配置 ---
    config_file_path = os.path.join(current_directory, 'fan_settings.json')
    try:
        with open(config_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        # 在日志系统完全建立前，只能用print
        print(f"错误：配置文件 'fan_settings.json' 未找到。")
        input("按任意键退出程序：")
        return
    except json.JSONDecodeError:
        print("错误：文件内容不是有效的JSON格式，请检查配置后重新打开。")
        input("按任意键退出程序：")
        return

    # --- 日志配置 ---
    log_backup_count = data.get('log_backup_count', 30)  # 从配置读取日志保留天数，默认为30
    logger = logging.getLogger('FanController')
    logger.setLevel(logging.INFO)

    # 文件处理器 (按天轮转)
    file_handler = TimedRotatingFileHandler(
        log_file_path,
        when='midnight',
        interval=1,
        backupCount=log_backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)

    # 控制台处理器
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)

    # 日志格式
    formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # 添加处理器到logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # --- 启动控制器 ---
    logger.info("程序启动")
    servers = data['servers']
    windows_ipmi_tool_path = data['windows_ipmi_tool_path']
    interval = data['interval']
    auto = data.get('auto', False)
    threads = []

    for server in servers:
        if server['type'] == 'dell730':
            fan_controller = Dell730FanController(servers=server, interval=interval,
                                                windows_ipmi_tool_path=windows_ipmi_tool_path, logger=logger, auto=auto)
            thread = threading.Thread(target=fan_controller.start_fan_control, name=f"Thread-{server['ip']}")
            thread.start()
            threads.append(thread)

    for thread in threads:
        thread.join()