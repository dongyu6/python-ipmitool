[English Readme](./README_EN.md)

# python-ipmitool

根据ipmi来监测服务器的CPU温度并根据预定义的温度区间调整风扇转速

## Windows和linux平台通用！！！

## 兼容服务器

经过了本人实践可以正常使用的型号如下，更多型号等待测试，欢迎参与维护！

|  品牌  |  型号   | 是否兼容 | type类型  |
|:----:|:-----:|:----:|:-------:|
| Dell | 730XD |  Y   | dell730 |
| Dell |  730  |  Y   | dell730 |

## 使用方式

> linux需要安装好`ipmitool`
> 
> debain系列使用`apt install -y ipmitool`安装，redhat系列使用`yum install -y ipmitool`安装
> 

1. clone 本项目

    ```
    git clone https://github.com/dongyu6/python-ipmitool.git
    ```
2. 进入本项目路径

    ```
    cd python-ipmitool
    ```
3. 复制 `fan_settings.json.template` 文件为 `fan_settings.json`。

4. 编辑新创建的 `fan_settings.json` 配置文件，其含义如下，需要自己配置ip地址和风扇转速

    > 注意只能用ip地址，不能用域名
    >
    > 注意，添加或删除服务配置的时候，要注意{}不要带多余的逗号，否则会报错json.decoder.JSONDecodeError
    >

    ```
    {
      "auto": true, // 是否自动控制风扇转速，true为自动控制，false为手动控制
      "interval": 60,  // 控制风扇转速的时间间隔，单位为秒
      "log_backup_count": 30, // 日志文件保留天数
      "windows_ipmi_tool_path": ".\\ipmitool\\ipmitool.exe",  // Windows 系统下 ipmitool 工具的路径
      "servers": [  // 服务器列表
        {
          "type": "dell730",  // 服务器类型
          "ip": "192.168.71.90",  // 服务器 IP 地址。如果脚本与服务器在同一台机器运行，可设置为 "local" 以直接执行本地命令。
          "user": "root",  // IPMI 用户名
          "password": "123123",  // IPMI 密码
          "temperature_ranges": [  // 温度范围与对应的风扇转速
            {
              "min_temp": 0,  // 区间最低温度（包括）
              "max_temp": 60,  // 区间最高温度（包括）
              "fan_speeds": [20,20,20,20,20,20]  // 对应风扇转速的列表，每个元素表示一个风扇的转速，单位为百分比
            },
            {
              "min_temp": 61,  // 区间最低温度（包括）
              "max_temp": 80,  // 区间最高温度（包括）
              "fan_speeds": [25,25,25,25,25,25]  // 对应风扇转速的列表，每个元素表示一个风扇的转速，单位为百分比
            }
          ]
        },
        {
          "type": "dell730",
          "ip": "192.168.71.91",
          "user": "root",
          "password": "123123",
          "temperature_ranges": [
            {
              "min_temp": 0,
              "max_temp": 60,
              "fan_speeds": [20,20,20,20,20,20]
            },
            {
              "min_temp": 61,
              "max_temp": 80,
              "fan_speeds": [25,25,25,25,25,25]
            }
          ]
        },
        {
          "type": "dell730",
          "ip": "192.168.71.92",
          "user": "root",
          "password": "123123",
          "temperature_ranges": [
            {
              "min_temp": 0,
              "max_temp": 60,
              "fan_speeds": [20,20,20,20,20,20]
            },
            {
              "min_temp": 61,
              "max_temp": 80,
              "fan_speeds": [25,25,25,25,25,25]
            }
          ]
        }
      ]
    }

    ```
5. 启动项目

    为了方便长期运行，推荐采用后台运行的方式。

    1. **Windows 环境**

        使用 `start /b` 命令让脚本在后台运行：
        ```
        start /b python fancontroller.py
        ```

    2. **Linux 环境**

        使用 `nohup` 和 `&` 让脚本在后台运行，并确保退出终端后进程不被终止：
        ```
        nohup python3 fancontroller.py &
        ```

### 设置为 systemd 服务 (Linux 推荐)

对于需要稳定可靠运行的Linux服务器，强烈建议将本脚本配置为 systemd 服务，以实现开机自启、进程守护等功能。

1.  **创建服务文件**

    使用文本编辑器（如`nano`或`vim`）创建一个新的服务文件：
    ```
    sudo nano /etc/systemd/system/fancontroller.service
    ```

2.  **粘贴服务配置**

    将以下内容粘贴到文件中。**注意：** 您必须将 `User`、`WorkingDirectory` 和 `ExecStart` 中的路径修改为您服务器上的实际路径。

    ```ini
    [Unit]
    Description=Python IPMI Fan Controller
    After=network.target

    [Service]
    Type=simple
    # 如果您使用非root用户运行，请确保该用户有权限执行ipmitool命令
    User=root
    # 此处填写项目的绝对路径
    WorkingDirectory=/path/to/python-ipmitool
    # 此处填写Python解释器和脚本的绝对路径
    ExecStart=/usr/bin/python3 /path/to/python-ipmitool/fancontroller.py
    Restart=always
    RestartSec=3

    [Install]
    WantedBy=multi-user.target
    ```

3.  **重载并启用服务**

    执行以下命令来重载 systemd 配置、启动服务并设置为开机自启。

    ```bash
    # 重新加载 systemd 配置
    sudo systemctl daemon-reload

    # 启动服务
    sudo systemctl start fancontroller.service

    # 检查服务状态，确保没有错误
    sudo systemctl status fancontroller.service

    # 设置服务开机自启
    sudo systemctl enable fancontroller.service
    ```

4.  **查看日志**

    配置为服务后，所有日志（包括错误）都可以通过 `journalctl` 查看：
    ```bash
    journalctl -u fancontroller.service -f
    ```

## 贡献与反馈
欢迎提交 Issue 和 Pull Request 来帮助改进项目。如有任何问题或建议，请通过 GitHub Issues 反馈。

## 许可证
本项目采用 MIT 许可证，详情请参阅 LICENSE 文件。

## 感谢项目

[perryclements/r410-fancontroller: Python fan controller for Dell R410 server (GitHub.com)](https://github.com/perryclements/r410-fancontroller)

[ipmitool/ipmitool: An open-source tool for controlling IPMI-enabled systems (GitHub.com)](https://github.com/ipmitool/ipmitool)