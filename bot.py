import os
from time import sleep
from bs4 import BeautifulSoup
from utils import file_operation, get_config
from selenium import webdriver


class bot(object):
    def __init__(self, network_control, browser_control, telegram_worker):
        (PASS_FOR_TOR, PORT_FOR_TOR, BOT_TOKEN, BIN_LOCATION) = get_config()
        self.network_control = network_control(PASS_FOR_TOR, PORT_FOR_TOR)
        self.browser_control = browser_control(BIN_LOCATION)
        self.telegram_worker = telegram_worker(BOT_TOKEN, session=self.network_control.session)
        self.labels_to_search, self.urls = self.get_data_from_simplenote()

    def get_html_and_soup(self, url):
        try:
            html = self.network_control.session.get(url, timeout=2)
            soup = BeautifulSoup(html.content, 'lxml')
            block_with_content = soup.find('div', {'class': 'note note-detail-markdown'})
            return block_with_content
        except:
            return []

    def dump_file(self, path, data):
        data = list(set(data))
        if data:
            file_operation(path=path, mode='w', yaml_file=True, data=data)
        else:
            data = file_operation(path=path, mode='r', yaml_file=True)
        return data

    def get_urls_from_simplenote(self):
        urls = []
        block_with_urls = self.get_html_and_soup(url='http://simp.ly/p/lSQ9WH')
        for i in block_with_urls:
            try:
                href = i.get('href')
                urls.append(href) if href else None
            except:
                continue
        urls = self.dump_file(path='order/urls.yaml', data=urls)
        return urls

    def get_labels_from_simplenote(self):
        labels = []
        block_with_labels = self.get_html_and_soup(url='http://simp.ly/p/Cn0vSP')
        for i in block_with_labels:
            href = i.nextSibling
            try:
                href = href.replace('\n', '')
                href = href.replace('  ', '')
                labels.append(href)
            except:
                continue
        labels = self.dump_file(path='order/labels.yaml', data=labels)
        return labels

    def get_data_from_simplenote(self):
        return self.get_labels_from_simplenote(), self.get_urls_from_simplenote()

    def get_labels_from_betexplorer(self, html):
        labels = []
        soup = BeautifulSoup(html, 'lxml')
        try:
            table = soup.find('table', {'class': 'table-main h-mb15 sortable'})
            tds = table.findAll('td', {'class': 'h-text-left over-s-only'})
            for td in tds:
                labels.append(td.text)
        except:
            pass
        return labels

    def get_title_from_betexplorer(self, html):
        soup = BeautifulSoup(html, 'lxml')
        try:
            block_title = soup.find('ul', {'class': 'list-breadcrumb'})
            titles = block_title.findAll('li', {'class': 'list-breadcrumb__item'})
            temp = []
            for title in titles:
                temp.append(title.text)
            title = temp.copy()[2:]
            title = ' => '.join(title)
        except:
            title = ''
        return title

    def get_data_from_betexplorer(self, html):
        labels = self.get_labels_from_betexplorer(html=html)
        title = self.get_title_from_betexplorer(html=html)
        return labels, title

    def get_news_and_labels(self, list_values, news_to_telegram, url=None, track_on_disk=None, merge=False):
        if merge:
            renew_val = []
            for label in list_values[0]:
                renew_val.append(label)
                if label not in track_on_disk[url]:
                    news_to_telegram += '{}: {}\n'.format(str(list_values[1]), str(label))
            renew_val.extend(track_on_disk[url])
            renew_val = list(set(renew_val))
            values = [renew_val, list_values[1]]
            return values, news_to_telegram
        else:
            labels = [str(i) for i in list_values[0]]
            labels = ', '.join(labels)
            news_to_telegram += '{}: {}\n'.format(str(list_values[1]), labels)
            values = list_values[0], list_values[1]
            return values, news_to_telegram

    def resave_track(self, input_track):
        if os.path.isfile('track/track.yaml'):
            track_on_disk = file_operation(path='track/track.yaml', mode='r', yaml_file=True)
        else:
            track_on_disk = None
        renew_track = {}
        news_to_telegram = ''
        for url, list_values in input_track.items():
            if track_on_disk:
                if list_values[0]:
                    if url in track_on_disk.keys():
                        renew_track[url], news_to_telegram = self.get_news_and_labels(list_values=list_values, url=url,
                                                                                      track_on_disk=track_on_disk,
                                                                                      merge=True,
                                                                                      news_to_telegram=news_to_telegram)
                    else:
                        renew_track[url], news_to_telegram = self.get_news_and_labels(list_values=list_values,
                                                                                      news_to_telegram=news_to_telegram)
                else:
                    if url in track_on_disk.keys():
                        renew_track[url] = [track_on_disk[url], list_values[1]]
                    else:
                        renew_track[url] = [[], list_values[1]]
            else:
                renew_track[url], news_to_telegram = self.get_news_and_labels(list_values=list_values,
                                                                              news_to_telegram=news_to_telegram)

        track2yaml = { key: val[0] for key, val in renew_track.items() }
        file_operation(path='track/track.yaml', mode='w', yaml_file=True, data=track2yaml)
        if news_to_telegram:
            print('NEWS TO TELEGA', news_to_telegram)
            # self.telegram_worker.telegram_message(message=news_to_telegram)               # <==================
        return renew_track

    def get_new_windowkey(self, browser, windows):
        '''Создание новой вкладки и поиск ключа.'''
        old_key_windows = browser.window_handles.copy()
        browser.switch_to.window(old_key_windows[-1])
        browser.execute_script("window.open('')")
        for new_windowkey in browser.window_handles:
            if new_windowkey not in old_key_windows:
                return new_windowkey

    def tracking(self, browser, windows, track, url, refresh):
        self.network_control.check_connection()
        if not refresh and windows:
            browser.execute_script("window.open('')")
        if not refresh:
            windows[url] = browser.window_handles[-1]
        if refresh and url not in windows.keys():
            windows[url] = self.get_new_windowkey(browser=browser, windows=windows)
            refresh = False
        browser.switch_to.window(windows[url])
        try:
            browser.refresh() if refresh else browser.get(url)
            sleep(4)
            all_lbls, title = self.get_data_from_betexplorer(html=browser.page_source)
        except:
            all_lbls = []
            title = ''
        track_lbls = [label for label in self.labels_to_search if label in all_lbls] if all_lbls else []
        track[url] = [track_lbls, title]
        return windows, track

    def del_old_urls(self, windows, track):
        '''Удалить старые ссылки и ключи окон.'''
        old_urls = windows.copy()
        for old_url in old_urls.keys():
            if old_url not in self.urls:
                _ = windows.pop(old_url)
                _ = track.pop(old_url)
        return windows, track

    def run(self):
        with webdriver.Chrome(executable_path='driver/chromedriver.exe',
                              **self.browser_control.make_options(headless=False, proxing=True),
                              service_args=['--verbose', '--log-path=logs/gh.log']) as browser:
            windows = {}
            track = {}
            refresh = False
            while True:
                for url in self.urls:
                    windows, track = self.tracking(browser=browser, windows=windows, track=track,
                                                   url=url, refresh=refresh)
                track = self.resave_track(input_track=track)
                windows, track = self.del_old_urls(windows=windows, track=track)
                self.browser_control.close_old_windows(windows=windows, browser=browser)
                self.browser_control.clear_cache(browser=browser)
                sleep(5)
                self.labels_to_search, self.urls = self.get_data_from_simplenote()
                refresh = True
