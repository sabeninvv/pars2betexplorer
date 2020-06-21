#!/usr/local/bin/env python3
# -*- coding: utf-8 -*-

import requests
import yaml
from time import sleep, time
from random import randint
import os
from stem import Signal
from stem.control import Controller
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.chrome.options import Options


class parse_bot(object):
    def __init__(self, url_bot_telegram):
        self.url_bot_telegram = url_bot_telegram
        self.session = self.get_session()

    def get_user_agent(self):
        ua = self.file_operation(path='track/ua.yaml', mode='r', yaml_file=True, data=None)
        inx = randint(0, len(ua)-1)
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
                print('Начните общение с ботом. Пропишите в чате с ботом любой символ.')
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
                    for label in val[1]:
                        renew_val.append(label)
                        if label not in track_on_disk[key][1]:
                            news_to_telegram += '{}: {}\n'.format(str(val[-1]), str(label))
                renew_track[key] = [track[key][0], renew_val]
            else:
                for label in val[1]:
                    news_to_telegram += '{}: {}\n'.format(str(val[-1]), str(label))
                renew_track[key] = val

        self.file_operation(path='track/track.yaml', mode='w', yaml_file=True, data=renew_track)
        if news_to_telegram:
            self.telegram_message(message=news_to_telegram)
        return renew_track

    def tracking(self, browser, windows, track, url, refresh, labels_to_search):
        turn = 0
        while True:
            if self.check_connection():
                track_lbls = []
                if windows and not refresh:
                    browser.execute_script("window.open('')")
                if not refresh:
                    windows[url] = browser.window_handles[-1]
                browser.switch_to.window(windows[url])
                try:
                    if refresh:
                        browser.refresh()
                    else:
                        browser.get(url)
                    sleep(4)
                    all_lbls, title = self.get_bk_label(html=browser.page_source)
                except:
                    all_lbls = []
                    title = ''
                if all_lbls:
                    track_lbls = [i for i in labels_to_search if i in all_lbls]
                track[url] = [int(time()), track_lbls, title]
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
                sleep(5)


def make_options(headless=True, proxing=False):
    dict_options = {}
    options = Options()
    if headless:
        options.add_argument("--headless")  # Runs Chrome in headless mode.
    options.page_load_strategy = 'eager'
    options.add_argument('--no-sandbox')  # Bypass OS security model
    options.add_argument('--disable-gpu')  # applicable to windows os only
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
    url_bot_telegram = ''
    bot = parse_bot(url_bot_telegram=url_bot_telegram)
    with webdriver.Chrome(executable_path='driver/chromedriver.exe', **make_options(headless=True, proxing=True)) as browser:
        urls = bot.file_operation(path='order/urls.txt', mode='r', yaml_file=False)
        labels_to_search = bot.file_operation(path='order/labels.txt', mode='r', yaml_file=False)

        windows = {}
        track = {}
        refresh = False
        while True:
            for url in urls:
                if refresh:
                    _, track = bot.tracking(browser=browser, windows=windows, track=track, url=url, refresh=refresh,
                                            labels_to_search=labels_to_search)
                else:
                    windows, track = bot.tracking(browser=browser, windows=windows, track=track, url=url,
                                                  refresh=refresh,
                                                  labels_to_search=labels_to_search)
            refresh = True
            if track:
                track = bot.resave_track(track=track)
            sleep(30)

if __name__ == '__main__':
    main()
