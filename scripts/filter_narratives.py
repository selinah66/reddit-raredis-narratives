import pandas as pd

df = pd.read_csv("reddit_posts_cleaned.csv")

experience_keywords = [
    "i was diagnosed",
    "i am diagnosed",
    "my symptoms",
    "my experience",
    "i have been",
    "living with",
    "it started",
    "over the years",
    "i suffer from",
    "i struggle with"
]

df["text_lower"] = df["text"].str.lower()

experience_posts = df[
    df["text_lower"].str.contains("|".join(experience_keywords), na=False)
]

experience_posts = experience_posts.drop(columns=["text_lower"])
experience_posts.to_csv("experience_posts.csv", index=False)

print(f"Cleaned posts: {len(df)}")
print(f"Experience posts: {len(experience_posts)}")
