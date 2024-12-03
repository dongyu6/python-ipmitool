import os
import subprocess
from datetime import datetime
import time
import platform

class IPMIFanController:
    def __init__(self, servers, interval, windows_ipmi_tool_path,log_file_path):
        """
        初始化 IPMI 风扇控制器。

        Args:
            servers (dict): 包含服务器信息的字典。
            interval (int): 检查 CPU 温度的时间间隔（秒）。
            windows_ipmi_tool_path (str): Windows 平台上 IPMI 工具的路径。
            log_file_path (str):  日志文件路径。

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
        self.log_file_path=log_file_path

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

    def log_to_file(self, message):
        """
        将日志信息写入日志文件。

        Args:
            message (str): 要写入日志文件的信息。
        """
        if not os.path.exists(self.log_file_path):
            with open(self.log_file_path, 'w', encoding='utf-8') as log_file:
                log_file.write("日志开始\n")

        with open(self.log_file_path, 'a', encoding='utf-8') as log_file:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"[{current_time}] {message}\n")

    def set_ipmi_manual_mode(self, ip, user, password):
        """
        设置 IPMI 为手动模式。

        Args:
            ip (str): 服务器的 IP 地址。
            user (str): IPMI 认证的用户名。
            password (str): IPMI 认证的密码。

        Returns:
            str: IPMI 命令的输出。
        """
        command = f'-I lanplus -H {ip} -U {user} -P {password} raw 0x30 0x30 0x01 0x00'
        return self.ipmi_command(command)

    def get_fan_rotational_speed(self, ip, user, password):
        """获取 Dell 730 服务器 风扇转速 的方法。

        Args:
            ip (str): 服务器 IP 地址。
            user (str): IPMI 用户名。
            password (str): IPMI 密码。

        Returns:
            list: 包含 风扇转速 的列表。
        """
        raise NotImplementedError("Method get_cpu_temperature must be implemented by subclasses")

    def process_server(self):
        """
        处理服务器，监测 CPU 温度并相应调整风扇转速。
        """
        ip = self.servers['ip']
        user = self.servers['user']
        password = self.servers['password']

        # 设置 IPMI 为手动模式
        self.set_ipmi_manual_mode(ip, user, password)

        prev_temp_ranges = None
        prev_fan_speeds = None

        while True:
            cpu_temps = self.get_cpu_temperature(ip, user, password)
            fan_speeds=self.get_fan_rotational_speed(ip,user,password)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if cpu_temps:
                avg_temp = sum(cpu_temps) / len(cpu_temps)
                avg_speed=sum(fan_speeds) / len(fan_speeds)
                log_message = f"服务器 {ip}：CPU 平均温度：{avg_temp}°C, 风扇平均转速{avg_speed}"
                self.log_to_file(log_message)
                print(f"[{current_time}] {log_message}")

                for temp_range in self.servers['temperature_ranges']:
                    min_temp = temp_range['min_temp']
                    max_temp = temp_range['max_temp']
                    fan_speeds = temp_range['fan_speeds']

                    if min_temp <= avg_temp < max_temp or avg_speed>15000:
                        if (prev_temp_ranges == (min_temp, max_temp)) and (prev_fan_speeds == fan_speeds):
                            log_message = "温度在之前的范围内，跳过设置"
                            self.log_to_file(log_message)
                            print(f"[{current_time}] {log_message}")
                            break

                        log_message = f"设置风扇转速为 {fan_speeds}"
                        self.log_to_file(log_message)
                        print(f"[{current_time}] {log_message}")
                        for fan_index, speed in enumerate(fan_speeds):
                            self.set_fan_speed(ip, user, password, fan_index, speed)
                            time.sleep(1)

                        prev_temp_ranges = (min_temp, max_temp)
                        prev_fan_speeds = fan_speeds
                        break
            else:
                log_message = f"服务器 {ip}：没有 CPU 温度数据可用。"
                self.log_to_file(log_message)
                print(f"[{current_time}] {log_message}")

            time.sleep(self.interval)