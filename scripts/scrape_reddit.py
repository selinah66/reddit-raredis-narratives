import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import pandas as pd
import time

session = requests.Session()

retries = Retry(
    total=3,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (academic research; public data; contact: selina.hui2005@gmail.com)"
}

BASE_URL = "https://old.reddit.com/r/rarediseases/"
posts = []

url = BASE_URL

for page in range(5):  # start small
    print(f"Scraping page {page + 1}")

    response = session.get(url, headers=HEADERS, timeout=30)

    if response.status_code != 200:
        print("Request failed:", response.status_code)
        break

    soup = BeautifulSoup(response.text, "html.parser")
    post_divs = soup.find_all("div", class_="thing", attrs={"data-domain": "self.rarediseases"})

    for post in post_divs:
        title = post.find("a", class_="title")
        permalink = post.get("data-permalink")
        if not permalink:
            continue

        post_url = "https://old.reddit.com" + permalink
        try:
            post_resp = session.get(post_url, headers=HEADERS, timeout=45)
        except requests.exceptions.RequestException as e:
            print("Skipping post due to error:", e)
            continue
        
        time.sleep(6)  # VERY important

        post_soup = BeautifulSoup(post_resp.text, "html.parser")
        post_text = ""

        body_div = post_soup.find("div", class_="expando")
        if not body_div:
            body_div = post_soup.find("div", class_="usertext-body")

        if body_div:
            paragraphs = body_div.find_all("p")
            post_text = "\n".join(p.get_text(strip=True) for p in paragraphs)

        posts.append({
            "title": title.text.strip() if title else "",
            "url": post_url,
            "text": post_text
        })
        
        if not post_text.strip():
            continue
    
    next_button = soup.find("span", class_="next-button")
    if not next_button:
        break

    url = next_button.find("a")["href"]
    time.sleep(10)  # heavy rate limit

df = pd.DataFrame(posts)
df.to_csv("reddit_posts.csv", index=False)

print(f"Collected {len(df)} posts")
