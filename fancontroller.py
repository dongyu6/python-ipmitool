import json
import threading

from fanController.dell730_controller import Dell730FanController


def main():
    # 从配置文件中读取数据
    with open('fan_settings.json', 'r') as file:
        data = json.load(file)

    servers = data['servers']
    windows_ipmi_tool_path = data['windows_ipmi_tool_path']
    interval = data['interval']
    threads = []

    for server in servers:
        if server['type'] == 'dell730':
            # 使用 Dell730FanController 控制器
            fan_controller = Dell730FanController(servers=server, interval=interval, windows_ipmi_tool_path=windows_ipmi_tool_path)
            # 创建线程并启动风扇控制
            thread = threading.Thread(target=fan_controller.start_fan_control)
            thread.start()
            threads.append(thread)

    # 等待所有线程完成
    for thread in threads:
        thread.join()

if __name__ == '__main__':
    main()