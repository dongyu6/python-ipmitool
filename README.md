# python-ipmitool

根据ipmi来监测服务器的CPU温度并根据预定义的温度区间调整风扇转速

## 兼容服务器

经过了本人实践可以正常使用的型号如下，更多型号等待测试，欢迎参与维护！

|  品牌  |  型号   | 是否兼容 |
|:----:|:-----:|:----:|
| Dell | 730XD |  Y   |
| Dell |  730  |  Y   |

## 使用方式

1. clone 本项目

    ```
    git clone https://github.com/dongyu6/python-ipmitool.git
    ```
2. 进入本项目路径

    ```
    cd python-ipmitool
    ```
3. 编辑fan\_settings.json配置文件，其含义如下，需要自己配置ip地址和风扇转速

    > 注意只能用ip地址，不能用域名
    >
    > 注意，添加或删除服务配置的时候，要注意{}不要带多余的逗号，否则会报错json.decoder.JSONDecodeError
    >

    ```
    {
          "interval": 60,  // 温度检查和风扇速度调整的时间间隔，以秒为单位
          "windows_ipmi_tool_path": ".\\ipmitool\\ipmitool.exe", //ipmitool地址，本项目自带tpmitool.exe，可以不用改，linux也不用改
          "servers": [
            {
              "ip": "192.168.xx.xx",  // 服务器的IP地址
              "user": "root",  // 服务器的用户名
              "password": "xxx"  // 服务器的密码
            },
            {
              "ip": "192.168.xx.xxx",  // 第二台服务器的IP地址
              "user": "root",  // 第二台服务器的用户名
              "password": "xxx"  // 第二台服务器的密码
            },
            {
              "ip": "192.168.xxx.xxx",  // 第三台服务器的IP地址
              "user": "root",  // 第三台服务器的用户名
              "password": "xxx"  // 第三台服务器的密码
            }
          ],
          "temperature_ranges": [
            {
              "min_temp": 0,  // 最低温度（包括）
              "max_temp": 60,  // 最高温度（不包括）
              "fan_speeds": [20, 20, 20, 20, 20, 20]  // 在此温度区间内的风扇速度百分比，分别对应6个风扇
            },
            {
              "min_temp": 61,  // 最低温度（包括）
              "max_temp": 80,  // 最高温度（不包括）
              "fan_speeds": [25, 25, 25, 25, 25, 25]  // 在此温度区间内的风扇速度百分比
            }
          ]
        }
    ```
4. 启动项目

    1. windows环境直接在命令行输入以下命令即可运行

        ```
        bash python fancontroller.py
        ```
    2. linux环境直接在命令行输入以下命令即可运行

        ```
        bash python3 fancontroller.py 
        ```

## 感谢项目

[perryclements/r410-fancontroller: Python fan controller for Dell R410 server (GitHub.com)](https://github.com/perryclements/r410-fancontroller)

[ipmitool/ipmitool: An open-source tool for controlling IPMI-enabled systems (GitHub.com)](https://github.com/ipmitool/ipmitool)