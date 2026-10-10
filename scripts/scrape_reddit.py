import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime
import os
import random
import json
from urllib.parse import urlparse, parse_qs

# Constants and configuration
TARGET_POSTS = 1000
ADDITIONAL_POSTS = 124        # number of extra accepted posts to collect when resuming
MAX_PAGES = 1000            # increased cap to allow more paging if many posts filtered
post_sleep = 10             # seconds between fetching individual post pages
page_sleep = 15            # seconds between listing page requests
save_every = 25
OUTPUT_DIR = "/Users/Selina/Documents/reddit_rare_disease/data"
output_csv = os.path.join(OUTPUT_DIR, "reddit_scraped_posts.csv")
ANONYMIZE_USERNAMES = False
BASE_URL = "https://old.reddit.com/r/rarediseases/new/"

posts = []
seen_urls = set()
accepted = 0

os.makedirs(OUTPUT_DIR, exist_ok=True)
state_path = os.path.join(OUTPUT_DIR, "scrape_state.json")

if os.path.exists(output_csv):
    try:
        df_prev = pd.read_csv(output_csv)
        # ensure columns exist
        if "url" in df_prev.columns:
            posts = df_prev.to_dict(orient="records")
            seen_urls = set(r["url"] for r in posts if isinstance(r.get("url"), str))
            accepted = len(posts)
            print(f"Resuming from existing CSV: loaded {accepted} accepted posts.")
            if accepted > 0:
                old_target = TARGET_POSTS
                TARGET_POSTS = 1000
                print(f"Adjusted TARGET_POSTS from {old_target} -> {TARGET_POSTS} to collect {ADDITIONAL_POSTS} additional posts.")
            else:
                print("Existing CSV found but no 'url' column — starting fresh.")
    except Exception as e:
        print("Failed to load existing CSV, starting fresh:", e)

url = BASE_URL
if os.path.exists(state_path):
    try:
        with open(state_path, "r") as fh:
            state = json.load(fh)
        last_after = state.get("last_after")  # full t3_xxx token
        last_url = state.get("last_url")
        # Prefer last_url if present (more robust)
        if last_url:
            url = last_url
            print("Resuming listing from last saved URL:", url)
        elif last_after:
            # build listing URL with the same 'count' param as before (safe fallback)
            url = BASE_URL + f"?count=0&after={last_after}"
            print("Resuming listing using last_after token:", last_after)
    except Exception as e:
        print("Failed to read state file — starting from base URL:", e)

# session with retries
session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (academic research; public data; contact: selina.hui2005@gmail.com)",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.google.com/"
}

# megathread filter patterns
MEGATHREAD_PATTERNS = [
    r"\bmegathread\b", r"\bweekly\b", r"\bmonthly\b", r"\bmoderator\b",
    r"\bcontest\b", r"\bgiveaway\b", r"\badverti(s|se|sement)\b",
    r"\bsponsored\b", r"\bpromo\b"
]
MEGATHREAD_RE = re.compile("|".join(MEGATHREAD_PATTERNS), re.IGNORECASE)

def save_state(next_url=None, after_token=None):
    """Save minimal resume state (last_url and last_after token)."""
    state = {"last_url": next_url if next_url else None,
             "last_after": after_token if after_token else None}
    try:
        with open(state_path, "w") as fh:
            json.dump(state, fh)
    except Exception as e:
        print("Warning: failed to write state file:", e)

def looks_like_megathread(text):
    return bool(text and MEGATHREAD_RE.search(text))

def extract_iso_datetime(post_soup, listing_post):
    time_tag = post_soup.find("time")
    if time_tag and time_tag.has_attr("datetime"):
        try:
            dt = datetime.fromisoformat(time_tag["datetime"].replace("Z", "+00:00"))
            return dt.isoformat()
        except Exception:
            pass
    if listing_post:
        ts = listing_post.get("data-timestamp") or listing_post.get("data-time")
        if ts:
            try:
                ts_n = int(ts)
                if ts_n > 1e12:
                    ts_n = ts_n / 1000.0
                dt = datetime.utcfromtimestamp(ts_n)
                return dt.isoformat() + "Z"
            except Exception:
                pass
    span_ts = post_soup.find(attrs={"data-timestamp": True})
    if span_ts:
        try:
            ts_n = int(span_ts["data-timestamp"])
            if ts_n > 1e12:
                ts_n = ts_n / 1000.0
            dt = datetime.utcfromtimestamp(ts_n)
            return dt.isoformat() + "Z"
        except Exception:
            pass
    header = post_soup.find(["p", "span"])
    if header and header.text:
        m = re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b.*\d{4}', header.text)
        if m:
            return m.group(0)
    return ""

# counters for diagnostics
skipped_megathread = 0
skipped_empty = 0
total_inspected = 0
skipped_duplicate = 0

