import requests
from time import sleep
from stem import Signal
from stem.control import Controller
from utils import load_ua


class network_control(object):
    def __init__(self, PASS_FOR_TOR, PORT_FOR_TOR):
        self.PASS_FOR_TOR = PASS_FOR_TOR
        self.PORT_FOR_TOR = PORT_FOR_TOR
        self.session = self.get_session()

    def get_session(self):
        session = requests.session()
        session.proxies = {'http': 'socks5://127.0.0.1:9050',
                           'https': 'socks5://127.0.0.1:9050'
                           }
        session.headers = {'User-Agent': load_ua()}
        return session

    def update_tor_ip(self):
        with Controller.from_port(port=self.PORT_FOR_TOR) as controller:
            controller.authenticate(self.PASS_FOR_TOR)
            controller.signal(Signal.NEWNYM)
            sleep(8)
        self.session = self.get_session()

    def check_connection(self):
        step = 0
        while True:
            self.update_tor_ip() if step == 5 else None
            try:
                _ = self.session.get('https://www.ya.ru', verify=True, timeout=1)
                break
            except:
                try:
                    _ = self.session.get('https://api.ipify.org?format=json', timeout=1.2)
                except (requests.ConnectionError,
                        requests.RequestException,
                        requests.HTTPError,
                        requests.Timeout,
                        requests.TooManyRedirects) as e:
                    step += 1
                    continue
