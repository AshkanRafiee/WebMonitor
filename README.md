# WebMonitor

WebMonitor is a Python script for monitoring the accessibility of websites and sending alerts if necessary. It is designed to be configurable using a YAML file and can be used to keep an eye on the availability of your websites over the internet.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Usage](#usage)
- [Customization](#customization)
- [Contributing](#contributing)
- [License](#license)

## Features

- Monitor the accessibility of multiple websites concurrently.
- Send alerts to Rocket.Chat when a website becomes inaccessible (configurable).
- Retain logs or overwrite them for each run (configurable).
- Manage the size of the log file and clear it when it exceeds a specified limit (configurable).
- Customize the number of concurrent requests and request timeout.
- Define global and per-website accessibility texts for checking website availability.
- Run monitoring for a specified number of iterations or continuously.

## Requirements

- Python 3.7 or higher
- [aiohttp](https://docs.aiohttp.org/en/stable/index.html) library for asynchronous HTTP requests
- [PyYAML](https://pyyaml.org/) library for parsing YAML configuration files

You can install the required packages using `pip`:

```bash
pip install -r requirements.txt
```

## Getting Started

### Installation

1. Clone this repository to your local machine:

```bash
git clone https://github.com/AshkanRafiee/WebMonitor.git
```

2. Navigate to the project directory:

```bash
cd WebMonitor
```

### Configuration

1. Create a YAML configuration file named `config.yaml` with the following structure:

```yaml
# Rocket.Chat webhook URL for sending alerts
webhook_url: 'https://rocketchat-webhook-url'

# Flag to control sending of alerts
send_alerts: false

# Flag to retain logs or overwrite them for each run
retain_logs: true

# Flag to check and manage the size of the log file
check_file_size: true

# Maximum file size in megabytes (MB) before log file is cleared (Default: 2GB)
max_file_size_mb: 2048

# Number of concurrent requests to make for WebMonitoring
concurrent_requests: 10

# Timeout value in seconds for each HTTP request
timeout: 10

# Global accessibility_texts to be used by default
global_accessibility_texts:
  - "some text 1"
  - "some text 2"

# List of allowed websites to monitor
allowed_websites:
  - url: 'https://example.com'
  - url: 'https://example2.com'

# List of disallowed websites to monitor
disallowed_websites:
  - url: 'https://example3.com'
    accessibility_texts:
      - "Custom text for example.com"
  - url: 'https://example4.com'
  - url: 'https://example5.com'

# Number of times to run the monitoring (use -1 for continuous monitoring)
num_runs: 2

# Delay in seconds between monitoring iterations (use 0 for immediate rerun)
iteration_delay: 5  # 2 minutes
```

Replace `'https://rocketchat-webhook-url'` with your Rocket.Chat webhook URL and customize the other configuration settings as needed.

## Usage

To run the WebMonitor, execute the following command in your terminal:

```bash
python webmonitor.py
```

The script will start monitoring the specified websites based on your configuration. It will run for the specified number of iterations with a delay between iterations or continue running indefinitely if configured as such.

You will see log messages in the terminal indicating the status of each website being monitored.

## Customization

You can customize the behavior of the WebMonitor by editing the `config.yaml` file. Here are some key customization options:

- **Webhook URL**: Set the `webhook_url` to enable sending alerts to Rocket.Chat.

- **Logging**: Control whether to retain logs or overwrite them for each run using the `retain_logs` option. You can also set a maximum log file size (`max_file_size_mb`) to manage log file size.

- **Concurrent Requests**: Adjust the number of concurrent requests (`concurrent_requests`) and request timeout (`timeout`) based on your requirements.

- **Website Accessibility**: Define global accessibility texts (`global_accessibility_texts`) that are checked by default for all websites. Customize the list of allowed and disallowed websites with their respective URLs and accessibility texts.

- **Monitoring Duration**: Specify the number of times to run the monitoring with the `num_runs` option. Use `-1` for continuous monitoring. Set the delay between monitoring iterations with `iteration_delay`.

## Contributing

Contributions to this project are welcome! If you have suggestions, improvements, or bug fixes, please open an issue or create a pull request. For major changes, please discuss them in the issue first.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
