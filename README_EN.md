[中文文档](./README.md)

# Python IPMI Fan Controller

A Python script to monitor server CPU temperature via IPMI and adjust fan speeds according to predefined temperature ranges.

## Cross-Platform Support (Windows & Linux)!

## Compatible Servers

The following models have been tested and are confirmed to work. More models are pending testing; contributions are welcome!

| Brand | Model | Compatible | Type Name |
|:-----:|:-----:|:----------:|:---------:|
| Dell  | 730XD |     Y      | `dell730` |
| Dell  | 730   |     Y      | `dell730` |

## How to Use

> On Linux, `ipmitool` must be installed.
> 
> For Debian-based systems, install it with `apt install -y ipmitool`.
> For Red Hat-based systems, use `yum install -y ipmitool`.

1.  **Clone the project**

    ```
    git clone https://github.com/dongyu6/python-ipmitool.git
    ```

2.  **Navigate to the project directory**

    ```
    cd python-ipmitool
    ```

3.  **Copy the template file** `fan_settings.json.template` to `fan_settings.json`.

4.  **Edit the newly created `fan_settings.json`** file. The meaning of each field is as follows. You need to configure the IP addresses and fan speeds yourself.

    > Note: Only IP addresses are supported, not domain names.
    > 
    > Note: When adding or removing server configurations, be careful not to leave a trailing comma `}` inside the last `}` of a list, as this will cause a `json.decoder.JSONDecodeError`.

    ```json
    {
      "auto": true, // true for automatic fan control, false for manual.
      "interval": 60,  // The interval in seconds for checking temperature and adjusting fan speed.
      "log_backup_count": 30, // Number of days to retain log files.
      "windows_ipmi_tool_path": ".\\ipmitool\\ipmitool.exe",  // Path to the ipmitool executable on Windows.
      "servers": [  // List of servers to manage.
        {
          "type": "dell730",  // Server type.
          "ip": "192.168.71.90",  // Server IP address. Set to "local" if the script is running on the target machine.
          "user": "root",  // IPMI username.
          "password": "123123",  // IPMI password.
          "temperature_ranges": [  // List of temperature ranges and corresponding fan speeds.
            {
              "min_temp": 0,  // Minimum temperature of the range (inclusive).
              "max_temp": 60,  // Maximum temperature of the range (inclusive).
              "fan_speeds": [20,20,20,20,20,20]  // List of fan speeds in percent for this range.
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

5.  **Run the Project**

    For long-term operation, it is recommended to run the script as a background process.

    1.  **On Windows**

        Use the `start /b` command to run the script in the background:
        ```
        start /b python fancontroller.py
        ```

    2.  **On Linux**

        Use `nohup` and `&` to run the script in the background and ensure it keeps running after you close the terminal:
        ```
nohup python3 fancontroller.py &
        ```

### Setup as a systemd Service (Linux Recommended)

For reliable operation on a Linux server, setting up a systemd service is highly recommended. This provides features like auto-start on boot and process supervision.

1.  **Create the Service File**

    Use a text editor (like `nano` or `vim`) to create a new service file:
    ```
    sudo nano /etc/systemd/system/fancontroller.service
    ```

2.  **Paste the Service Configuration**

    Paste the following content into the file. **Note:** You must replace the paths for `User`, `WorkingDirectory`, and `ExecStart` with the actual paths on your server.

    ```ini
    [Unit]
    Description=Python IPMI Fan Controller
    After=network.target

    [Service]
    Type=simple
    # If you use a non-root user, ensure they have permissions for ipmitool.
    User=root
    # Absolute path to the project directory.
    WorkingDirectory=/path/to/python-ipmitool
    # Absolute path to the Python interpreter and the script.
    ExecStart=/usr/bin/python3 /path/to/python-ipmitool/fancontroller.py
    Restart=always
    RestartSec=3

    [Install]
    WantedBy=multi-user.target
    ```

3.  **Reload and Enable the Service**

    Run the following commands to reload the systemd configuration, start the service, and enable it to start on boot.

    ```bash
    # Reload the systemd configuration
    sudo systemctl daemon-reload

    # Start the service
    sudo systemctl start fancontroller.service

    # Check the service status to ensure there are no errors
    sudo systemctl status fancontroller.service

    # Enable the service to start automatically on boot
    sudo systemctl enable fancontroller.service
    ```

4.  **View Logs**

    Once configured as a service, all output (including errors) can be viewed with `journalctl`:
    ```bash
    journalctl -u fancontroller.service -f
    ```

## Contributing and Feedback

Contributions via Issues and Pull Requests are welcome to help improve the project. If you have any questions or suggestions, please provide feedback through GitHub Issues.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgements

- [perryclements/r410-fancontroller: Python fan controller for Dell R410 server (GitHub.com)](https://github.com/perryclements/r410-fancontroller)
- [ipmitool/ipmitool: An open-source tool for controlling IPMI-enabled systems (GitHub.com)](https://github.com/ipmitool/ipmitool)
