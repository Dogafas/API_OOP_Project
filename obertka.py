
from pprint import pprint
import requests
import os
from datetime import datetime

""" functools import cached_property - позволяет мне закешировать результат вычисления свойства объекта.
Очень полезно, когда свойство требует сложных вычислений или обращений к ресурсам,
 но результат не меняется при повторных вызовах.
 """
from functools import cached_property 

class VK:
    def __init__(self, access_token, user_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    @cached_property 
    def albums_get(self, need_system=1):
        """
        Получает список альбомов пользователя.
        :param need_system: Флаг, указывающий на необходимость включения системных альбомов (по умолчанию 1)
        :return: Список альбомов
        """
        url = 'https://api.vk.com/method/photos.getAlbums'
        params = {
            'owner_id': self.id,
            'need_system': need_system,
        }
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    def photos_get(self, album_id='profile', count=5, extended=1):
        """
        Получает фотографии пользователя из указанного альбома.
        :param album_id: ID альбома (по умолчанию 'profile' для фотографий профиля)
        :param count: Количество фотографий для загрузки (по умолчанию 5)
        :param extended: Включить информацию о лайках и комментариях (по умолчанию 1)
        :return: Список фотографий
        """
        url = 'https://api.vk.com/method/photos.get'
        params = {
            'owner_id': self.id,
            'album_id': album_id,
            'count': count,
            'extended': extended,
        }
        response = requests.get(url, params={**self.params, **params})
        return response.json()

    def data_out(self, data):
        """
        Извлекаем данные. URL для фото типа "w" (наибольший размер фото пользователя)
        и количеством лайков - likes, если количество лайков у всех фото одинаковое или их нет,
        то присваиваем дату загрузки в название сохраняемого фото"
        (баг: "Если фотографии были загружены в альбом VK - одновременно и без метаданных,
        то ЯндексДиск даст загрузить меньше, чем 5 фотографий заданных по умолчанию.") 
        """
        output_data = []

        # Получаем все количества лайков
        likes_counts = [item['likes']['count'] for item in data['response']['items']]
        
        # Проверяем, все ли количества лайков одинаковые
        all_likes_same = all(count == likes_counts[0] for count in likes_counts)
        for item in data['response']['items']:
            likes_count = item['likes']['count']
            # Форматируем дату загрузки в понятный формат
            upload_date = datetime.fromtimestamp(item['date']).strftime('%Y-%m-%d_%H-%M-%S')
            likes = upload_date if likes_count == 0 or all_likes_same else str(likes_count)

            for size in item['sizes']:
                if size['type'] == 'w':
                    url_w = size['url']
                    size_type = size['type']
                    output_data.append({"likes": likes,
                        "url": url_w,
                        "upload_date": upload_date,
                        "size_type": size_type})

        return output_data


# Пример использования (мой открытый ВК user_id = '878687318')
def main():
    user_id = input("Введите id пользователя из VK: ")
    VKservice_key = os.getenv('KEY_VK')
    
    if not VKservice_key:
        print("Сервисный ключ не найден.")
    else:
        vk = VK(VKservice_key, user_id)
        # Вызываем метод albums_get для получения списка альбомов
        albums = vk.albums_get
        # Обработка ошибок
        if 'error' in albums:
            print(f"Ошибка при получении списка альбомов: {albums['error']['error_msg']}")
        else:
            # Создаем список для хранения данных о фотографиях из всех альбомов
            all_photos_data = []
            # Проходим по каждому альбому и получаем фотографии
            for album in albums['response']['items']:
                album_id = album['id']
                album_title = album['title']
                # Вызываем метод photos_get для получения фотографий из текущего альбома
                photos = vk.photos_get(album_id=album_id, count=5)
                # Обработка ошибок
                if 'error' in photos:
                    print(f"Ошибка при получении фотографий из альбома {album_title}: {photos['error']['error_msg']}")
                else:
                    # Извлекаем данные с помощью data_out
                    output_data = vk.data_out(photos)
                    # Добавляем данные в общий список
                    all_photos_data.append({
                        "album_id": album_id,
                        "album_title": album_title,
                        "photos": output_data
                    })

            # Выводим все данные на экран
            # pprint(all_photos_data)

if __name__ == "__main__":
    main()
