# extract_rules.py
import re
import pandas as pd

def any_match(text, patterns):
    """Return True if any pattern (regex or string) matches text (case-insensitive)."""
    if not isinstance(text, str): 
        return False
    t = text.lower()
    for p in patterns:
        if isinstance(p, re.Pattern):
            if p.search(t):
                return True
        else:
            if p in t:
                return True
    return False

def extract_multi(text, patterns):
    """Return list of pattern keys that matched in text."""
    matches = []
    if not isinstance(text, str):
        return matches
    t = text.lower()
    for key, pats in patterns.items():
        for p in pats:
            if isinstance(p, re.Pattern):
                if p.search(t):
                    matches.append(key); break
            else:
                if p in t:
                    matches.append(key); break
    return sorted(set(matches))

def extract_first_match(text, patterns):
    """Return the first category that matches (or None)."""
    if not isinstance(text, str): 
        return None
    t = text.lower()
    for key, pats in patterns.items():
        for p in pats:
            if isinstance(p, re.Pattern):
                if p.search(t):
                    return key
            else:
                if p in t:
                    return key
    return None

def extract_timelines(text):
    """Simple extraction of numeric years/phrases like 'x years', 'since childhood', 'recently'."""
    if not isinstance(text, str): 
        return ""
    t = text.lower()
    years = re.findall(r'(\d{1,2})\s*(?:years|yrs)\b', t)
    phrases = []
    if 'childhood' in t or 'from birth' in t or 'since birth' in t:
        phrases.append('congenital')
    if 'recent' in t or 'recently' in t or 'last month' in t or 'last year' in t:
        phrases.append('recent')
    return ", ".join(years + phrases)

# Keyword & pattern dictionaries
DIAGNOSIS_PATTERNS = {
    "undiagnosed": [
        # direct negative statements
        re.compile(r"\b(still\s+(do\s*not|don['’]t|haven['’]t)\s+have\s+(a|an|the)?\s*(clear\s*)?diagnos(is|ed))\b", re.IGNORECASE),
        re.compile(r"\b(haven'?t been (formally )?diagnosed|not formally diagnosed)\b", re.IGNORECASE),
        re.compile(r"\b(no diagnosis|no clear diagnosis|without a diagnosis|still undiagnosed|undiagnosed|still no diagnosis)\b", re.IGNORECASE),
        re.compile(r"\bdon'?t have (an |a |the )?(official )?diagnos(?:is|ed)\b", re.IGNORECASE),
        # phrasing like "I still don’t have a (clear) diagnosis" (allow arbitrary filler)
        re.compile(r"\b(still (do(es)?|did(n't)?)? ?not? have( a| an| the)?( .*?)?diagnos(?:is|ed))\b", re.IGNORECASE)
    ],
    "diagnosed": [
        # classic explicit diagnosed phrasing
        re.compile(r"\b(diagnosed with|diagnosis of|was diagnosed|were diagnosed|am diagnosed|i'm diagnosed)\b", re.IGNORECASE),
        # phrasing like "my experience with a X" (user requested mapping -> flagged as diagnosed)
        re.compile(r"\bmy experience with (a |an |the )?[a-z0-9][\w\W]{0,80}\b", re.IGNORECASE), # might remove this rule if false positives
        # "due to a rare condition" or "due to an extremely rare multisystem condition" => likely diagnosed
        re.compile(r"\bdue to\s+(a|an|the)\s+(?:\w+\s+){0,6}?(rare|extremely rare|very rare)\s+(?:\w+\s+){0,4}?(condition|disease|disorder|syndrome)\b", re.IGNORECASE),
        # "diagnosis: X" or "DX: X"
        re.compile(r"\b(diagnosis[:]\s*[\w\- ]+|dx[:]\s*[\w\- ]+)\b", re.IGNORECASE)
    ],
    "congenital": [
        re.compile(r"\b(from birth|since birth|congenital|since childhood|born with)\b", re.IGNORECASE)
    ],
    "suspected": [
        re.compile(r"\b(suspect(ed)?|possible (?:diagnosis|condition)|probable (?:diagnosis|condition)|I think it might be)\b", re.IGNORECASE)
    ]
}

# Load data
df = pd.read_csv("experience_posts.csv")
df['text'] = df['text'].fillna("").astype(str)
df['title'] = df.get('title', "").fillna("").astype(str)

# Extraction
# Diagnosis status: prefer "diagnosed" > "congenital" > "undiagnosed" > "suspected"
def get_diagnosis_status(text):
    """
    Advanced decision logic:
    1) If explicit 'undiagnosed' signals exist -> 'undiagnosed'
    2) Else if explicit 'diagnosed' signals exist -> 'diagnosed'
    3) Else if 'congenital' signals -> 'congenital'
    4) Else if 'suspected' signals -> 'suspected'
    5) Else -> 'unspecified'
    If both 'diagnosed' and 'undiagnosed' match, prefer 'undiagnosed' when the undiagnosed pattern contains negation words (don't/haven't/etc).
    """
    if not isinstance(text, str):
        return "unspecified"

    t = text  # we'll use regex with IGNORECASE already
    matched = {k: any(p.search(t) for p in pats) for k, pats in DIAGNOSIS_PATTERNS.items()}

    # If both diagnosed & undiagnosed signals present, try to disambiguate:
    if matched.get("undiagnosed") and matched.get("diagnosed"):
        # If undiagnosed matched via explicit negation patterns, prefer undiagnosed
        # (our undiagnosed patterns are designed to include negations like "don't have", "haven't been diagnosed")
        return "undiagnosed"

    # Standard ordering
    if matched.get("undiagnosed"):
        return "undiagnosed"
    if matched.get("diagnosed"):
        return "diagnosed"
    if matched.get("congenital"):
        return "congenital"
    if matched.get("suspected"):
        return "suspected"

    return "unspecified"

df['diagnosis_status'] = df['text'].apply(get_diagnosis_status)

# Quick check of test cases
tests = [
    "I still don’t have a clear diagnosis and I'm frustrated.",
    "My experience with a rare neuro condition started last year.",
    "Due to an extremely rare multisystem condition, I have chronic fatigue.",
    "Haven't been formally diagnosed despite many tests.",
    "I don't have an official diagnosis."
]

for t in tests:
    print(t, "=>", get_diagnosis_status(t))

# Compute output
out = "experience_posts_extracted.csv"
df.to_csv(out, index=False)
print(f"Saved extracted file to: {out}")

