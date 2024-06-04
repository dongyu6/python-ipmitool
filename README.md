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

1. clone 本项目

    ```
    git clone https://github.com/dongyu6/python-ipmitool.git
    ```
2. 进入本项目路径

    ```
    cd python-ipmitool
    ```
3. 编辑`fan_settings.json`配置文件，其含义如下，需要自己配置ip地址和风扇转速

    > 注意只能用ip地址，不能用域名
    >
    > 注意，添加或删除服务配置的时候，要注意{}不要带多余的逗号，否则会报错json.decoder.JSONDecodeError
    >

    ```
    {
      "interval": 60,  // 控制风扇转速的时间间隔，单位为秒
      "windows_ipmi_tool_path": ".\\ipmitool\\ipmitool.exe",  // Windows 系统下 ipmitool 工具的路径
      "servers": [  // 服务器列表
        {
          "type": "dell730",  // 服务器类型
          "ip": "192.168.71.90",  // 服务器 IP 地址
          "user": "root",  // IPMI 用户名
          "password": "123123",  // IPMI 密码
          "temperature_ranges": [  // 温度范围与对应的风扇转速
            {
              "min_temp": 0,  // 区间最低温度（包括）
              "max_temp": 60,  // 区间最高温度（不包括）
              "fan_speeds": [20,20,20,20,20,20]  // 对应风扇转速的列表，每个元素表示一个风扇的转速，单位为百分比
            },
            {
              "min_temp": 61,  // 区间最低温度（包括）
              "max_temp": 80,  // 区间最高温度（不包括）
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
4. 启动项目

    1. windows环境直接在命令行输入以下命令即可运行

        ```
        python fancontroller.py
        ```
    2. linux环境直接在命令行输入以下命令即可运行

        ```
        python3 fancontroller.py 
        ```

## 感谢项目

[perryclements/r410-fancontroller: Python fan controller for Dell R410 server (GitHub.com)](https://github.com/perryclements/r410-fancontroller)

[ipmitool/ipmitool: An open-source tool for controlling IPMI-enabled systems (GitHub.com)](https://github.com/ipmitool/ipmitool)