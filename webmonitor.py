import asyncio
import aiohttp
import logging
import yaml
import os
import itertools

class WebsiteMonitor:
    """Monitors the accessibility of websites and sends alerts if necessary."""

    def __init__(self, config_file):
        """
        Initialize the WebsiteMonitor.

        Args:
            config_file (str): Path to the configuration file (in YAML format).

        Raises:
            FileNotFoundError: If the config file is not found.
            Exception: If an error occurs while loading the config.

        """
        self.config_file = config_file
        self.load_config()
        self.logger = self.setup_logging()
        self.websites = self.load_websites_from_file()

    def load_config(self):
        """
        Load configuration settings from the YAML config file.

        Raises:
            FileNotFoundError: If the config file is not found.
            Exception: If an error occurs while loading the config.

        """
        try:
            with open(self.config_file, 'r') as file:
                config = yaml.safe_load(file)
                self.webhook_url = config.get('webhook_url', '')
                self.send_alerts = config.get('send_alerts', False)
                self.retain_logs = config.get('retain_logs', True)
                self.check_file_size = config.get('check_file_size', False)
                max_file_size_mb = config.get('max_file_size_mb', 2048)  # Default: 2GB
                self.max_file_size = max_file_size_mb * 1024 * 1024  # Convert MB to bytes
                self.concurrent_requests = config.get('concurrent_requests', 10)  # Default: 10 concurrent requests
                self.timeout = config.get('timeout', 10)  # Default: 10 seconds
                self.global_accessibility_texts = config.get('global_accessibility_texts', [])
                self.num_runs = config.get('num_runs', 1)
                self.iteration_delay = config.get('iteration_delay', 0)
        except FileNotFoundError:
            print(f'Config file "{self.config_file}" not found.')
            raise
        except Exception as e:
            print(f'Error occurred while loading the config from file "{self.config_file}": {str(e)}')
            raise

    def setup_logging(self):
        """
        Configure logging for the WebsiteMonitor.

        Returns:
            logging.Logger: The configured logger object.

        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            filename='app.log',
            filemode='a' if self.retain_logs else 'w'
        )

        logger = logging.getLogger(__name__.replace('__main__', ''))

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

        return logger

    async def send_alert_to_rocketchat(self, website):
        """
        Send an alert to Rocket.Chat if send_alerts is enabled.

        Args:
            website (str): The website URL.

        """
        if not self.send_alerts:
            return

        message = f'The website {website} is accessible over the internet.'
        payload = {'text': message}

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.webhook_url, json=payload, timeout=self.timeout) as response:
                    if response.status == 200:
                        self.logger.info(f'Successfully sent alert to Rocket.Chat for {website}.')
                    else:
                        self.logger.error(
                            f'Failed to send alert to Rocket.Chat for {website}. Status code: {response.status}')
            except aiohttp.ClientError as e:
                self.logger.error(f'Error occurred while sending alert to Rocket.Chat for {website}: {str(e)}')

    def load_websites_from_file(self):
        """
        Load the list of websites to monitor from the config file.

        Returns:
            dict: Dictionary of websites with their URLs as keys and their configurations as values.

        """
        try:
            with open(self.config_file, 'r') as file:
                config = yaml.safe_load(file)
                do_not_monitor = config.get('do_not_monitor', [])
                monitor = config.get('monitor', [])

                websites = {}

                for website in do_not_monitor:
                    websites[website['url']] = {'allowed': True}

                for website in monitor:
                    websites[website['url']] = {
                        'allowed': False,
                        'accessibility_texts': website.get('accessibility_texts', self.global_accessibility_texts)
                    }

                return websites
        except FileNotFoundError:
            self.logger.error(f'File "{self.config_file}" not found.')
        except Exception as e:
            self.logger.error(
                f'Error occurred while loading the websites from file "{self.config_file}": {str(e)}')
        return {}

    def is_website_allowed(self, website):
        """
        Check if a website is allowed based on its configuration.

        Args:
            website (dict): The website dictionary containing URL and allowed flag.

        Returns:
            bool: True if the website is allowed, False otherwise.

        """
        return website.get('allowed', True)

    async def check_website_accessibility(self, sem, session, website):
        """
        Check the accessibility of a website asynchronously.

        Args:
            sem (asyncio.Semaphore): Semaphore for limiting concurrent requests.
            session (aiohttp.ClientSession): HTTP session.
            website (str): The website URL to check.

        Returns:
            bool: True if the website is accessible, False otherwise.

        """
        async with sem:  # Acquire the semaphore to limit concurrent requests
            try:
                async with session.get(website, timeout=self.timeout) as response:
                    response_text = await response.text()
                    website_data = self.websites[website]
                    texts_to_check = website_data.get('accessibility_texts', self.global_accessibility_texts)
                    if not any(text in response_text for text in texts_to_check):
                        self.logger.warning(f'{website}: ALERT! Website is not accessible over the internet.')
                        self.logger.info(f'{website}: Server returned status code {response.status}.')
                        await self.send_alert_to_rocketchat(website)
                        return True
                    else:
                        self.logger.info(f'{website}: accessible over the internet.')
                        self.logger.info(f'{website}: Server returned status code {response.status}.')
                        return False
            except asyncio.TimeoutError:
                self.logger.error(f'{website}: Request to {website} timed out.')
            except aiohttp.ClientError as e:
                self.logger.error(f'{website}: Error occurred during the request: {str(e)}')

    async def monitor_websites(self, iteration):
        """
        Monitor the websites for accessibility and send alerts if necessary.

        Args:
            iteration (int): The current iteration number.

        """
        sem = asyncio.Semaphore(self.concurrent_requests)

        async with aiohttp.ClientSession() as session:
            tasks = []
            for website_url, website_data in self.websites.items():
                if not self.is_website_allowed(website_data):
                    task = asyncio.ensure_future(self.check_website_accessibility(sem, session, website_url))
                    tasks.append(task)

            if tasks:
                await asyncio.gather(*tasks)
        
        if self.num_runs != -1 and iteration < self.num_runs - 1:
            print(f'Iteration {iteration + 1}/{self.num_runs} completed. Delaying for {self.iteration_delay} seconds.')
        elif self.num_runs == -1 or iteration < self.num_runs - 1:
            print(f'Iteration {iteration + 1} completed. Delaying for {self.iteration_delay} seconds.')

    async def run_monitoring(self):
        for iteration in range(self.num_runs) if self.num_runs != -1 else itertools.count():
            await self.monitor_websites(iteration)
            if self.iteration_delay > 0:
                await asyncio.sleep(self.iteration_delay)
                if self.num_runs != -1 and iteration < self.num_runs - 1:
                    print(f'Delay of {self.iteration_delay} seconds completed. Starting the next iteration.')
                elif self.num_runs != -1 and iteration == self.num_runs - 1:
                    print('Last iteration completed.')

    def run(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.run_monitoring())
        if self.check_file_size:
            log_file = 'app.log'
            if os.path.isfile(log_file) and os.path.getsize(log_file) > self.max_file_size:
                os.remove(log_file)

if __name__ == '__main__':
    config_file = 'config.yaml'

    monitor = WebsiteMonitor(config_file)
    monitor.run()
