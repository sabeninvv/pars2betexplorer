from time import  monotonic
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.chrome.options import Options
from utils import load_ua


class browser_control(object):
    def __init__(self, binary_location):
        self.time_without_clean_cache = int(monotonic())
        self.binary_location = binary_location

    def make_options(self, headless=True, proxing=False):
        '''Конфигурирование браузера'''
        dict_options = {}
        options = Options()
        if headless:
            options.add_argument("--headless")
        if self.binary_location:
            options.binary_location = (self.binary_location)
        options.page_load_strategy = 'eager'
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('user-agent={}'.format(load_ua()))
        dict_options['options'] = options

        if proxing:
            prox = Proxy()
            prox.proxy_type = ProxyType.MANUAL
            prox.http_proxy = 'socks5://127.0.0.1:9050'
            prox.ssl_proxy = 'socks5://127.0.0.1:9050'
            capabilities = webdriver.DesiredCapabilities.CHROME
            prox.add_to_capabilities(capabilities)
            dict_options['desired_capabilities'] = capabilities
        return dict_options

    def close_old_windows(self, windows, browser):
        '''Закрыть не нужные окна.'''
        if len(browser.window_handles) > len(windows):
            old_key_windows = browser.window_handles.copy()
            browser.switch_to.window(old_key_windows[-1])
            for window_key in old_key_windows:
                if window_key not in windows.values():
                    browser.switch_to.window(window_key)
                    browser.close()

    def clear_cache(self, browser):
        '''Чистить кэш браузера каждые 50 мин.'''
        if monotonic() - self.time_without_clean_cache > 3100:
            send_command = ('POST', '/session/$sessionId/chromium/send_command')
            browser.command_executor._commands['SEND_COMMAND'] = send_command
            _ = browser.execute('SEND_COMMAND', dict(cmd='Network.clearBrowserCache', params={}))
            self.time_without_clean_cache = int(monotonic())
