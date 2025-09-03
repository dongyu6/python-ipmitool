import re
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

    def start_fan_control(self):
        """启动风扇控制的方法。
        使用self.auto来判断是否自动模式。
        """
        import os
        if not os.path.exists(self.log_file_path):
            os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
            open(self.log_file_path, 'a').close()
        self.process_server()

    def set_ipmi_manual_mode(self):
        """
        设置 IPMI 为手动模式。

        Returns:
            str: IPMI 命令的输出。
        """
        base_cmd = self._get_base_command()
        command = f'{{base_cmd}} raw 0x30 0x30 0x01 0x00'
        return self.ipmi_command(command.strip())

    def set_ipmi_auto_mode(self):
        """
        设置 IPMI 为自动模式。

        Returns:
            str: IPMI 命令的输出。
        """
        base_cmd = self._get_base_command()
        command = f'{{base_cmd}} raw 0x30 0x30 0x01 0x01'
        return self.ipmi_command(command.strip())
