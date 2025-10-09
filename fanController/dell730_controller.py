import re
import time
import logging

from .base_controller import IPMIFanController  # 导入基础控制器类


class Dell730FanController(IPMIFanController):
    """Dell730 服务器风扇控制器类，继承自基础控制器类 IPMIFanController。"""
    max_fan_rotational_speed = 16000

    def _get_base_command(self):
        """根据IP配置生成基础IPMI命令。"""
        if self.ip == 'local':
            return ""
        else:
            return f"-I lanplus -H {self.ip} -U {self.user} -P {self.password}"

    def set_fan_speed(self, fan_index, percentage):
        """设置 Dell 730 服务器风扇转速的方法。

        Args:
            fan_index (int): 风扇索引。
            percentage (int): 风扇转速百分比。
        """
        hex_percentage = format(percentage, '02x')
        base_cmd = self._get_base_command()
        set_speed_cmd = f"{base_cmd} raw 0x30 0x30 0x02 0x{fan_index:02x} 0x{hex_percentage}"
        self.ipmi_command(set_speed_cmd.strip())

    def get_cpu_temperature(self):
        """获取 Dell 730 服务器 CPU 温度的方法。

        Returns:
            list: 包含 CPU 温度的列表。
        """
        base_cmd = self._get_base_command()
        command = f"{base_cmd} sdr type Temperature"
        output = self.ipmi_command(command.strip())

        temp_list = []
        for line in output.split("\n"):
            items = line.split("|")
            if len(items) > 1 and "ok" in items[2]:
                if "0Eh" in items[1] or "0Fh" in items[1]:
                    temp_match = re.search(r'(\d+)\s+degrees\s+C', items[4])
                    if temp_match:
                        temp = int(temp_match.group(1))
                        temp_list.append(temp)
        return temp_list

    def get_fan_rotational_speed(self):
        """获取 Dell 730 服务器 风扇转速 的方法。

        Returns:
            list: 包含 风扇转速 的列表。
        """
        base_cmd = self._get_base_command()
        command = f"{base_cmd} sdr type fan"
        output = self.ipmi_command(command.strip())

        rpm_values = re.findall(r'\|\s(\d+)\sRPM', output)
        rpm_values = [int(rpm) for rpm in rpm_values]

        return rpm_values

    def _initialize_dell730(self):
        """
        Dell 730 服务器初始化流程。
        """
        # Dell 730 特定初始化：禁用第三方 PCIe 卡的散热响应策略
        self.disable_third_party_pcie_thermal_response()
        # 设置 IPMI 为手动模式
        self.set_ipmi_manual_mode()

    def process_server_loop(self):
        """
        循环模式：持续监测 CPU 温度并相应调整风扇转速。
        重写父类方法以添加 Dell 特定的初始化步骤。
        """
        self._initialize_dell730()

        prev_temp_ranges = None
        prev_fan_speeds = None

        while True:
            result = self.adjust_fans_once(prev_temp_ranges, prev_fan_speeds)
            prev_temp_ranges = result['temp_ranges']
            prev_fan_speeds = result['fan_speeds']

            time.sleep(self.interval)

    def process_server_once(self):
        """
        单次执行模式：执行一次温度检测和风扇调整后退出。
        重写父类方法以添加 Dell 特定的初始化步骤。
        """
        self._initialize_dell730()
        # 执行一次调整
        self.adjust_fans_once()

    def start_fan_control(self):
        """启动风扇控制的方法（循环模式）。"""
        self.process_server_loop()

    def run_once(self):
        """执行一次风扇控制（单次模式）。"""
        self.process_server_once()

    def set_ipmi_manual_mode(self):
        """
        设置 IPMI 为手动模式。

        Returns:
            str: IPMI 命令的输出。
        """
        base_cmd = self._get_base_command()
        command = f'{base_cmd} raw 0x30 0x30 0x01 0x00'
        return self.ipmi_command(command.strip())

    def set_ipmi_auto_mode(self):
        """
        设置 IPMI 为自动模式。

        Returns:
            str: IPMI 命令的输出。
        """
        base_cmd = self._get_base_command()
        command = f'{base_cmd} raw 0x30 0x30 0x01 0x01'
        return self.ipmi_command(command.strip())

    def disable_third_party_pcie_thermal_response(self):
        """
        禁用第三方 PCIe 卡的散热响应策略。
        这是 Dell 服务器风扇控制的必要初始化步骤。

        Returns:
            str: IPMI 命令的输出。成功时应返回 "16 05 00 00 00"。
        """
        base_cmd = self._get_base_command()
        command = f'{base_cmd} raw 0x30 0xce 0x00 0x16 0x05 0x00 0x00 0x00 0x05 0x00 0x01 0x00 0x00'
        output = self.ipmi_command(command.strip())

        # 记录命令执行结果
        if '16 05 00 00 00' in output.replace(' ', '').replace('\n', ''):
            self.logger.info(f"服务器 {self.ip}: 成功禁用第三方 PCIe 卡散热响应策略")
        else:
            self.logger.warning(f"服务器 {self.ip}: 禁用第三方 PCIe 卡散热响应策略可能失败，返回: {output.strip()}")

        return output
