import requests, random

# Real, well-known songs as search seeds per mood — far more reliable than generic genre phrases
MOOD_SEEDS = {
    'calm':        ['Ed Sheeran Perfect', 'Norah Jones Come Away With Me', 'Bon Iver Skinny Love'],
    'peaceful':    ['Norah Jones Come Away With Me', 'Jack Johnson Better Together', 'Iron & Wine Flightless Bird'],
    'dreamy':      ['Lana Del Rey Video Games', 'Beach House Space Song', 'Cigarettes After Sex Apocalypse'],
    'romantic':    ['Ed Sheeran Perfect', 'John Legend All of Me', 'Adele Make You Feel My Love'],
    'melancholic': ['Adele Someone Like You', 'Sam Smith Stay With Me', 'Billie Eilish Everything I Wanted'],
    'energetic':   ['Dua Lipa Levitating', 'The Weeknd Blinding Lights', 'Bruno Mars Uptown Funk'],
    'happy':       ['Pharrell Williams Happy', 'Justin Timberlake Cant Stop the Feeling', 'Katrina and the Waves Walking on Sunshine'],
    'nostalgic':   ['a-ha Take On Me', 'Journey Dont Stop Believin', 'Fleetwood Mac Dreams'],
    'dark':        ['Billie Eilish Bad Guy', 'Lorde Royals', 'The Weeknd Blinding Lights'],
    'intense':     ['Imagine Dragons Believer', 'Linkin Park Numb', 'Muse Uprising'],
    'adventurous': ['Imagine Dragons Radioactive', 'Fun Some Nights', 'Coldplay Adventure of a Lifetime'],
    'mysterious':  ['Billie Eilish Bury a Friend', 'Massive Attack Teardrop', 'Radiohead Everything In Its Right Place'],
}

BAD_WORDS = ['instrumental', 'karaoke', 'backing track', 'made famous by', 'tribute']

def _is_junk(t, query):
    title  = t['title'].lower()
    artist = t['artist']['name'].lower()
    if any(bw in title for bw in BAD_WORDS):
        return True
    if artist == query.lower():
        return True
    return False

def get_tracks(mood, mood2=None, n=6):
    m1 = (mood or '').lower()
    m2 = (mood2 or '').lower()

    seeds = MOOD_SEEDS.get(m1, ['Ed Sheeran Perfect'])
    if m2 and m2 != m1 and m2 in MOOD_SEEDS:
        seeds = seeds + MOOD_SEEDS[m2]

    try:
        all_results = []
        # search 2 different seed songs, gather results from both
        for seed in random.sample(seeds, min(2, len(seeds))):
            r = requests.get(f"https://api.deezer.com/search?q={seed}&order=RANKING&limit=15", timeout=5).json()
            all_results += r.get('data', [])

        clean = [t for t in all_results if not _is_junk(t, '')]

        seen, final = set(), []
        for t in clean:
            key = (t['title'], t['artist']['name'])
            if key not in seen:
                seen.add(key)
                final.append(t)

        random.shuffle(final)
        picks = final[:n]
        if not picks:
            raise ValueError("empty")

        return [{'title':  t['title'][:27] + '...' if len(t['title']) > 30 else t['title'],
                 'artist': t['artist']['name'],
                 'preview': t['preview']} for t in picks]
    except Exception:
        return [{'title': 'Space Song', 'artist': 'Beach House', 'preview': ''},
                {'title': 'After Dark',  'artist': 'Mr.Kitty',    'preview': ''}]