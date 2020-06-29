import requests
import yaml
from time import sleep, monotonic
from random import randint
import os
from stem import Signal
from stem.control import Controller
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.chrome.options import Options


BOT_TOKEN = ''


class parse_bot(object):
    def __init__(self, url_bot_telegram):
        self.url_bot_telegram = url_bot_telegram
        self.session = self.get_session()
        self.labels_to_search, self.urls = self.get_data_from_simplenote()
        self.time_without_clean_cache = int(monotonic())

    def get_user_agent(self):
        ua = self.file_operation(path='track/ua.yaml', mode='r', yaml_file=True, data=None)
        inx = randint(0, len(ua) - 1)
        ua = ua[inx]
        return str(ua)

    def get_session(self):
        session = requests.session()
        session.proxies = {'http': 'socks5://127.0.0.1:9050',
                           'https': 'socks5://127.0.0.1:9050'
                           }
        session.headers = {'User-Agent': self.get_user_agent()}
        return session

    def update_tor_ip(self):
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)
            sleep(8)
        self.session = self.get_session()

    def check_connection(self):
        try:
            _ = requests.get('https://www.ya.ru', verify=True, timeout=1)
            return True
        except:
            try:
                _ = requests.get('https://api.ipify.org?format=json', timeout=1.2)
            except (requests.ConnectionError,
                    requests.RequestException,
                    requests.HTTPError,
                    requests.Timeout,
                    requests.TooManyRedirects) as e:
                return False

    def get_update(self):
        method = 'getUpdates'
        url = self.url_bot_telegram + method
        data = self.session.get(url)
        return data.json()

    def get_chats_id(self, data):
        dump = False
        if os.path.isfile('track/user_id.yaml'):
            chat_ids = self.file_operation(path='track/user_id.yaml', mode='r', yaml_file=True, data=None)
        else:
            chat_ids = []
            dump = True
        try:
            for member in data['result']:
                chat_id = member['message']['chat']['id']
                if chat_id not in chat_ids:
                    chat_ids.append(chat_id)
                    dump = True
        except:
            if dump == True:
                print('Начните общение с ботом. Отправьте в чат с ботом любой символ.')
            chat_ids = ['837181918']
            return chat_ids
        if dump:
            self.file_operation(path='track/user_id.yaml', mode='w', yaml_file=True, data=chat_ids)
        return chat_ids

    def send_message(self, chat_id, message):
        message = message.replace('&', 'and')
        method = 'sendMessage?chat_id={}&text={}'.format(str(chat_id), message)
        url = self.url_bot_telegram + method
        _ = self.session.get(url)

    def telegram_message(self, message):
        while True:
            try:
                data = self.get_update()
                chat_ids = self.get_chats_id(data)
                for chat_id in chat_ids:
                    self.send_message(chat_id, message)
                break
            except:
                print('Получение нового ip')
                self.update_tor_ip()

    def file_operation(self, path, mode, yaml_file=False, data=None):
        with open(path, mode=mode) as file:
            if mode == 'r' and not yaml_file:
                data = file.read()
                return data.split('\n')
            elif mode == 'r' and yaml_file:
                data = yaml.safe_load(file)
                return data
            elif mode == 'w' and yaml_file:
                yaml.dump(data, file, default_flow_style=False)

    def get_data_from_simplenote(self):
        turn = 0
        data = []
        url_labels = 'http://simp.ly/p/Cn0vSP'
        url_urls = 'http://simp.ly/p/lSQ9WH'
        while True:
            if self.check_connection():
                while True:
                    temp_turn = 0
                    if temp_turn > 5:
                        self.update_tor_ip()
                    try:
                        req = self.session.get(url_labels, timeout=1)
                        req = BeautifulSoup(req.content, 'lxml')
                        req = req.find('div', {'class': 'note note-detail-markdown'})
                        temp = []
                        for i in req:
                            href = i.nextSibling
                            try:
                                href = href.replace('\n', '')
                                href = href.replace('  ', '')
                                temp.append(href)
                            except:
                                continue
                        temp = list(set(temp))
                        data.append(temp)
                        break
                    except:
                        temp_turn += 1
                        sleep(2)
                while True:
                    temp_turn = 0
                    if temp_turn > 5:
                        self.update_tor_ip()
                    try:
                        req = self.session.get(url_urls, timeout=1)
                        req = BeautifulSoup(req.content, 'lxml')
                        temp = []
                        req = req.find('div', {'class': 'note note-detail-markdown'})
                        for i in req:
                            try:
                                href = i.get('href')
                                temp.append(href) if href else None
                            except:
                                continue
                        temp = list(set(temp))
                        data.append(temp)
                        break
                    except:
                        temp_turn += 1
                        sleep(2)
                return data
            else:
                if turn > 5:
                    self.update_tor_ip()
                    print('Получение нового ip')
                print('Проверьте интернет соединение')
                turn += 1
                sleep(2)

    def get_bk_label(self, html):
        soup = BeautifulSoup(html, 'lxml')
        labels = []
        title = []
        try:
            table = soup.find('table', {'class': 'table-main h-mb15 sortable'})
            tds = table.findAll('td', {'class': 'h-text-left over-s-only'})
            for td in tds:
                labels.append(td.text)
        except:
            pass
        try:
            block_title = soup.find('ul', {'class': 'list-breadcrumb'})
            titles = block_title.findAll('li', {'class': 'list-breadcrumb__item'})
            temp = []
            for title in titles:
                temp.append(title.text)
            title = temp.copy()[2:]
            title = ' => '.join(title)
        except:
            pass
        return labels, title

    def resave_track(self, track):
        if os.path.isfile('track/track.yaml'):
            track_on_disk = self.file_operation(path='track/track.yaml', mode='r', yaml_file=True)
        else:
            track_on_disk = None
        renew_track = {}
        news_to_telegram = ''
        for key, val in track.items():
            if track_on_disk:
                renew_val = []
                if key in track_on_disk.keys():
                    for label in val[0]:
                        renew_val.append(label)
                        if label not in track_on_disk[key]:
                            news_to_telegram += '{}: {}\n'.format(str(val[1]), str(label))
                    renew_track[key] = renew_val
                else:
                    labels = [str(i) for i in val[0]]
                    labels = ', '.join(labels)
                    news_to_telegram += '{}: {}\n'.format(str(val[1]), labels)
                    renew_track[key] = val[0]

            else:
                labels = [str(i) for i in val[0]]
                labels = ', '.join(labels)
                news_to_telegram += '{}: {}\n'.format(str(val[1]), labels)
                renew_track[key] = val[0]

        self.file_operation(path='track/track.yaml', mode='w', yaml_file=True, data=renew_track)
        if news_to_telegram:
            self.telegram_message(message=news_to_telegram)
        return renew_track

    def tracking(self, browser, windows, track, url, refresh):
        turn = 0
        while True:
            if self.check_connection():
                track_lbls = []
                if not refresh and windows:
                    browser.execute_script("window.open('')")
                if not refresh:
                    windows[url] = browser.window_handles[-1]
                if refresh and url not in windows.keys():
                    browser.execute_script("window.open('')")
                    for new_window in browser.window_handles:
                        if new_window not in windows.values():
                            windows[url] = new_window
                    refresh = False
                browser.switch_to.window(windows[url])
                try:
                    browser.refresh() if refresh else browser.get(url)
                    sleep(4)
                    all_lbls, title = self.get_bk_label(html=browser.page_source)
                except:
                    all_lbls = []
                    title = ''
                if all_lbls:
                    track_lbls = [i for i in self.labels_to_search if i in all_lbls]
                track[url] = [track_lbls, title]
                return windows, track
            else:
                if turn > 5:
                    try:
                        self.update_tor_ip()
                        print('Получение нового ip')
                    except:
                        continue
                print('Проверьте интернет соединение')
                turn += 1
                sleep(2)

    def del_old_urls(self, windows, track):
        old_urls = windows.copy()
        for old_url in old_urls.keys():
            if old_url not in self.urls:
                _ = track.pop(old_url)
                _ = windows.pop(old_url)
        return windows, track

    def close_old_windows(self, windows, browser, track):
        empty_windows_key = ''
        if not track:
            browser.execute_script("window.open('')")
            for window_key in browser.window_handles:
                if window_key not in windows.values():
                    empty_windows_key = window_key

        for window_key in browser.window_handles:
            if window_key not in windows.values() and window_key != empty_windows_key:
                browser.switch_to.window(window_key)
                browser.close()

    def clear_cache(self, browser):
        send_command = ('POST', '/session/$sessionId/chromium/send_command')
        browser.command_executor._commands['SEND_COMMAND'] = send_command
        _ = browser.execute('SEND_COMMAND', dict(cmd='Network.clearBrowserCache', params={}))


