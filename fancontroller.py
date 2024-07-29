import json
import threading
import os

from fanController.dell730_controller import Dell730FanController


def main():
    # 获取当前脚本所在目录
    current_directory = os.path.dirname(os.path.abspath(__file__))
    # 构建配置文件路径
    config_file_path = os.path.join(current_directory, 'fan_settings.json')
    # 构建日志文件路径
    log_file_path = os.path.join(current_directory, 'fancontroller.log')

    # 从配置文件中读取数据
    with open(config_file_path, 'r') as file:
        try:
            data = json.load(file)
        except json.JSONDecodeError:
            input("错误：文件内容不是有效的JSON格式，请检查配置后重新打开，输入任意键退出程序：")
            return

    servers = data['servers']
    windows_ipmi_tool_path = data['windows_ipmi_tool_path']
    interval = data['interval']
    threads = []

    for server in servers:
        if server['type'] == 'dell730':
            # 使用 Dell730FanController 控制器
            fan_controller = Dell730FanController(servers=server, interval=interval, windows_ipmi_tool_path=windows_ipmi_tool_path,log_file_path=log_file_path)
            # 创建线程并启动风扇控制
            thread = threading.Thread(target=fan_controller.start_fan_control)
            thread.start()
            threads.append(thread)

    # 等待所有线程完成
    for thread in threads:
        thread.join()

if __name__ == '__main__':
    main()
