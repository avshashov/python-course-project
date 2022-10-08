import os
import requests
import time
from datetime import datetime
from pprint import pprint
from tqdm import tqdm
import my_token


class VkPhoto:
    token = my_token.vk_token
    url = 'https://api.vk.com/method/photos.get'
    vk_params = {'v': 5.131, 'access_token': token}

    def __init__(self, user_id=None, count=5):
        self.id = self._check_user_id(user_id)
        self.count = count
        self.photo_params = {
            'owner_id': self.id, 'album_id': 'profile',
            'count': self.count,
            'extended': 1
        }

        self.response = requests.get(VkPhoto.url, params={**self.photo_params, **VkPhoto.vk_params})

    def _check_user_id(self, user_id):
        if not isinstance(user_id, int):
            user_url = 'https://api.vk.com/method/users.get'
            user_id = requests.get(user_url, params={'user_ids': user_id, **VkPhoto.vk_params}).json()['response'][0][
                'id']
        return user_id

    def download_photo(self):
        files, check_file_name = [], []
        for photo in tqdm(self.response.json()['response']['items'], colour='#FFFFFF', desc='processing'):
            date = datetime.strftime(datetime.fromtimestamp(photo['date']), '%d-%m-%Y %H-%M-%S')

            file_name = f"{photo['likes']['count']}.jpg"
            if file_name in check_file_name:
                file_name = file_name.replace('.jpg', f'_{date}.jpg')
            check_file_name.append(file_name)
            photo_description = {
                'file_name': file_name,
                'size': photo['sizes'][-1]['type'],
            }

            files.append(photo_description)

            path = os.path.join(os.getcwd(), 'photo to upload')
            if not os.path.exists(path):
                os.mkdir(path)

            with open(os.path.join(path, file_name), 'wb') as f:
                image = requests.get(url=photo['sizes'][-1]['url'], params={**VkPhoto.vk_params,
                                                                            **self.photo_params}).content
                f.write(image)

            time.sleep(0.2)
        return files


class YaUploader:

    def __init__(self, token):
        self.token = token
        self.headers = {"content-type": "application/json",
                        "Authorization": f'OAuth {token}'}

    def create_folder(self, folder_name):
        params = {'path': folder_name}
        requests.put('https://cloud-api.yandex.net/v1/disk/resources', headers=self.headers, params=params)
        return folder_name

    def _get_upload_link(self, disk_space_path):
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        params = {'path': disk_space_path, 'overwrite': 'true'}
        response = requests.get(upload_url, headers=self.headers, params=params)
        return response.json()

    def upload(self, disk_file_path, files):
        for file in tqdm(files, colour='#FFFFFF', desc='upload to yandex'):
            href = self._get_upload_link(disk_space_path=f"{disk_file_path}/{file['file_name']}").get('href', '')
            requests.put(href, data=open(os.path.join(os.getcwd(), 'photo to upload', file['file_name']), 'rb'))
            time.sleep(0.2)


if __name__ == '__main__':

    vk = VkPhoto()
    yandex = YaUploader(my_token.ya_token)

    try:
        files = vk.download_photo()
        folder_name = yandex.create_folder('vk_photo')
        yandex.upload(folder_name, files)
        pprint(files)

    except KeyError:
        print(f"Error. {vk.response.json()['error']['error_msg']}")
