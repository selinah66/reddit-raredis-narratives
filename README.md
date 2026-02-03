# Reddit Rare Disease Narrative Analysis

This project collects and analyzes public Reddit posts from r/rarediseases
to study patient and caregiver experiences related to rare diseases,
including diagnosis status, symptoms, diagnostic journeys, treatment,
and psychosocial impact.

All data used are publicly available posts. No usernames or identifying
information are stored or redistributed.

## Data Files

### data/reddit_posts.csv
Raw scraped Reddit posts from old.reddit.com.
Contains:
- title
- url
- text (full post body)

### data/reddit_posts_cleaned.csv
Posts after removing:
- megathreads
- moderator posts
- administrative content

### data/experience_posts.csv
Subset of posts filtered for first-person illness or caregiver narratives.

### data/experience_posts_extracted.csv
Experience posts with rule-based extraction applied (ongoing), including:
- diagnosis_status (currently working)
- condition_type (and below to be tweaked)
- diagnostic_difficulty
- symptoms
- treatment_status
- psychosocial_impact
- healthcare_system_experience

## Scripts

### scripts/clean_posts.py
Removes non-narrative posts such as megathreads and moderator content
based on title keywords.

Input:
- data/reddit_posts.csv

Output:
- data/reddit_posts_cleaned.csv

---

### scripts/filter_narratives.py
Filters posts to retain first-person experience narratives using
keyword-based rules.

Input:
- data/reddit_posts_cleaned.csv

Output:
- data/experience_posts.csv

---

### scripts/extract_rules.py
Applies rule-based NLP extraction using regular expressions to identify: (ongoing)
- diagnosis status
- condition type
- diagnostic difficulty
- symptom categories
- treatment mentions
- psychosocial impact
- healthcare system experiences

Input:
- data/experience_posts.csv

Output:
- data/experience_posts_extracted.csv

---

### scripts/scrape_reddit.py
Scrapes public Reddit posts from the r/rarediseases subreddit using
HTML-based scraping of old.reddit.com.

This script collects:
- Post titles
- Post URLs
- Full post body text (self-post narratives only)

Requests are heavily rate-limited and no authentication or login is used.
Only publicly available content is collected.

The output of this script serves as the raw input for subsequent cleaning,
filtering, and rule-based extraction steps in the analysis pipeline.

Input:
- None (direct web scraping)

Output:
- data/reddit_posts.csv

## Data Processing Pipeline

1. Scrape public Reddit posts using HTML scraping (old.reddit.com)
   → reddit_posts.csv

2. Remove non-narrative posts (megathreads, moderator posts)
   → reddit_posts_cleaned.csv

3. Filter for first-person illness and caregiver narratives
   → experience_posts.csv

4. Apply rule-based extraction to generate structured variables
   → experience_posts_extracted.csv

## Data Availability and Ethics

This project uses publicly available Reddit posts collected without
authentication or login. Usernames and identifying metadata are not stored.
Data are analyzed in aggregate and are not redistributed.
