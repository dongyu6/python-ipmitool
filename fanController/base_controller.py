import subprocess
from datetime import datetime
import time
import platform

class IPMIFanController:
    def __init__(self, servers, interval, windows_ipmi_tool_path):
        """
        初始化 IPMI 风扇控制器。

        Args:
            servers (dict): 包含服务器信息的字典。
            interval (int): 检查 CPU 温度的时间间隔（秒）。
            windows_ipmi_tool_path (str): Windows 平台上 IPMI 工具的路径。

        Attributes:
            platform_system (str): 操作系统平台。
            ipmi_tool_path (str): IPMI 工具的路径。
            interval (int): 检查 CPU 温度的时间间隔（秒）。
            servers (dict): 包含服务器信息的字典。
        """
        self.platform_system = platform.system()
        if self.platform_system == 'Windows':
            self.ipmi_tool_path = windows_ipmi_tool_path
        else:
            self.ipmi_tool_path = 'ipmitool'
        self.interval = interval
        self.servers = servers

    def send_command(self, cmd_in):
        """
        发送命令到系统 Shell。

        Args:
            cmd_in (str): 要执行的命令。

        Returns:
            str: 命令的输出。
        """
        p = subprocess.Popen(cmd_in, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             universal_newlines=True, stderr=subprocess.STDOUT, close_fds=True)
        return p.stdout.read()

    def ipmi_command(self, cmd_in):
        """
        执行 IPMI 命令。

        Args:
            cmd_in (str): 要执行的 IPMI 命令。

        Returns:
            str: IPMI 命令的输出。
        """
        command = f'{self.ipmi_tool_path} {cmd_in}'
        return self.send_command(command)

    def set_fan_speed(self, ip, user, password, fan_index, percentage):
        """
        设置指定风扇的转速。

        Args:
            ip (str): 服务器的 IP 地址。
            user (str): IPMI 认证的用户名。
            password (str): IPMI 认证的密码。
            fan_index (int): 要设置速度的风扇索引。
            percentage (int): 要设置的风扇转速百分比。

        Raises:
            NotImplementedError: 子类必须实现此方法。
        """
        raise NotImplementedError("Method set_fan_speed must be implemented by subclasses")

    def get_cpu_temperature(self, ip, user, password):
        """
        获取服务器的 CPU 温度。

        Args:
            ip (str): 服务器的 IP 地址。
            user (str): IPMI 认证的用户名。
            password (str): IPMI 认证的密码。

        Raises:
            NotImplementedError: 子类必须实现此方法。
        """
        raise NotImplementedError("Method get_cpu_temperature must be implemented by subclasses")

    def process_server(self):
        """
        处理服务器，监测 CPU 温度并相应调整风扇转速。
        """
        ip = self.servers['ip']
        user = self.servers['user']
        password = self.servers['password']

        prev_temp_ranges = None
        prev_fan_speeds = None

        while True:
            cpu_temps = self.get_cpu_temperature(ip, user, password)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if cpu_temps:
                avg_temp = sum(cpu_temps) / len(cpu_temps)
                print(f"[{current_time}] 服务器 {ip}：CPU 平均温度：{avg_temp} °C")

                for temp_range in self.servers['temperature_ranges']:
                    min_temp = temp_range['min_temp']
                    max_temp = temp_range['max_temp']
                    fan_speeds = temp_range['fan_speeds']

                    if min_temp <= avg_temp < max_temp:
                        if (prev_temp_ranges == (min_temp, max_temp)) and (prev_fan_speeds == fan_speeds):
                            print(f"[{current_time}] 温度在之前的范围内，跳过设置")
                            break

                        print(f"[{current_time}] 服务器 {ip}：温度范围：{min_temp}-{max_temp} °C")
                        print(f"[{current_time}] 服务器 {ip}：设置风扇转速为 {fan_speeds}")
                        for fan_index, speed in enumerate(fan_speeds):
                            self.set_fan_speed(ip, user, password, fan_index, speed)
                            time.sleep(1)

                        prev_temp_ranges = (min_temp, max_temp)
                        prev_fan_speeds = fan_speeds
                        break
            else:
                print(f"[{current_time}] 服务器 {ip}：没有 CPU 温度数据可用。")

            time.sleep(self.interval)
