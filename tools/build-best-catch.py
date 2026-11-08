"""Builds data/best-catch.json: per evolution line, the most evolved stage that can be
caught in the wild in each game of a dex, with its highest wild level and where.

Run from the project root:  python tools/build-best-catch.py
Data comes from PokeAPI (pokedex, pokemon-species, evolution-chain, pokemon/<id>/encounters).
Gift Pokemon are not wild encounters and are left out.
"""
import json
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor

API = 'https://pokeapi.co/api/v2/'
OUT = 'data/best-catch.json'
SKIP_METHODS = {'gift', 'gift-egg'}

# dex name -> { PokeAPI version name: tag shown on the card }
GAMES = {
    'kanto': {'firered': 'FR', 'leafgreen': 'LG'},
}


def get(path):
    req = urllib.request.Request(API + path, headers={'User-Agent': 'mydex-data-build'})
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.load(res)


# Place names that read wrong after plain title case
PLACE_FIXES = [
    (r'^Mt ', 'Mt. '),
    (r'^Digletts', "Diglett's"),
    (r'^Pokemon', 'Pokémon'),
    (r'^Cinnabar Island Cinnabar Lab', 'Cinnabar Lab'),
    (r'^Victory Road 2 ', 'Victory Road '),
    (r' North Towards .*', ' North'),
    (r'^Safari Zone Area \d ', 'Safari Zone '),
    (r'^Sea Route', 'Route'),
]


def place(slug):
    """'kanto-route-14-area' -> 'Route 14'"""
    s = re.sub(r'-area(-\d+)?$', '', slug)
    s = re.sub(r'^kanto-', '', s)
    name = ' '.join(w.upper() if re.fullmatch(r'b?\d+f', w) else w.capitalize() for w in s.split('-'))
    for old, new in PLACE_FIXES:
        name = re.sub(old, new, name)
    return name


def stages(chain):
    """species id -> depth in the line (0 = first stage)."""
    out = {}

    def walk(node, depth):
        out[int(node['species']['url'].rstrip('/').split('/')[-1])] = depth
        for nxt in node['evolves_to']:
            walk(nxt, depth + 1)

    walk(chain['chain'], 0)
    return out


def best_wild(species_id, versions):
    """version -> (max level, location) over wild encounters, only versions with any."""
    found = {}
    for enc in get(f'pokemon/{species_id}/encounters'):
        for vd in enc['version_details']:
            v = vd['version']['name']
            if v not in versions:
                continue
            for d in vd['encounter_details']:
                if d['method']['name'] in SKIP_METHODS:
                    continue
                if v not in found or d['max_level'] > found[v][0]:
                    found[v] = (d['max_level'], place(enc['location_area']['name']))
    return found


def build(dex, versions):
    ids = [int(e['pokemon_species']['url'].rstrip('/').split('/')[-1])
           for e in get('pokedex/' + dex)['pokemon_entries']]
    with ThreadPoolExecutor(8) as pool:
        chain_url = dict(zip(ids, pool.map(
            lambda i: get(f'pokemon-species/{i}')['evolution_chain']['url'].split('/api/v2/')[1], ids)))
        chains = dict(zip(set(chain_url.values()), pool.map(
            lambda u: stages(get(u)), set(chain_url.values()))))
        wild = dict(zip(ids, pool.map(lambda i: best_wild(i, versions), ids)))

    picks = {}
    for url, depth_of in chains.items():
        members = [i for i in depth_of if i in wild]  # only species in this dex
        for v, tag in versions.items():
            catchable = [i for i in members if v in wild[i]]
            if not catchable:
                continue
            # latest evolution first, then the highest wild level
            best = max(catchable, key=lambda i: (depth_of[i], wild[i][v][0]))
            level, where = wild[best][v]
            picks.setdefault(str(best), {})[tag] = [level, where]
    return {'games': list(versions.values()), 'picks': picks}


result = {
    '_source': 'PokeAPI encounters, built by tools/build-best-catch.py. '
               'Per evolution line and game: the most evolved stage that appears in the wild '
               '(gifts excluded), its highest wild level and where. Ties: highest level wins.',
    'dexes': {dex: build(dex, versions) for dex, versions in GAMES.items()},
}
with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print({d: len(p['picks']) for d, p in result['dexes'].items()}, 'picks written to', OUT)
