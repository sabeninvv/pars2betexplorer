import os
from utils import file_operation


class telegram_worker(object):
    def __init__(self, BOT_TOKEN, session):
        self.BOT_TOKEN = 'https://api.telegram.org/bot' + BOT_TOKEN
        self.session = session

    def get_update(self):
        method = '/getUpdates'
        url = self.BOT_TOKEN + method
        data = self.session.get(url)
        return data.json()

    def get_chats_id(self, data):
        dump = False
        if os.path.isfile('track/user_id.yaml'):
            chat_ids = file_operation(path='track/user_id.yaml', mode='r', yaml_file=True, data=None)
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
            return ['837181918']
        file_operation(path='track/user_id.yaml', mode='w', yaml_file=True, data=chat_ids) if dump else None
        return chat_ids

    def send_message(self, chat_id, message):
        message = message.replace('&', 'and')
        method = '/sendMessage?chat_id={}&text={}'.format(str(chat_id), message)
        url = self.BOT_TOKEN + method
        _ = self.session.get(url)

    def telegram_message(self, message):
        try:
            data = self.get_update()
            chat_ids = self.get_chats_id(data)
            for chat_id in chat_ids:
                self.send_message(chat_id, message)
            return True
        except:
            return False