def load_ua():
    with open('track/ua.yaml', 'r') as file:
        ua = yaml.safe_load(file)
        inx = randint(0, len(ua) - 1)
        ua = ua[inx]
    return ua


def make_options(path2google_chrome='/usr/bin/google-chrome', headless=True, proxing=False):
    dict_options = {}
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.page_load_strategy = 'eager'
    options.binary_location = (path2google_chrome)
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--no-sandbox')
    options.add_argument(f'user-agent={load_ua()}')
    dict_options['options'] = options

    if proxing:
        prox = Proxy()
        prox.proxy_type = ProxyType.MANUAL
        prox.http_proxy = 'socks5://127.0.0.1:9050'
        prox.ssl_proxy = 'socks5://127.0.0.1:9050'
        capabilities = webdriver.DesiredCapabilities.CHROME
        prox.add_to_capabilities(capabilities)
    else:
        capabilities = webdriver.DesiredCapabilities.CHROME
    dict_options['desired_capabilities'] = capabilities
    return dict_options


def main():
    bot = parse_bot(url_bot_telegram=BOT_TOKEN)
    with webdriver.Chrome(**make_options(headless=True, proxing=True)) as browser:
        windows = {}
        track = {}
        while True:
            refresh = True if track else False
            for url in bot.urls:
                windows, track = bot.tracking(browser=browser, windows=windows, track=track, url=url, refresh=refresh)
            if track:
                track = bot.resave_track(track=track)
            bot.labels_to_search, bot.urls = bot.get_data_from_simplenote()
            windows, track = bot.del_old_urls(windows=windows, track=track)
            bot.close_old_windows(windows=windows, browser=browser, track=track)
            if monotonic() - bot.time_without_clean_cache > 3100:
                bot.clear_cache(browser=browser)
                bot.time_without_clean_cache = int(monotonic())
            sleep(5)


if __name__ == '__main__':
    main()
