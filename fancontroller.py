import json
import re
import time
import subprocess
from datetime import datetime
import threading
import platform

platform_system = platform.system()

# 全局变量存储JSON数据
data = None

# 读取 JSON 文件并解析内容
def read_json_file(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data

# 执行命令并返回进程的标准输出
def sendcommand(cmdIn):
    if platform_system == 'Windows':
        # 在Windows上执行命令
        p = subprocess.Popen(cmdIn, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             universal_newlines=True, stderr=subprocess.STDOUT, close_fds=True)
    else:
        # 在Linux上执行命令
        p = subprocess.Popen(cmdIn, shell=True, executable="/bin/bash", stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             universal_newlines=True, stderr=subprocess.STDOUT, close_fds=True)
    return p.stdout.read()

# 执行 ipmi 命令，默认使用 ipmitool
def ipmicmd(cmdIn, ipmi_tool_path):
    if platform_system == 'Windows':
        command = f'"{ipmi_tool_path}" {cmdIn}'
    else:
        command = f'ipmitool {cmdIn}'
    output = subprocess.run(command, shell=True, capture_output=True, text=True)
    return sendcommand(command)

# 设置风扇转速
def set_fan_speed(ip, user, password, fan_index, percentage, ipmi_tool_path):
    # 将百分比转换为十六进制字符串
    hex_percentage = format(percentage, '02x')
    # 设置风扇速度命令
    set_speed_cmd = f"-I lanplus -H {ip} -U {user} -P {password} raw 0x30 0x30 0x02 0x{fan_index:02x} 0x{hex_percentage}"
    ipmicmd(set_speed_cmd, ipmi_tool_path)

# 获取 CPU 温度
def get_cpu_temperature(ip, user, password, ipmi_tool_path):
    command = f"-I lanplus -H {ip} -U {user} -P {password} sensor list"
    output = ipmicmd(command, ipmi_tool_path)
    temp_lines = re.findall(r'^Temp\s+\|\s+([\d.]+)\s+\|\s+degrees\s+C', output, re.MULTILINE)
    cpu_temps = [float(temp) for temp in temp_lines]
    return cpu_temps

# 处理单台服务器的温度设置
def process_server(server_info, temperature_ranges, ipmi_tool_path):
    ip = server_info['ip']
    user = server_info['user']
    password = server_info['password']

    # 禁用自动模式
    disable_auto_cmd = f"-I lanplus -H {ip} -U {user} -P {password} raw 0x30 0x30 0x01 0x00"
    ipmicmd(disable_auto_cmd, ipmi_tool_path)

    # 初始化临时变量
    prev_temp_ranges = None
    prev_fan_speeds = None

    while True:
        # 获取 CPU 温度
        cpu_temps = get_cpu_temperature(ip, user, password, ipmi_tool_path)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if cpu_temps:
            avg_temp = sum(cpu_temps) / len(cpu_temps)
            print(f"[{current_time}] Server {ip}: Average CPU temperature: {avg_temp} °C")

            # 查找当前温度所在的温度区间
            for temp_range in temperature_ranges:
                min_temp = temp_range['min_temp']
                max_temp = temp_range['max_temp']
                fan_speeds = temp_range['fan_speeds']

                if min_temp <= avg_temp < max_temp:
                    # 如果当前温度区间和上一次相同，则不需要重新设置风扇转速
                    if (prev_temp_ranges == (min_temp, max_temp)) and (prev_fan_speeds == fan_speeds):
                        print(f"[{current_time}] Temperature is in the previous temperature range, skipping")
                        break

                    print(f"[{current_time}] Server {ip}: Temperature Range: {min_temp}-{max_temp} °C")
                    print(f"[{current_time}] Server {ip}: Set Fans to ", fan_speeds)
                    for fan_index, speed in enumerate(fan_speeds):
                        set_fan_speed(ip, user, password, fan_index, speed, ipmi_tool_path)
                        time.sleep(1)  # 等待一秒钟，以避免发送命令过快

                    # 更新临时变量
                    prev_temp_ranges = (min_temp, max_temp)
                    prev_fan_speeds = fan_speeds
                    break
        else:
            print(f"[{current_time}] Server {ip}: No CPU temperature data available.")

        interval = data['interval']
        time.sleep(interval)  # 每隔指定的时间间隔检查一次温度

# 主函数
def main():
    global data
    data = read_json_file('fan_settings.json')

    # 从 JSON 数据中提取服务器配置信息和风扇设置
    servers = data['servers']
    temperature_ranges = data['temperature_ranges']
    ipmi_tool_path = data.get('windows_ipmi_tool_path', 'ipmitool')  # 获取Windows环境下的ipmitool路径

    # 创建并启动一个线程来处理每台服务器
    threads = []
    for server_info in servers:
        thread = threading.Thread(target=process_server, args=(server_info, temperature_ranges, ipmi_tool_path))
        thread.start()
        threads.append(thread)

    # 等待所有线程结束
    for thread in threads:
        thread.join()

if __name__ == '__main__':
    main()
