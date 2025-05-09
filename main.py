from bs4 import BeautifulSoup
import json
import re
import ffmpeg
import aiohttp
import asyncio

async def get_soundcloud_client_id():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('https://soundcloud.com') as response:
                if response.status != 200:
                    raise Exception(f"Ошибка: {response.status}")
                html = await response.text()

            script_pattern = re.compile(r'<script[^>]+src="([^"]+)"', re.IGNORECASE)
            script_urls = script_pattern.findall(html)

            for url in script_urls:
                if not url.startswith(('https://a-v2.sndcdn.com', 'https://a1.sndcdn.com')):
                    continue

                try:
                    async with session.get(url) as script_response:
                        if script_response.status != 200:
                            continue
                        script_text = await script_response.text()

                        client_id_match = re.search(r'client_id\s*:\s*"([0-9a-zA-Z]{32})"', script_text)
                        if client_id_match:
                            return client_id_match.group(1)

                except Exception as e:
                    continue

            raise Exception("Client ID не найден")

        except Exception as e:
            raise Exception(f"Ошибка при получении client_id: {str(e)}")

async def main():
    music_url = input("Ссылка на музыку soundcloud: ")
    ffmpeg_path = 'ВАШ ПУТЬ К ffmpeg.exe'
    async with aiohttp.ClientSession() as session:
        soup = BeautifulSoup(await (await session.get(music_url,headers={"user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/536.30.1 (KHTML, like Gecko) Version/6.0.5 Safari/536.30.1"})).text(), 'html.parser')
        
        for script in soup.find_all('script'):
            if script.string:
                match = re.compile(r'window\.__sc_hydration\s*=\s*(\[\{.*?\}\]);', re.DOTALL).search(script.string)
                if match:
                    try:
                        for item in json.loads(match.group(1)):
                            if 'data' in item and 'media' in item['data']:
                                for transcoding in item['data']['media'].get('transcodings', []):
                                    if transcoding['format']['protocol'] == 'hls':
                                        hls_url = transcoding['url']
                                        break
                        track_auth_match = re.compile(r'"track_authorization":\s*"([^"]+)"').search(script.string)
                        if track_auth_match:
                            track_authorization = track_auth_match.group(1)
                
                        m3u8_url = (await (await session.get(f"{hls_url}?client_id={await get_soundcloud_client_id()}&track_authorization={track_authorization}",headers={"user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/536.30.1 (KHTML, like Gecko) Version/6.0.5 Safari/536.30.1"})).json())["url"]

                        output_file = "output.mp3"
                        (
                            ffmpeg
                            .input(m3u8_url)
                            .output(output_file)
                            .overwrite_output()
                            .run(cmd=ffmpeg_path)
                        )

                        print(f"Конвертация завершена! Файл сохранен как {output_file}")
                    except json.JSONDecodeError as e:
                        print(f'Ошибка декодирования JSON: {e}')
                    break 

asyncio.run(main())
