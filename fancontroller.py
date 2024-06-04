import json
import re
import time
import subprocess
from datetime import datetime
import threading
import platform

class IPMIFanController:
    def __init__(self, servers, interval, windows_ipmi_tool_path):
        # 初始化时指定 IPMI 工具的路径，默认为 ipmitool
        self.platform_system = platform.system()
        if self.platform_system == 'Windows':
            self.ipmi_tool_path = windows_ipmi_tool_path
        else:
            self.ipmi_tool_path='ipmitool'
        self.interval = interval
        self.servers = servers


    def send_command(self, cmd_in):
        # 发送命令并返回输出结果
        p = subprocess.Popen(cmd_in, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             universal_newlines=True, stderr=subprocess.STDOUT, close_fds=True)
        return p.stdout.read()

    def ipmi_command(self, cmd_in):
        # 执行 IPMI 命令
        command = f'{self.ipmi_tool_path} {cmd_in}'
        return self.send_command(command)

    def set_fan_speed(self, ip, user, password, fan_index, percentage):
        # 设置风扇转速，需要在子类中实现
        raise NotImplementedError("Method set_fan_speed must be implemented by subclasses")

    def get_cpu_temperature(self, ip, user, password):
        # 获取 CPU 温度，需要在子类中实现
        raise NotImplementedError("Method get_cpu_temperature must be implemented by subclasses")

    def process_server(self):
        # 处理单台服务器的温度设置
        ip = self.servers['ip']
        user = self.servers['user']
        password = self.servers['password']

        # # 禁用自动模式
        # disable_auto_cmd = f"-I lanplus -H {ip} -U {user} -P {password} raw 0x30 0x30 0x01 0x00"
        # self.ipmi_command(disable_auto_cmd)

        prev_temp_ranges = None
        prev_fan_speeds = None

        while True:
            # 获取 CPU 温度
            cpu_temps = self.get_cpu_temperature(ip, user, password)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if cpu_temps:
                avg_temp = sum(cpu_temps) / len(cpu_temps)
                print(f"[{current_time}] Server {ip}: Average CPU temperature: {avg_temp} °C")

                # 查找当前温度所在的温度区间
                for temp_range in self.servers['temperature_ranges']:
                    min_temp = temp_range['min_temp']
                    max_temp = temp_range['max_temp']
                    fan_speeds = temp_range['fan_speeds']

                    if min_temp <= avg_temp < max_temp:
                        # 如果当前温度区间和上一次相同，则不需要重新设置风扇转速
                        if (prev_temp_ranges == (min_temp, max_temp)) and (prev_fan_speeds == fan_speeds):
                            print(f"[{current_time}] Temperature is in the previous temperature range, skipping")
                            break

                        print(f"[{current_time}] Server {ip}: Temperature Range: {min_temp}-{max_temp} °C")
                        print(f"[{current_time}] Server {ip}: Set Fans to {fan_speeds}")
                        for fan_index, speed in enumerate(fan_speeds):
                            self.set_fan_speed(ip, user, password, fan_index, speed)
                            time.sleep(1)  # 等待一秒钟，以避免发送命令过快

                        # 更新临时变量
                        prev_temp_ranges = (min_temp, max_temp)
                        prev_fan_speeds = fan_speeds
                        break
            else:
                print(f"[{current_time}] Server {ip}: No CPU temperature data available.")

            time.sleep(self.interval)

    def start_fan_control(self):
        # 启动风扇控制
        self.process_server()

class Dell730FanController(IPMIFanController):
    def set_fan_speed(self, ip, user, password, fan_index, percentage):
        # 实现设置 Dell 730 服务器风扇转速的方法
        hex_percentage = format(percentage, '02x')
        set_speed_cmd = f"-I lanplus -H {ip} -U {user} -P {password} raw 0x30 0x30 0x02 0x{fan_index:02x} 0x{hex_percentage}"
        self.ipmi_command(set_speed_cmd)

    def get_cpu_temperature(self, ip, user, password):
        # 实现获取 Dell 730 服务器 CPU 温度的方法
        command = f"-I lanplus -H {ip} -U {user} -P {password} sdr type Temperature"
        output = self.ipmi_command(command)

        temp_list = []
        for line in  output.split("\n"):
                items = line.split("|")
                if len(items) > 1 and "ok" in items[2]:
                    if "0Eh" in items[1] or "0Fh" in items[1]:
                        temp_match = re.search(r'(\d+)\s+degrees\s+C', items[4])
                        if temp_match:
                            temp = int(temp_match.group(1))
                            temp_list.append(temp)
        return temp_list

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
            thread = threading.Thread(target=fan_controller.start_fan_control)
            thread.start()
            threads.append(thread)

    for thread in threads:
        thread.join()

if __name__ == '__main__':
    main()


