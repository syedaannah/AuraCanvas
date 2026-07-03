import requests, random

MOOD_TERMS = {
    'calm':        ['acoustic', 'chill pop', 'soft indie'],
    'peaceful':    ['soft indie', 'gentle folk', 'acoustic'],
    'dreamy':      ['dream pop', 'ethereal pop', 'indie dream'],
    'romantic':    ['love ballad', 'soul', 'r&b love'],
    'melancholic': ['sad indie', 'melancholy pop', 'emotional ballad'],
    'energetic':   ['upbeat pop', 'dance pop', 'high energy pop'],
    'happy':       ['feel good pop', 'summer pop', 'happy indie'],
    'nostalgic':   ['80s pop', 'retro pop', 'throwback hits'],
    'dark':        ['dark pop', 'moody alternative', 'gothic rock'],
    'intense':     ['powerful rock', 'epic alternative', 'cinematic rock'],
    'adventurous': ['folk rock', 'indie rock', 'anthemic rock'],
    'mysterious':  ['trip hop', 'moody alternative', 'dark pop'],
}

BAD_WORDS = ['instrumental', 'karaoke', 'backing track', 'made famous by']

def _is_junk(t, query):
    title  = t['title'].lower()
    artist = t['artist']['name'].lower()
    q      = query.lower()

    if any(bw in title for bw in BAD_WORDS):
        return True
    # generic library-track pattern: artist name IS the genre/search term
    if artist == q or artist in q or q in artist:
        return True
    # title is just the genre word plus a number, e.g. "Trip Hop 19"
    stripped = ''.join(c for c in title if not c.isdigit()).strip()
    if stripped == q:
        return True
    return False

def _search(query, n):
    url = f"https://api.deezer.com/search?q={query}&order=RANKING&limit=25"
    r = requests.get(url, timeout=5).json()
    results = r.get('data', [])
    clean = [t for t in results if not _is_junk(t, query)]
    random.shuffle(clean)
    return clean

def get_tracks(mood, mood2=None, n=6):
    m1 = (mood or '').lower()
    m2 = (mood2 or '').lower()

    pool = MOOD_TERMS.get(m1, ['pop'])
    if m2 and m2 != m1 and m2 in MOOD_TERMS:
        pool = pool + MOOD_TERMS[m2]

    try:
        term = random.choice(pool)
        picks = _search(term, n)

        if len(picks) < n:
            term2 = random.choice(pool)
            picks += _search(term2, n)

        if len(picks) < n:
            picks += _search(f"{m1 or 'pop'} songs", n)

        seen, final = set(), []
        for t in picks:
            key = (t['title'], t['artist']['name'])
            if key not in seen:
                seen.add(key)
                final.append(t)

        if not final:
            raise ValueError("empty")

        final = final[:n]
        return [{'title':  t['title'][:27] + '...' if len(t['title']) > 30 else t['title'],
                 'artist': t['artist']['name'],
                 'preview': t['preview']} for t in final]
    except Exception:
        return [{'title': 'Space Song', 'artist': 'Beach House', 'preview': ''},
                {'title': 'After Dark',  'artist': 'Mr.Kitty',    'preview': ''}]