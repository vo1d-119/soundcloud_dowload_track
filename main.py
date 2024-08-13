import requests
from bs4 import BeautifulSoup
import json
import re
import ffmpeg
import os

music_url = input("Ссылка на музыку soundcloud: ")

ffmpeg_path = 'ПУТЬ ДО ffmpeg.exe'
soup = BeautifulSoup(requests.get(music_url,headers={"user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/536.30.1 (KHTML, like Gecko) Version/6.0.5 Safari/536.30.1"}).content, 'html.parser')
json_pattern = re.compile(r'window\.__sc_hydration\s*=\s*(\[\{.*?\}\]);', re.DOTALL)
track_auth_pattern = re.compile(r'"track_authorization":\s*"([^"]+)"')

for script in soup.find_all('script'):
    script_text = script.string
    if script_text:
        match = json_pattern.search(script_text)
        if match:
            try:
                for item in json.loads(match.group(1)):
                    if 'data' in item and 'media' in item['data']:
                        for transcoding in item['data']['media'].get('transcodings', []):
                            if transcoding['format']['protocol'] == 'hls':
                                hls_url = transcoding['url']
                                break
                track_auth_match = track_auth_pattern.search(script_text)
                if track_auth_match:
                    track_authorization = track_auth_match.group(1)

                temp_files = []
                for i, url in enumerate([line for line in requests.get(requests.get(f"{hls_url}?client_id=H8sYVN4CJ2E8Ij83bJZ1OtB9w4kzyyvy&track_authorization={track_authorization}",headers={"user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/536.30.1 (KHTML, like Gecko) Version/6.0.5 Safari/536.30.1"}).json()["url"]).text.splitlines() if line.startswith("http")]):
                    temp_file = f"temp_{i}.BY_VOID"
                    temp_files.append(temp_file)
                    with requests.get(url, stream=True) as r:
                        with open(temp_file, 'wb') as f:
                            f.write(r.content)

                with open("file_list.txt", "w") as file_list:
                    for temp_file in temp_files:
                        file_list.write(f"file '{temp_file}'\n")

                output_file = "output.mp3"
                (
                    ffmpeg
                    .input('file_list.txt', format='concat', safe=0)
                    .output(output_file, codec='copy')
                    .run(cmd=ffmpeg_path)
                )

                for temp_file in temp_files:
                    os.remove(temp_file)
                os.remove("file_list.txt")

                print(f"Конвертация завершена! Файл сохранен как {output_file}")
            except json.JSONDecodeError as e:
                print(f'Ошибка декодирования JSON: {e}')
            break 
