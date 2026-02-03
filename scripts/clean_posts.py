import pandas as pd

df = pd.read_csv("reddit_posts.csv")

# Remove megathreads / wiki / admin posts
exclude_keywords = [
    "megathread",
    "weekly",
    "wiki",
    "moderator",
    "mod post"
]

df["title_lower"] = df["title"].str.lower()

cleaned = df[~df["title_lower"].str.contains("|".join(exclude_keywords), na=False)]

cleaned = cleaned.drop(columns=["title_lower"])
cleaned.to_csv("reddit_posts_cleaned.csv", index=False)

print(f"Original posts: {len(df)}")
print(f"After removing megathreads: {len(cleaned)}")
