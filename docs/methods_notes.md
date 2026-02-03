## Data Collection

Public Reddit posts were collected from the r/rarediseases subreddit
using HTML scraping of old.reddit.com. Requests were heavily rate-limited
to minimize server load and comply with ethical research practices.
No login or authentication was used.

## Ethical Considerations

Only publicly available posts were collected. Usernames, comments,
and identifying metadata were excluded. Data were analyzed in aggregate
for research purposes only.

## Narrative Filtering

Posts were filtered using keyword-based heuristics to identify
first-person patient or caregiver narratives describing illness
experiences.

## Rule-Based Extraction

A rule-based NLP approach using regular expressions was used to extract
structured variables from narrative text. This approach was chosen for
its interpretability, reproducibility, and suitability for small to
moderate qualitative datasets.

Variables extracted include diagnosis status, symptom presence,
diagnostic difficulty, treatment mentions, psychosocial impact, and
healthcare system experiences.
