import requests, random

MOOD_SEEDS = {
    'calm':        ['Ed Sheeran Perfect', 'Norah Jones Come Away With Me', 'Bon Iver Skinny Love', 'Jungkook Stay Alive'],
    'peaceful':    ['Norah Jones Come Away With Me', 'Jack Johnson Better Together', 'Iron & Wine Flightless Bird'],
    'dreamy':      ['Lana Del Rey Video Games', 'Beach House Space Song', 'Cigarettes After Sex Apocalypse',
                     'a-ha Take On Me', 'Damiano David Tangerine', 'Damiano David Cinnamon'],
    'romantic':    ['Michael Jackson Another Part of Me', 'Harry Styles Sign of the Times', 'Jimin Be Mine',
                     'Bryan Adams Please Forgive Me', 'Bon Jovi Always', 'Righteous Brothers Unchained Melody',
                     'Frankie Valli Cant Take My Eyes Off You', 'Berlin Take My Breath Away', 'Kiss I Was Made For Lovin You'],
    'melancholic': ['Adele Someone Like You', 'Sam Smith Stay With Me',
                    'Billie Eilish Everything I Wanted', 'Lewis Capaldi Someone You Loved',
                    'James Arthur Say You Wont Let Go', 'Passenger Let Her Go',
                    'Coldplay The Scientist', 'Ed Sheeran Happier',
                    'Taylor Swift All Too Well'],
    'heartbreak':  ['Damiano David Voices', 'Damiano David Born With a Broken Heart', 'Brooks and Dunn My Next Broken Heart',
                     'Brooks and Dunn Gone', 'ABBA The Winner Takes It All', 'Billy Joel Vienna', 'ABBA Angel Eyes'],
    'energetic':   ['Dua Lipa Levitating', 'The Weeknd Blinding Lights', 'ABBA Gimme Gimme Gimme',
                     'Franz Ferdinand Take Me Out', 'Chris Young Im Coming Over'],
    'happy':       ['Pharrell Williams Happy', 'The Turtles Happy Together', 'Modern Talking Brother Louie',
                     'Chris Young Beer or Gasoline', 'Jungkook Standing Next to You', '5 Seconds of Summer English Love Affair'],
    'nostalgic':   ['Billy Joel Piano Man', 'a-ha Take On Me', 'The Turtles Happy Together', 'Modern Talking Brother Louie'],
    'dark':        ['Billie Eilish Bad Guy', 'Yungblud Zombie', 'Michael Jackson Thriller'],
    'intense':     ['Imagine Dragons Believer', 'Yungblud Zombie', 'Linkin Park Numb'],
    'adventurous': ['Young the Giant Strings', 'Young the Giant Garlands', 'Young the Giant Saint Walker',
                     'Mumford and Sons Tompkins Square Park', 'Stephen Sanchez Hold On While You Can'],
     'mysterious':  ['Damiano David Mysterious Girl', 'a-ha Take On Me', 'Damiano David First Time', 'Michael Jackson Bad',
                     'Michael Jackson Human Nature', 'Radiohead Everything In Its Right Place', 'Walk The Moon Shut Up and Dance'],
}


BAD_WORDS = ['instrumental', 'karaoke', 'backing track', 'made famous by', 'tribute', 'acoustic',
             '8-bit', '16-bit', 'remix', 'cover', 'lullaby', 'nightcore', 'live', 'version']

def _is_junk(t):
    title = t['title'].lower()
    return any(bw in title for bw in BAD_WORDS)

def _norm(title):
    return ''.join(c for c in title.lower() if c.isalnum())

def get_tracks(mood, mood2=None, n=6, exclude=None):
    exclude = exclude or set()
    m1 = (mood or '').lower()
    m2 = (mood2 or '').lower()

    seeds = MOOD_SEEDS.get(m1, ['Ed Sheeran Perfect'])
    if m2 and m2 != m1 and m2 in MOOD_SEEDS:
        seeds = seeds + MOOD_SEEDS[m2]

    try:
        all_results = []
        for seed in random.sample(seeds, min(5, len(seeds))):
            r = requests.get(f"https://api.deezer.com/search?q={seed}&order=RANKING&limit=15", timeout=5).json()
            all_results += r.get('data', [])

        clean = [t for t in all_results if not _is_junk(t)]
        random.shuffle(clean)

        seen_titles, artist_count, final = set(), {}, []

        for t in clean:
            key = (_norm(t['title']), t['artist']['name'])
            if key in exclude:
                continue
            if key[0] in seen_titles:
                continue
            if artist_count.get(t['artist']['name'], 0) >= 2:
                continue
            seen_titles.add(key[0])
            artist_count[t['artist']['name']] = artist_count.get(t['artist']['name'], 0) + 1
            final.append(t)
            if len(final) >= n:
                break

        if len(final) < n:
            for t in clean:
                key = (_norm(t['title']), t['artist']['name'])
                if key[0] in seen_titles:
                    continue
                seen_titles.add(key[0])
                final.append(t)
                if len(final) >= n:
                    break

        if not final:
            raise ValueError("empty")

        return [{'title':  t['title'][:27] + '...' if len(t['title']) > 30 else t['title'],
                 'artist': t['artist']['name'],
                 'preview': t['preview'],
                 '_key': (_norm(t['title']), t['artist']['name'])} for t in final]
    except Exception:
        return [{'title': 'Space Song', 'artist': 'Beach House', 'preview': '', '_key': ('spacesong','Beach House')},
                {'title': 'After Dark',  'artist': 'Mr.Kitty',    'preview': '', '_key': ('afterdark','Mr.Kitty')}]