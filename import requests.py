from pprint import pprint
import requests
import keyring


class VK:
    def __init__(self, access_token, user_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def users_info(self):
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': self.id}
        response = requests.get(url, params={**self.params, **params})
        return response.json()

# Пример использования
user_id = '878687318'  # замените на реальный идентификатор пользователя
service_name = "VK2Yandex"

access_token = keyring.get_password(service_name, user_id)


vk = VK(access_token, user_id)
pprint(vk.users_info())



