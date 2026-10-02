import re

STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'for', 'to', 'of', 'in', 'on', 'with',
    'is', 'are', 'i', 'need', 'want', 'have', 'looking', 'help', 'can',
    'will', 'would', 'should', 'please', 'thanks',
}

def _keywords(text):
    tokens = re.findall(r'[a-z]+', (text or '').lower())
    return {token for token in tokens if len(token) >= 3 and token not in STOPWORDS}

def _as_dict(record):
    if hasattr(record, 'keys'):
        return {key: record[key] for key in record.keys()}
    return dict(record)

def explain_match(need, offer):
    need_data = _as_dict(need)
    offer_data = _as_dict(offer)
    need_cat = str(need_data.get('category', '')).strip().lower()
    offer_cat = str(offer_data.get('category', '')).strip().lower()
    category = 50 if need_cat and need_cat == offer_cat else 0
    keywords_a = _keywords(f"{need_data.get('title', '')} {need_data.get('description', '')}")
    keywords_b = _keywords(f"{offer_data.get('title', '')} {offer_data.get('description', '')}")
    union = keywords_a | keywords_b
    inter = keywords_a & keywords_b
    keywords = round(40 * (len(inter) / len(union)), 2) if keywords_a and keywords_b and union else 0.0
    urgency_map = {'high': 10, 'medium': 5, 'low': 0}
    urgency = urgency_map.get(str(need_data.get('urgency', '')).lower(), 0)
    reputation = min(float(offer_data.get('average_rating', 0) or 0) * 2, 10)
    reputation = round(reputation, 2)
    total = min(100, category + keywords + urgency + reputation)
    return {
        'category': category,
        'keywords': keywords,
        'shared_keywords': sorted(inter),
        'urgency': urgency,
        'reputation': reputation,
        'total': round(total, 2),
    }

def score_match(need, offer):
    return explain_match(need, offer)['total']

def find_best_matches(need, offers, limit=5):
    scored = []
    for offer in offers:
        score = score_match(need, offer)
        if score > 0:
            created = offer.get('created_at', '') if hasattr(offer, 'get') else ''
            scored.append((score, created, offer))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [offer for _, _, offer in scored[:limit]]
