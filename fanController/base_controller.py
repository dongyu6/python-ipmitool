import platform
import subprocess
import time
from datetime import datetime

from loguru import logger  # 引入 loguru 模块


class IPMIFanController:
    def __init__(self, servers, interval, windows_ipmi_tool_path, log_file_path, auto=True):
        """
        初始化 IPMI 风扇控制器。

        Args:
            servers (dict): 包含服务器信息的字典。
            interval (int): 检查 CPU 温度的时间间隔（秒）。
            windows_ipmi_tool_path (str): Windows 平台上 IPMI 工具的路径。
            log_file_path (str):  日志文件路径。
            auto (bool): 是否自动模式，True为自动模式，False为手动模式。
        """
        self.platform_system = platform.system()
        if self.platform_system == 'Windows':
            self.ipmi_tool_path = windows_ipmi_tool_path
        else:
            self.ipmi_tool_path = 'ipmitool'
        self.interval = interval
        self.servers = servers
        self.log_file_path = log_file_path
        self.ip = self.servers['ip']
        self.user = self.servers['user']
        self.password = self.servers['password']
        self.auto = auto
        logger.add(self.log_file_path, format="{time:YYYY-MM-DD HH:mm:ss} {message}", level="INFO", encoding="utf-8")  # 配置 loguru

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

    def set_fan_speed(self, fan_index, percentage):
        """
        设置指定风扇的转速。

        Args:
            fan_index (int): 要设置速度的风扇索引。
            percentage (int): 要设置的风扇转速百分比。

        Raises:
            NotImplementedError: 子类必须实现此方法。
        """
        raise NotImplementedError("Method set_fan_speed must be implemented by subclasses")

    def get_cpu_temperature(self):
        """
        获取服务器的 CPU 温度。

        Raises:
            NotImplementedError: 子类必须实现此方法。
        """
        raise NotImplementedError("Method get_cpu_temperature must be implemented by subclasses")

    def set_ipmi_manual_mode(self):
        """
        设置 IPMI 为手动模式。

        Returns:
            str: IPMI 命令的输出。
        """
        command = f'-I lanplus -H {self.ip} -U {self.user} -P {self.password} raw 0x30 0x30 0x01 0x00'
        return self.ipmi_command(command)

    def get_fan_rotational_speed(self):
        """获取 Dell 730 服务器 风扇转速 的方法。

        Returns:
            list: 包含 风扇转速 的列表。
        """
        raise NotImplementedError("Method get_cpu_temperature must be implemented by subclasses")

    def process_server(self):
        """
        处理服务器，监测 CPU 温度并相应调整风扇转速。
        """
        # 设置 IPMI 为手动模式
        self.set_ipmi_manual_mode()

        prev_temp_ranges = None
        prev_fan_speeds = None

        self.monitor_and_adjust_fans(prev_temp_ranges, prev_fan_speeds)

    def monitor_and_adjust_fans(self, prev_temp_ranges, prev_fan_speeds):
        """
        监控并调整风扇转速的方法。

        Args:
            prev_temp_ranges (tuple): 之前的温度范围。
            prev_fan_speeds (list): 之前的风扇转速。
        """
        while True:
            cpu_temps = self.get_cpu_temperature()
            fan_speeds = self.get_fan_rotational_speed()
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if cpu_temps:
                avg_temp = max(cpu_temps)
                max_speed = max(fan_speeds)
                log_message = f"服务器 {self.ip}：CPU 平均温度：{avg_temp}°C, 风扇最大转速{max_speed}"
                logger.info(log_message)  # 使用 loguru 记录日志

                for temp_range in self.servers['temperature_ranges']:
                    min_temp = temp_range['min_temp']
                    max_temp = temp_range['max_temp']
                    fan_speeds = temp_range['fan_speeds']

                    if min_temp <= avg_temp < max_temp:
                        if (prev_temp_ranges == (min_temp, max_temp)) and (prev_fan_speeds == fan_speeds) and max_speed < 15000:
                            log_message = "温度在之前的范围内，跳过设置"
                            logger.info(log_message)  # 使用 loguru 记录日志
                            break

                        log_message = f"设置风扇转速为 {fan_speeds}"
                        logger.info(log_message)  # 使用 loguru 记录日志
                        for fan_index, speed in enumerate(fan_speeds):
                            self.set_fan_speed(fan_index, speed)
                            time.sleep(1)

                        prev_temp_ranges = (min_temp, max_temp)
                        prev_fan_speeds = fan_speeds
                        break
            else:
                log_message = f"服务器 {self.ip}：没有 CPU 温度数据可用。"
                logger.info(log_message)  # 使用 loguru 记录日志

            if not self.auto:
                break

            time.sleep(self.interval)
