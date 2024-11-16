from flask import Flask, request, jsonify
import os
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Initialize Selenium WebDriver
options = Options()
options.add_argument('--headless')  # Run Chrome in headless mode
options.add_argument('--disable-gpu')
options.add_argument('--log-level=3')
options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Added to suppress DevTools messages
options.add_argument("--disable-dev-shm-usage") 

driver = webdriver.Chrome(options=options)

def get_total_episodes(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    total_episodes = int(soup.find('ul', {'id': 'episode_page'}).find('a')['ep_end'])
    return total_episodes

def get_real_download_link_from_tab(tab):
    driver.switch_to.window(tab)
    time.sleep(5)  # Allow time for redirects and page load
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    download_divs = soup.find_all('div', {'class': 'dowload'})
    for div in download_divs:
        a_tag = div.find('a')
        if a_tag and '1080P - mp4' in a_tag.text:
            real_download_link = a_tag['href']
            return real_download_link
    return None

def get_download_links(url, episodes):
    episode_url_format = f"https://{(url := url.replace('category/', '').replace('-tv', '')).split('/')[2]}/{url.split('/')[-1]}-episode-{{}}"
    episode_range = []
    if episodes == "all":
        episode_range = range(1, get_total_episodes(url) + 1)
    elif '-' in episodes:
        start_episode, end_episode = map(int, episodes.split('-'))
        episode_range = range(start_episode, end_episode + 1)
    else:
        episode_number = int(episodes)
        episode_range = range(episode_number, episode_number + 1)

    download_links = []
    all_real_download_links = []
    batch_size = 5  # Number of download links to process per batch

    for episode in episode_range:
        episode_url = episode_url_format.format(episode)
        response = requests.get(episode_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        download_link = soup.find('li', {'class': 'dowloads'}).find('a')['href']
        download_links.append(download_link)

    for i in range(0, len(download_links), batch_size):
        batch = download_links[i:i + batch_size]
        tabs = []
        for download_link in batch:
            driver.execute_script("window.open('');")
            tabs.append(driver.window_handles[-1])

        for j, tab in enumerate(tabs):
            driver.switch_to.window(tab)
            driver.get(batch[j])

        for tab in tabs:
            real_download_link = get_real_download_link_from_tab(tab)
            if real_download_link:
                all_real_download_links.append(real_download_link)

    return all_real_download_links

@app.route('/start', methods=['POST'])
def start():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        total_episodes = get_total_episodes(url)
        return jsonify({"total_episodes": total_episodes})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    episodes = data.get('episodes')
    if not url or not episodes:
        return jsonify({"error": "URL and episodes are required"}), 400

    try:
        real_download_links = get_download_links(url, episodes)
        if real_download_links:
            download_links_json = {f"episode-{i+1}": link for i, link in enumerate(real_download_links)}
            return jsonify(download_links_json)
        else:
            return jsonify({"error": "No download links found."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/exit', methods=['POST'])
def exit_server():
    driver.quit()
    return jsonify({"message": "Server is shutting down."})

if __name__ == "__main__":
    app.run(debug=True)
