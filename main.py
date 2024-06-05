import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import time
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm
import os

# STEP-1
url = input("Enter URL: ")

# STEP-2
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
total_episodes = int(soup.find('ul', {'id': 'episode_page'}).find('a')['ep_end'])
print(f"Total episodes: {total_episodes}")

# STEP-3
episodes = input("Enter Episodes: ")
if episodes == "all":
    start_episode = 1
    end_episode = total_episodes
else:
    start_episode, end_episode = map(int, episodes.split('-'))

# STEP-4
download_links = []
for episode in range(start_episode, end_episode + 1):
    episode_url = url.replace('episode-1', f'episode-{episode}')
    response = requests.get(episode_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    download_link = soup.find('li', {'class': 'dowloads'}).find('a')['href']
    print(f"Episode {episode} - {download_link}")
    download_links.append(download_link)

# STEP-5
folder_name = input("Enter folder name: ")
folder_path = os.path.join(os.getcwd(), folder_name)

if not os.path.exists(folder_path):
    os.makedirs(folder_path)

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--log-level=3')
options.add_argument('--disable-dev-shm-usage')

for download_link in download_links:
    driver = webdriver.Chrome(options=options)
    driver.get(download_link)
    time.sleep(5)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    download_divs = soup.find_all('div', {'class': 'dowload'})
    for div in download_divs:
        a_tag = div.find('a')
        if a_tag and '1080P - mp4' in a_tag.text:
            real_download_link = a_tag['href']
            episode_number = download_links.index(download_link) + start_episode
            print(f"Downloading episode {episode_number}...")
            response = requests.get(real_download_link, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            t = tqdm(total=total_size, unit='B', unit_scale=True)
            episode_number = download_links.index(download_link) + start_episode
            with open(os.path.join(folder_name, f"episode-{episode_number}.mp4"), 'wb') as f:
                for data in response.iter_content(block_size):
                    t.update(len(data))
                    f.write(data)
            t.close()
    driver.quit()
