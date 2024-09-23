import requests
import json
import os
from tqdm import tqdm

class YandexDiskUploader:
    def __init__(self, token):
        self.token = token
        self.base_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.headers = {
            'Authorization': f'OAuth {self.token}',
            'Content-Type': 'application/json'
        }

    def create_folder(self, folder_path):
        url = f'{self.base_url}?path={folder_path}'
        response = requests.put(url, headers=self.headers)
        if response.status_code == 201:
            print(f"Папка {folder_path} успешно создана на Яндекс.Диске.")
        elif response.status_code == 409:
            print(f"Папка {folder_path} уже существует на Яндекс.Диске.")
        else:
            print(f"Ошибка при создании папки {folder_path}: {response.status_code} {response.text}")

    def check_folder_exists(self, folder_path):
        """Проверка существования папки"""
        url = f'{self.base_url}?path={folder_path}'
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return True  # Папка существует
        elif response.status_code == 404:
            return False  # Папка не существует
        else:
            print(f"Ошибка при проверке папки {folder_path}: {response.status_code} {response.text}")
            return False         

    def check_photo_url(self, url):
        try:
            response = requests.head(url)
            if response.status_code == 200:
                return True
            else:
                print(f"Ошибка при проверке URL фотографии: {response.status_code} {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при проверке URL фотографии: {e}")
            return False

    def upload_photo(self, file_name, url, folder):
        if not self.check_photo_url(url):
            print(f"Пропуск загрузки фото {file_name} из-за ошибки в URL.")
            return

        upload_url = f'{self.base_url}/upload'
        params = {
            'path': f'/{folder}/{file_name}',
            'url': url,
            'overwrite': 'true'
        }
        response = requests.post(upload_url, headers=self.headers, params=params)
        if response.status_code == 202:
            # print(f"Фото {file_name} успешно загружено на Яндекс.Диск.")
            pass
        else:
            print(f"Ошибка при загрузке фото {file_name}: {response.status_code} {response.text}")

    def upload_photos_from_vk(self, vk_instance, folder):
        # Получаем список альбомов из кешированного свойства vk_instance.albums_get
        albums = vk_instance.albums_get
        
        # Проверяем, существует ли основная папка PublicFolder, если нет — создаём
        if not self.check_folder_exists(folder):
            print(f"Папка {folder} не существует. Создаём её.")
            self.create_folder(folder)

        while True:
            # Запрос пользователю на ввод названия альбома
            album_title = input("Пишите, название альбома который хотите загрузить (ENTER для загрузки фото из профиля VK): ")
            
            # Если пользователь оставил поле пустым, используем альбом с "album_id": -6 (фото из профиля)
            if not album_title:
                for album in albums['response']['items']:
                    if album['id'] == -6:
                        album_title = album['title']
                        break
            
            # Пусть вводит название альбома любыми буквами, не зависимо от регистра
            selected_album = None
            for album in albums['response']['items']:
                if album['title'].lower() == album_title.lower():
                    selected_album = album
                    break
            
            if selected_album:
                break
            else:
                print(f"Альбом с названием '{album_title}' не найден. Пожалуйста, попробуйте еще раз.")
        
        # Создание папки на Яндекс.Диске
        album_folder = f"{folder}/{selected_album['title']}"
        self.create_folder(album_folder)

        log_list = []  # Лог для OUT_logs.json
    
        # Получаем фотографии для выбранного альбома
        photos = vk_instance.photos_get(album_id=selected_album['id'], count=5)
        output_data = vk_instance.data_out(photos)
        
        # Прогресс-бар для загрузки фотографий
        with tqdm(total=len(output_data), desc="Загрузка фото", bar_format="{l_bar}{bar:30}", unit="фото", colour="MAGENTA") as pbar:
            for photo in output_data:
                file_name = f"{photo['likes']}.jpg"
                size_type = photo.get('size_type', 'непонятный размер')
                self.upload_photo(file_name, photo['url'], album_folder)
                log_list.append({'file_name': file_name, 'size_type': size_type})
                pbar.update(1)  # Обновляем прогресс-бар

        with open('OUT_logs.json', 'w', encoding='utf-8') as log_file:
            json.dump(log_list, log_file, ensure_ascii=False, indent=4)
        print("Загрузка завершена. Лог записан в OUT_logs.json.")
        
 
# Пример использования
def main():
    # Получаем сервисный ключ доступа  VK
    user_id = input("Введите id пользователя из VK: ")
    VKservice_key = os.getenv('KEY_VK')

    if not VKservice_key:
        print("Сервисный ключ VK не найден.")
        return
    
    # Инициализация VK API
    from obertka import VK
    vk_instance = VK(VKservice_key, user_id)

    # Получение токена Яндекс.Диска
    YA_TOKEN = os.getenv('TOKEN_YA')  # Получение токена из переменных окружения 
    uploader = YandexDiskUploader(YA_TOKEN)
    # Загрузка фотографий напрямую из кешированных данных class VK
    uploader.upload_photos_from_vk(vk_instance, 'PublicFolder')


if __name__ == '__main__':
    main()