# Main scraping loop
for page_index in range(MAX_PAGES):
    print(f"[Page {page_index+1}] Fetching listing: {url}")
    try:
        response = session.get(url, headers=HEADERS, timeout=30)
    except requests.exceptions.RequestException as e:
        print("Listing request failed:", e)
        break

    if response.status_code == 429:
        print("429 Too Many Requests — stopping.")
        break
    if response.status_code != 200:
        print("Listing request failed:", response.status_code)
        break

    soup = BeautifulSoup(response.text, "html.parser")
    post_divs = soup.find_all("div", class_="thing")

    for post in post_divs:
        total_inspected += 1

        # listing info
        title_el = post.find("a", class_="title")
        listing_title = title_el.text.strip() if title_el else (post.get("data-title") or "").strip()
        author_listing = post.get("data-author") or ""
        permalink = post.get("data-permalink")
        if not permalink:
            continue
        post_url = "https://old.reddit.com" + permalink
        
        if post_url in seen_urls:
            skipped_duplicate += 1
            continue

        # fetch post page
        try:
            post_resp = session.get(post_url, headers=HEADERS, timeout=45)
        except requests.exceptions.RequestException as e:
            print("Skipping post due to error:", e)
            continue

        # polite sleep with jitter
        time.sleep(post_sleep + random.uniform(10, 25))

        if post_resp.status_code == 429:
            print("429 encountered on post page - stopping.")
            break
        if post_resp.status_code != 200:
            print("Post fetch failed:", post_resp.status_code, post_url)
            continue

        post_soup = BeautifulSoup(post_resp.text, "html.parser")

        # title extraction: og:title -> h1 -> fallback listing
        page_title = ""
        og = post_soup.find("meta", property="og:title")
        if og and og.has_attr("content") and og["content"].strip():
            page_title = og["content"].strip()
        else:
            h1 = post_soup.find("h1")
            if h1 and h1.text.strip():
                page_title = h1.text.strip()
            else:
                a_title = post_soup.find("a", class_="title")
                if a_title and a_title.text.strip():
                    page_title = a_title.text.strip()
        title = page_title or listing_title

        # author resolution
        author = author_listing
        if not author:
            a_author = post_soup.find("a", class_="author")
            if a_author:
                author = a_author.text.strip()

        # author flair
        author_flair = post.get("data-author-flair-text") or ""
        if not author_flair:
            fl = post_soup.find("span", class_="flair")
            if fl:
                author_flair = fl.text.strip()

        # post date
        post_date = extract_iso_datetime(post_soup, post)

        # extract body
        post_text = ""
        body_div = post_soup.find("div", class_="expando") or post_soup.find("div", class_="usertext-body")
        if body_div:
            paragraphs = body_div.find_all("p")
            post_text = "\n".join(p.get_text(strip=True) for p in paragraphs)

        if not post_text.strip():
            skipped_empty += 1
            print("Skipping empty post body:", post_url)
            seen_urls.add(post_url)
            continue

        combined_text = title + " " + post_text

        # megathread filter
        if looks_like_megathread(combined_text):
            skipped_megathread += 1
            print("Filtered (megathread/announcement):", title[:120])
            seen_urls.add(post_url)
            continue

        # passed filters -> accept
        stored_author = author if not ANONYMIZE_USERNAMES else ""

        posts.append({
            "title": title,
            "url": post_url,
            "author": stored_author,
            "author_flair": author_flair,
            "post_date": post_date,
            "text": post_text
        })
        seen_urls.add(post_url)
        accepted += 1
        if accepted % 5 == 0:
            save_state(next_url=url)
        
        if accepted >= TARGET_POSTS:
            print(f"Reached {TARGET_POSTS} accepted posts — stopping.")
            break

        if accepted % save_every == 0:
            pd.DataFrame(posts).to_csv(output_csv, index=False)
            print(f"Saved {accepted} accepted posts to {output_csv}")
            
    if accepted >= TARGET_POSTS:
            break

    next_button = soup.find("span", class_="next-button")
    if not next_button:
        print("No next button — reached end of subreddit listings.")
        # clear saved state so next run starts from base
        try:
            if os.path.exists(state_path):
                os.remove(state_path)
        except:
            pass
        break

    next_href = next_button.find("a")["href"]
    # save state: store the exact next-page URL and extract after token if present
    url = next_href
    # try to extract 'after' token for convenience
    try:
        parsed = urlparse(next_href)
        q = parse_qs(parsed.query)
        after_token = q.get("after", [None])[0]
    except Exception:
        after_token = None

    save_state(next_url=next_href, after_token=after_token)

    time.sleep(page_sleep + random.uniform(0,2))

# final save & diagnostics
pd.DataFrame(posts).to_csv(output_csv, index=False)
print(f"Finished. Collected {accepted} accepted posts -> {output_csv}")
print("Diagnostics: total inspected:", total_inspected, "accepted:", accepted,
      "skipped_empty:", skipped_empty, "skipped_megathread:", skipped_megathread, "skipped_duplicate:", skipped_duplicate)
