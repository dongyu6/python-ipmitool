import platform
import subprocess
import time
import logging
from datetime import datetime

class IPMIFanController:
    def __init__(self, servers, interval, windows_ipmi_tool_path, logger, auto=True, alert_config=None):
        """
        初始化 IPMI 风扇控制器。

        Args:
            servers (dict): 包含服务器信息的字典。
            interval (int): 检查 CPU 温度的时间间隔（秒）。
            windows_ipmi_tool_path (str): Windows 平台上 IPMI 工具的路径。
            logger (logging.Logger): 配置好的日志记录器实例。
            auto (bool): 是否自动模式，True为自动模式，False为手动模式。
            alert_config (dict, optional): 告警配置字典。
        """
        self.platform_system = platform.system()
        if self.platform_system == 'Windows':
            self.ipmi_tool_path = windows_ipmi_tool_path
        else:
            self.ipmi_tool_path = 'ipmitool'
        self.interval = interval
        self.servers = servers
        self.logger = logger
        self.ip = self.servers['ip']
        self.user = self.servers['user']
        self.password = self.servers['password']
        self.auto = auto

        # 统计信息
        self.start_time = None
        self.adjustment_count = 0
        self.last_cpu_temp = None
        self.last_check_time = None

        # 告警配置
        self.alert_config = alert_config or {}
        self.alert_enabled = self.alert_config.get('enabled', False)
        self.fan_speed_threshold = self.alert_config.get('fan_speed_threshold', 10000)
        self.max_failed_attempts = self.alert_config.get('max_failed_attempts', 3)
        self.failed_attempts = 0
        self.last_alert_time = None
        self.email_notifier = None

        # 初始化邮件通知器（如果启用）
        if self.alert_enabled:
            try:
                from utils.email_notifier import EmailNotifier
                email_config = self.alert_config.get('email', {})
                self.email_notifier = EmailNotifier(email_config, logger)
                self.logger.info(f"服务器 {self.ip}: 邮件告警功能已启用 (阈值: {self.fan_speed_threshold} RPM, 失败次数: {self.max_failed_attempts})")
            except Exception as e:
                self.logger.error(f"初始化邮件通知器失败: {str(e)}")
                self.alert_enabled = False

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

    def adjust_fans_once(self, prev_temp_ranges=None, prev_fan_speeds=None):
        """
        单次检测温度并调整风扇转速（不循环）。

        Args:
            prev_temp_ranges (tuple, optional): 之前的温度范围。
            prev_fan_speeds (list, optional): 之前的风扇转速。

        Returns:
            dict: 包含当前状态信息的字典 {
                'temp_ranges': (min_temp, max_temp) or None,
                'fan_speeds': [速度列表] or None,
                'cpu_temp': 当前最高CPU温度,
                'max_fan_speed': 当前最高风扇转速
            }
        """
        check_start_time = time.time()
        cpu_temps = self.get_cpu_temperature()
        current_fan_speeds = self.get_fan_rotational_speed()

        result = {
            'temp_ranges': None,
            'fan_speeds': None,
            'cpu_temp': None,
            'max_fan_speed': None
        }

        if cpu_temps:
            max_temp_value = max(cpu_temps)
            min_temp_value = min(cpu_temps)
            avg_temp_value = sum(cpu_temps) // len(cpu_temps)
            max_fan_speed = max(current_fan_speeds)
            min_fan_speed = min(current_fan_speeds)
            result['cpu_temp'] = max_temp_value
            result['max_fan_speed'] = max_fan_speed

            # 计算温度变化
            temp_change_str = ""
            if self.last_cpu_temp is not None:
                temp_delta = max_temp_value - self.last_cpu_temp
                if temp_delta > 0:
                    temp_change_str = f" | 变化: +{temp_delta}°C ↑"
                    if temp_delta >= 10:
                        temp_change_str += " [警告: 温度快速上升!]"
                elif temp_delta < 0:
                    temp_change_str = f" | 变化: {temp_delta}°C ↓"
                else:
                    temp_change_str = f" | 变化: 持平 →"

            # 计算实际检测间隔
            interval_str = ""
            if self.last_check_time is not None:
                actual_interval = time.time() - self.last_check_time
                interval_str = f" | 检测间隔: {actual_interval:.1f}秒"

            # 详细日志：显示所有 CPU 温度和风扇转速
            cpu_temps_str = ', '.join([f"{temp}°C" for temp in cpu_temps])
            fan_speeds_str = ', '.join([f"{speed} RPM" for speed in current_fan_speeds])

            self.logger.info("=" * 80)
            self.logger.info(f"服务器 {self.ip} 状态检测:")
            self.logger.info(f"  CPU 温度: [{cpu_temps_str}]")
            self.logger.info(f"    └─ 最低: {min_temp_value}°C | 平均: {avg_temp_value}°C | 最高: {max_temp_value}°C{temp_change_str}")
            self.logger.info(f"  风扇转速: [{fan_speeds_str}]")
            self.logger.info(f"    └─ 最低: {min_fan_speed} RPM | 最高: {max_fan_speed} RPM")

            # 温度过高警告
            temp_threshold_warning = 75  # 可配置的警告阈值
            temp_threshold_critical = 85  # 可配置的严重阈值
            if max_temp_value >= temp_threshold_critical:
                self.logger.warning(f"  ⚠️  严重警告: CPU 温度过高 ({max_temp_value}°C >= {temp_threshold_critical}°C)!")
            elif max_temp_value >= temp_threshold_warning:
                self.logger.warning(f"  ⚠️  警告: CPU 温度较高 ({max_temp_value}°C >= {temp_threshold_warning}°C)")

            # 风扇转速异常检测（告警前的检查）
            if max_fan_speed >= self.fan_speed_threshold:
                self.logger.warning(f"  ⚠️  风扇转速异常: {max_fan_speed} RPM (阈值: {self.fan_speed_threshold} RPM)")

                # 如果启用告警，检查是否需要发送告警邮件
                if self.alert_enabled:
                    self.failed_attempts += 1
                    self.logger.warning(f"  风扇调节失败计数: {self.failed_attempts}/{self.max_failed_attempts}")

                    # 连续失败次数达到阈值，发送告警邮件
                    if self.failed_attempts >= self.max_failed_attempts:
                        # 避免频繁发送邮件，至少间隔1小时
                        current_time = time.time()
                        should_send = True
                        if self.last_alert_time is not None:
                            time_since_last_alert = current_time - self.last_alert_time
                            if time_since_last_alert < 3600:  # 1小时
                                should_send = False
                                self.logger.info(f"  距离上次告警仅 {time_since_last_alert/60:.1f} 分钟，跳过邮件发送")

                        if should_send and self.email_notifier:
                            self.logger.warning(f"  ⚠️⚠️⚠️  连续 {self.failed_attempts} 次调节失败，发送告警邮件！")
                            subject = f"🚨 IPMI 风扇控制器告警 - 服务器 {self.ip}"
                            success = self.email_notifier.send_alert(
                                subject=subject,
                                server_ip=self.ip,
                                cpu_temps=cpu_temps,
                                fan_speeds=current_fan_speeds,
                                failed_attempts=self.failed_attempts,
                                threshold=self.fan_speed_threshold
                            )
                            if success:
                                self.last_alert_time = current_time
                                # 发送成功后重置计数器，避免重复告警
                                self.failed_attempts = 0
            else:
                # 风扇转速正常，重置失败计数
                if self.failed_attempts > 0:
                    self.logger.info(f"  风扇转速已恢复正常 ({max_fan_speed} RPM < {self.fan_speed_threshold} RPM)，重置失败计数")
                    self.failed_attempts = 0

            for temp_range in self.servers['temperature_ranges']:
                min_temp = temp_range['min_temp']
                max_temp = temp_range['max_temp']
                fan_speeds = temp_range['fan_speeds']

                if min_temp <= max_temp_value <= max_temp:
                    if (prev_temp_ranges == (min_temp, max_temp)) and (prev_fan_speeds == fan_speeds) and max_fan_speed < 15000:
                        self.logger.info(f"  动作: 温度在范围 [{min_temp}-{max_temp}°C] 内，风扇转速保持不变")
                        result['temp_ranges'] = (min_temp, max_temp)
                        result['fan_speeds'] = fan_speeds
                    else:
                        fan_speeds_percent_str = ', '.join([f"{speed}%" for speed in fan_speeds])
                        self.logger.info(f"  动作: 温度 {max_temp_value}°C 在范围 [{min_temp}-{max_temp}°C]，设置风扇转速为 [{fan_speeds_percent_str}]")

                        for fan_index, speed in enumerate(fan_speeds):
                            self.set_fan_speed(fan_index, speed)
                            time.sleep(1)

                        self.adjustment_count += 1
                        self.logger.info(f"  风扇调整完成 (总调整次数: {self.adjustment_count})")

                        result['temp_ranges'] = (min_temp, max_temp)
                        result['fan_speeds'] = fan_speeds
                    break

            # 更新状态
            self.last_cpu_temp = max_temp_value
            self.last_check_time = time.time()

            # 性能统计
            check_duration = time.time() - check_start_time
            self.logger.info(f"  性能: 检测耗时 {check_duration:.2f}秒{interval_str}")

            # 运行时统计（仅循环模式）
            if self.start_time is not None:
                uptime = time.time() - self.start_time
                uptime_hours = uptime / 3600
                if uptime_hours >= 1:
                    self.logger.info(f"  统计: 运行时长 {uptime_hours:.1f}小时 | 调整次数 {self.adjustment_count}")

        else:
            self.logger.error(f"服务器 {self.ip}: 没有 CPU 温度数据可用！")

        return result

    def process_server_loop(self):
        """
        循环模式：持续监测 CPU 温度并相应调整风扇转速。
        """
        # 设置 IPMI 为手动模式
        self.set_ipmi_manual_mode()

        # 初始化统计信息
        self.start_time = time.time()
        self.logger.info(f"服务器 {self.ip}: 循环控制模式已启动，检测间隔 {self.interval} 秒")

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
        适合被外部调度工具（cron、systemd timer 等）调用。
        """
        # 设置 IPMI 为手动模式
        self.set_ipmi_manual_mode()

        # 执行一次调整
        self.adjust_fans_once()
