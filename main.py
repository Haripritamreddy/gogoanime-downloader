import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tqdm import tqdm

#STEP - 1
url = input("Enter URL: ")
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
total_episodes = int(soup.find('ul', {'id': 'episode_page'}).find('a')['ep_end'])
print(f"Total episodes: {total_episodes}")

#STEP - 2 
episodes = input("Enter Episodes: ")
if episodes == "all":
    start_episode = 1
    end_episode = total_episodes
elif '-' in episodes:
    start_episode, end_episode = map(int, episodes.split('-'))
else:
    start_episode, end_episode = int(episodes), int(episodes)
    
episode_url_format = f"https://{(url := url.replace('category/', '').replace('-tv', '')).split('/')[2]}/{url.split('/')[-1]}-episode-{{}}"

# STEP - 3 
download_links = []
for episode in range(start_episode, end_episode + 1):
    episode_url = episode_url_format.format(episode)
    response = requests.get(episode_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    download_link = soup.find('li', {'class': 'dowloads'}).find('a')['href']
    download_links.append(download_link)

#STEP - 4
folder_name = input("Enter folder name: ")
folder_path = os.path.join(os.getcwd(), folder_name)

if not os.path.exists(folder_path):
    os.makedirs(folder_path)


options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--log-level=3')

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
