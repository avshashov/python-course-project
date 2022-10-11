import json
import requests
import time
from datetime import datetime
from tqdm import tqdm
import my_token


class VkPhoto:
    url = 'https://api.vk.com/method/photos.get'

    def __init__(self, user_id=None, count=5, token=my_token.vk_token):
        self.token = token
        self.vk_params = {'v': 5.131, 'access_token': token}
        self.id = self._screen_name_to_id(user_id)
        self.count = count

        self.photo_params = {
            'owner_id': self.id, 'album_id': 'profile',
            'count': self.count,
            'extended': 1
        }

        self.response = requests.get(VkPhoto.url, params={**self.photo_params, **self.vk_params})

    def _screen_name_to_id(self, user_id):
        if not isinstance(user_id, int):
            user_url = 'https://api.vk.com/method/users.get'
            user_id = requests.get(user_url, params={'user_ids': user_id, **self.vk_params}).json()['response'][0][
                'id']
        return user_id

    def _correct_file_name(self, file_name, date):
        if file_name in self.check_file_name:
            file_name = file_name.replace('.jpg', f'_{date}.jpg')
        self.check_file_name.append(file_name)
        return file_name

    def data_preparation(self):
        files, self.check_file_name = [], []
        files_to_upload = []
        for photo in tqdm(self.response.json()['response']['items'], colour='#FFFFFF', desc='processing'):
            date = datetime.strftime(datetime.fromtimestamp(photo['date']), '%d-%m-%Y %H-%M-%S')

            file_name = f"{photo['likes']['count']}.jpg"
            file_name = self._correct_file_name(file_name, date)
            photo_description = {
                'file_name': file_name,
                'size': photo['sizes'][-1]['type'],
            }

            files.append(photo_description)

            file_url = photo['sizes'][-1]['url']
            files_to_upload.append({'file_name': file_name, 'file_url': file_url})

            time.sleep(0.2)

        self._files_to_json(files)

        return files_to_upload

    def _files_to_json(self, files):
        with open('saved_photo.json', 'w', encoding='utf-8') as f:
            json.dump(files, f, indent=3)


class YaUploader:

    def __init__(self, token):
        self.token = token
        self.headers = {"content-type": "application/json",
                        "Authorization": f'OAuth {token}'}

    def create_folder(self, folder_name):
        params = {'path': folder_name}
        requests.put('https://cloud-api.yandex.net/v1/disk/resources', headers=self.headers, params=params)
        return folder_name

    def upload(self, disk_folder, files):
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        for file in tqdm(files, colour='#FFFFFF', desc='upload to yandex'):
            params = {'path': f"{disk_folder}/{file['file_name']}", 'url': file['file_url']}
            requests.post(upload_url, headers=self.headers, params=params)
            time.sleep(0.2)


if __name__ == '__main__':

    vk = VkPhoto()
    yandex = YaUploader(my_token.ya_token)

    try:
        files = vk.data_preparation()
        folder_name = yandex.create_folder('vk_photo')
        yandex.upload(folder_name, files)

    except KeyError:
        print(f"Error. {vk.response.json()['error']['error_msg']}")
