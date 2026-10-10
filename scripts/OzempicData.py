import json

with open("/Users/Selina/Documents/reddit_GLPdrugs/Ozempicdata.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(type(data))
print(len(data["data"]["children"]))
print(data["data"]["children"][0]["data"].keys())

import pandas as pd

posts = []

for child in data["data"]["children"]:
    p = child["data"]

    posts.append({
        "id": p["id"],
        "title": p["title"],
        "text": p["selftext"],
        "created": p["created_utc"],
        "subreddit": p["subreddit"],
        "score": p["score"],
        "num_comments": p["num_comments"],
        "flair": p["link_flair_text"],
        "url": p["permalink"]
    })

df = pd.DataFrame(posts)