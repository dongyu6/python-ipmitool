import re
from .base_controller import IPMIFanController  # 导入基础控制器类

class Dell730FanController(IPMIFanController):
    """Dell730 服务器风扇控制器类，继承自基础控制器类 IPMIFanController。"""

    def set_fan_speed(self, ip, user, password, fan_index, percentage):
        """设置 Dell 730 服务器风扇转速的方法。

        Args:
            ip (str): 服务器 IP 地址。
            user (str): IPMI 用户名。
            password (str): IPMI 密码。
            fan_index (int): 风扇索引。
            percentage (int): 风扇转速百分比。
        """
        hex_percentage = format(percentage, '02x')
        set_speed_cmd = f"-I lanplus -H {ip} -U {user} -P {password} raw 0x30 0x30 0x02 0x{fan_index:02x} 0x{hex_percentage}"
        self.ipmi_command(set_speed_cmd)

    def get_cpu_temperature(self, ip, user, password):
        """获取 Dell 730 服务器 CPU 温度的方法。

        Args:
            ip (str): 服务器 IP 地址。
            user (str): IPMI 用户名。
            password (str): IPMI 密码。

        Returns:
            list: 包含 CPU 温度的列表。
        """
        command = f"-I lanplus -H {ip} -U {user} -P {password} sdr type Temperature"
        output = self.ipmi_command(command)

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

    def start_fan_control(self):
        """启动风扇控制的方法。"""
        self.process_server()
