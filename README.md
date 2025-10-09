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

3. 安装依赖

    ```
    pip install -r requirements.txt
    ```

4. 复制 `fan_settings.yaml.template` 文件为 `fan_settings.yaml`。

    ```bash
    # Linux/Mac
    cp fan_settings.yaml.template fan_settings.yaml

    # Windows
    copy fan_settings.yaml.template fan_settings.yaml
    ```

5. 编辑新创建的 `fan_settings.yaml` 配置文件，其含义如下，需要自己配置ip地址和风扇转速

    > 注意只能用ip地址，不能用域名
    >
    > **新功能**: 支持邮件告警，当风扇调节连续失败时自动发送告警邮件（默认关闭）
    >

    ```yaml
    # IPMI 风扇控制器配置文件

    # 是否自动控制风扇转速，true 为自动控制，false 为手动控制
    auto: true

    # 控制风扇转速的时间间隔，单位为秒
    interval: 60

    # 日志文件保留天数
    log_backup_count: 30

    # Windows 系统下 ipmitool 工具的路径
    windows_ipmi_tool_path: ".\\ipmitool\\ipmitool.exe"

    # 告警配置（可选，默认关闭）
    alert:
      enabled: false                    # 是否启用邮件告警，默认 false
      fan_speed_threshold: 10000        # 风扇转速异常阈值（RPM）
      max_failed_attempts: 3            # 连续失败次数阈值
      email:
        smtp_server: "smtp.gmail.com"   # SMTP 服务器
        smtp_port: 587                  # SMTP 端口
        use_tls: true                   # 是否使用 TLS
        sender_email: "your_email@gmail.com"
        sender_password: "your_app_password"
        recipient_emails:
          - "admin@example.com"

    # 服务器列表
    servers:
      - type: dell730                    # 服务器类型
        ip: "192.168.71.90"              # 服务器 IP 地址。如果脚本与服务器在同一台机器运行，可设置为 "local" 以直接执行本地命令
        user: root                       # IPMI 用户名
        password: "123123"               # IPMI 密码
        temperature_ranges:              # 温度范围与对应的风扇转速
          - min_temp: 0                  # 区间最低温度（包括）
            max_temp: 60                 # 区间最高温度（包括）
            fan_speeds: [20, 20, 20, 20, 20, 20]  # 对应风扇转速的列表，单位为百分比
          - min_temp: 61
            max_temp: 80
            fan_speeds: [25, 25, 25, 25, 25, 25]

      - type: dell730
        ip: "192.168.71.91"
        user: root
        password: "123123"
        temperature_ranges:
          - min_temp: 0
            max_temp: 60
            fan_speeds: [20, 20, 20, 20, 20, 20]
          - min_temp: 61
            max_temp: 80
            fan_speeds: [25, 25, 25, 25, 25, 25]

      - type: dell730
        ip: "192.168.71.92"
        user: root
        password: "123123"
        temperature_ranges:
          - min_temp: 0
            max_temp: 60
            fan_speeds: [20, 20, 20, 20, 20, 20]
          - min_temp: 61
            max_temp: 80
            fan_speeds: [25, 25, 25, 25, 25, 25]
    ```


6. 启动项目

    项目提供两种运行模式：

    ## 模式一：循环控制模式（推荐用于长期运行）

    程序内部循环监控温度并调整风扇，适合作为后台服务运行。

    **前台运行（调试用）**
    ```bash
    # Windows
    python fancontroller.py

    # Linux
    python3 fancontroller.py
    ```

    **后台运行**
    ```bash
    # Windows
    start /b python fancontroller.py

    # Linux
    nohup python3 fancontroller.py &
    ```

    ## 模式二：单次执行模式（推荐用于外部调度）

    执行一次温度检测和风扇调整后退出，适合被 cron、systemd timer 等外部调度工具定时调用。

    **直接执行**
    ```bash
    # Windows
    python fancontroller_once.py

    # Linux
    python3 fancontroller_once.py
    ```

    **使用 cron 定时执行（Linux）**
    ```bash
    # 编辑 crontab
    crontab -e

    # 每 10 分钟执行一次
    */10 * * * * /usr/bin/python3 /path/to/python-ipmitool/fancontroller_once.py
    ```

    **使用 Windows 任务计划程序**
    ```powershell
    # 创建每 10 分钟执行一次的任务
    schtasks /create /tn "IPMI Fan Controller" /tr "python C:\path\to\python-ipmitool\fancontroller_once.py" /sc minute /mo 10
    ```

### 邮件告警功能（可选）

项目支持在风扇调节失败时自动发送告警邮件，**默认关闭**。

#### 启用步骤

1. **配置邮箱信息**

    编辑 `fan_settings.yaml`，设置 `alert.enabled: true` 并填写邮箱配置：

    ```yaml
    alert:
      enabled: true                     # 启用邮件告警
      fan_speed_threshold: 10000        # 风扇转速阈值（RPM）
      max_failed_attempts: 3            # 连续失败3次后发送邮件
      email:
        smtp_server: "smtp.gmail.com"
        smtp_port: 587
        use_tls: true
        sender_email: "your_email@gmail.com"
        sender_password: "your_app_password"  # Gmail 使用应用专用密码
        recipient_emails:
          - "admin@example.com"
          - "alert@example.com"  # 支持多个收件人
    ```

2. **Gmail 邮箱配置**

    - 开启两步验证
    - 生成应用专用密码: https://myaccount.google.com/apppasswords
    - 使用应用专用密码替代 Gmail 密码

3. **其他邮箱服务器**

    | 邮箱服务 | SMTP 服务器 | 端口 | TLS |
    |---------|------------|------|-----|
    | Gmail | smtp.gmail.com | 587 | true |
    | QQ 邮箱 | smtp.qq.com | 587 | true |
    | 163 邮箱 | smtp.163.com | 465 | false (使用SSL) |
    | Outlook | smtp-mail.outlook.com | 587 | true |

#### 告警触发条件

- 风扇转速超过配置的阈值（默认 10000 RPM）
- 连续检测失败达到配置的次数（默认 3 次）
- 为避免邮件轰炸，同一服务器告警邮件间隔至少 1 小时

#### 告警邮件内容

邮件包含：
- 服务器 IP 地址
- 当前所有 CPU 温度
- 当前所有风扇转速
- 连续失败次数
- 可能的故障原因和建议操作

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