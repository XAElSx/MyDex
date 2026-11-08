"""Builds data/best-sets.json: a best ability, nature and moves per species.

Run from the project root:  python tools/build-best-sets.py
Uses the Smogon set of the dex's generation when one exists (via pkmn.github.io/smogon).
Species without one get a calculated set from PokeAPI, marked "calc".
"""
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor

API = 'https://pokeapi.co/api/v2/'
SETS = 'https://pkmn.github.io/smogon/data/sets/gen{}.json'
OUT = 'data/best-sets.json'

# dex name -> generation for abilities/sets, PokeAPI version group and its id
GAMES = {
    'kanto': {'gen': 3, 'group': 'firered-leafgreen', 'group_id': 7},
}

# Best Smogon format first; anything else comes after these
TIERS = ['ou', 'ubers', 'uu', 'ru', 'nu', 'pu', 'lc']
TIER_NAMES = {'ou': 'OU', 'ubers': 'Ubers', 'uu': 'UU', 'ru': 'RU', 'nu': 'NU', 'pu': 'PU', 'lc': 'LC'}

# Smogon names that are not just the capitalized PokeAPI name
SMOGON_NAMES = {'nidoran-f': 'Nidoran-F', 'nidoran-m': 'Nidoran-M', 'mr-mime': 'Mr. Mime', 'farfetchd': "Farfetch'd"}

# Smogon set names, lowercase. Only attacking sets are used: all-out attacker, then setup
SETUP_SETS = ('swords dance', 'dragon dance', 'calm mind', 'bulk up', 'belly drum', 'agility', 'curse',
              'nasty plot', 'growth', 'setup', 'sweeper')
ATTACK_SETS = ('offensive', 'attacker', 'wallbreaker', 'mixed', 'choice band')
NOT_ATTACKING = ('wall', 'stall', 'tank', 'support', 'cleric', 'heal bell', 'wish', 'spike', 'baton', 'trap',
                 'lead', 'utility', 'rest')

LEARN_METHODS = {'level-up', 'machine', 'tutor'}
PHYSICAL_TYPES = {'normal', 'fighting', 'flying', 'poison', 'ground', 'rock', 'bug', 'ghost', 'steel'}

# Strong on paper, but they cost a turn, knock out the user or only work in special cases
SKIP_MOVES = {
    'explosion', 'self-destruct', 'hyper-beam', 'blast-burn', 'hydro-cannon', 'frenzy-plant',
    'solar-beam', 'sky-attack', 'razor-wind', 'skull-bash', 'fly', 'dig', 'dive', 'bounce',
    'focus-punch', 'dream-eater', 'snore', 'future-sight', 'doom-desire', 'outrage', 'thrash',
    'petal-dance', 'overheat', 'psycho-boost', 'superpower',
}


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'mydex-data-build'})
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.load(res)


def get(path):
    return fetch(API + path)


def url_id(url):
    return int(url.rstrip('/').split('/')[-1])


def first(value):
    """Smogon lists options as arrays; the first is its main choice."""
    return value[0] if isinstance(value, list) else value


def offense_rank(name, chosen):
    """Lower is better: 0 all-out attacker, 1 offensive setup, 2 other attacker. None = not an attacking set."""
    n = name.lower()
    if 'defensive' in n:
        return None
    if 'offensive' not in n and any(w in n.replace('wallbreaker', '') for w in NOT_ATTACKING):
        return None
    if 'all-out' in n:
        return 0
    if any(w in n for w in SETUP_SETS):
        return 1
    if any(w in n for w in ATTACK_SETS):
        return 2
    # A name like "Standard" says nothing: go by where the EVs went
    evs = first(chosen.get('evs')) or {}
    return 3 if max(evs.get('atk', 0), evs.get('spa', 0)) >= 200 else None


def smogon_set(sets):
    """(label, set) of the best attacking set, best format first. None if there is no attacking set."""
    if not sets:
        return None
    for fmt in sorted(sets, key=lambda f: TIERS.index(f) if f in TIERS else len(TIERS)):
        ranked = [(offense_rank(name, chosen), i, name, chosen) for i, (name, chosen) in enumerate(sets[fmt].items())]
        ranked = [row for row in ranked if row[0] is not None]
        if ranked:
            _, _, name, chosen = min(ranked, key=lambda row: row[:2])
            return f'{TIER_NAMES.get(fmt, fmt.upper())} · {name}', chosen
    return None


def gen_abilities(pokemon, gen):
    """Regular abilities in this generation, by slot (hidden abilities came in Gen 5)."""
    slots = {a['slot']: a['ability']['name'] for a in pokemon['abilities'] if not a['is_hidden']}
    # past_abilities = what a slot held up to and including that generation
    past = sorted((p for p in pokemon.get('past_abilities', []) if url_id(p['generation']['url']) >= gen),
                  key=lambda p: url_id(p['generation']['url']))
    if past:
        for a in past[0]['abilities']:
            if a['is_hidden']:
                continue
            if a['ability']:
                slots[a['slot']] = a['ability']['name']
            else:
                slots.pop(a['slot'], None)
    return [slots[s] for s in sorted(slots)]


def move_at(move, group_id):
    """Power, accuracy and type as they were in this version group."""
    values = {f: move[f] for f in ('power', 'accuracy')}
    values['type'] = move['type']['name']
    # past_values = what a field was before that version group, oldest change first
    changes = sorted((p for p in move['past_values'] if url_id(p['version_group']['url']) > group_id),
                     key=lambda p: url_id(p['version_group']['url']), reverse=True)
    for change in changes:
        for field in ('power', 'accuracy'):
            if change[field] is not None:
                values[field] = change[field]
        if change['type']:
            values['type'] = change['type']['name']
    return values


def learnable(pokemon, group):
    return [m['move']['name'] for m in pokemon['moves']
            if any(d['version_group']['name'] == group and d['move_learn_method']['name'] in LEARN_METHODS
                   for d in m['version_group_details'])]


def english(entry):
    return next(n['name'] for n in entry['names'] if n['language']['name'] == 'en')


def calculated_set(pokemon, group, group_id, moves):
    """Strongest moves it can learn in the game (one per type), and a nature to match."""
    stats = {s['stat']['name']: s['base_stat'] for s in pokemon['stats']}
    types = {t['type']['name'] for t in pokemon['types']}
    gen3_split = group_id <= 7  # before Gen 4 the type decides physical or special

    scored, rest = [], []
    for name in learnable(pokemon, group):
        move = moves[name]
        at = move_at(move, group_id)
        if move['damage_class']['name'] == 'status' or not at['power'] or name in SKIP_MOVES:
            rest.append(name)
            continue
        physical = at['type'] in PHYSICAL_TYPES if gen3_split else move['damage_class']['name'] == 'physical'
        stat = stats['attack'] if physical else stats['special-attack']
        stab = 1.5 if at['type'] in types else 1
        score = at['power'] * (at['accuracy'] or 100) / 100 * stab * stat
        scored.append((score, name, at['type'], physical))
    scored.sort(reverse=True)

    picked, seen = [], set()
    for row in scored:
        if row[2] not in seen:  # coverage: one move per type first
            seen.add(row[2])
            picked.append(row[1])
    picked += [row[1] for row in scored if row[1] not in picked]
    picked += sorted(rest)

    physical = scored[0][3] if scored else stats['attack'] >= stats['special-attack']
    attack = stats['attack'] if physical else stats['special-attack']
    fast = stats['speed'] > attack
    nature = ('Jolly' if fast else 'Adamant') if physical else ('Timid' if fast else 'Modest')
    return [english(moves[m]) for m in picked[:4]], nature


def build(dex, game):
    gen, group, group_id = game['gen'], game['group'], game['group_id']
    sets = fetch(SETS.format(gen))
    entries = get('pokedex/' + dex)['pokemon_entries']
    species = [(url_id(e['pokemon_species']['url']), e['pokemon_species']['name']) for e in entries]

    with ThreadPoolExecutor(8) as pool:
        pokemon = dict(zip([i for i, _ in species], pool.map(lambda s: get(f'pokemon/{s[0]}'), species)))
        pending = {i: smogon_set(sets.get(SMOGON_NAMES.get(n, n.capitalize()))) for i, n in species}

        ability_slugs = {a for p in pokemon.values() for a in gen_abilities(p, gen)}
        abilities = dict(zip(ability_slugs, pool.map(lambda a: get('ability/' + a), ability_slugs)))

        move_slugs = {m for i, _ in species if not pending[i] for m in learnable(pokemon[i], group)}
        moves = dict(zip(move_slugs, pool.map(lambda m: get('move/' + m), move_slugs)))

    out, not_in_game = {}, 0
    for i, _ in species:
        options = [english(abilities[a]) for a in gen_abilities(pokemon[i], gen)
                   if url_id(abilities[a]['generation']['url']) <= gen]
        if pending[i]:
            label, chosen = pending[i]
            names = [first(m) for m in chosen['moves']]
            can_learn = set(learnable(pokemon[i], group))
            not_in_game += any(m.split(' ')[0].lower() != 'hidden' and
                               m.lower().replace(' ', '-').replace("'", '') not in can_learn for m in names)
            out[i] = {'source': 'smogon', 'label': label,
                      'ability': first(chosen.get('ability')) or (options[0] if options else None),
                      'nature': first(chosen.get('nature')), 'moves': names}
        else:
            names, nature = calculated_set(pokemon[i], group, group_id, moves)
            out[i] = {'source': 'calc', 'label': None,
                      'ability': options[0] if options else None, 'nature': nature, 'moves': names}
    smogon = sum(s['source'] == 'smogon' for s in out.values())
    print(f'{dex}: {smogon} Smogon, {len(out) - smogon} calculated, '
          f'{not_in_game} Smogon sets with a move not learnable in {group}')
    return out


result = {
    '_source': 'Smogon sets (pkmn.github.io/smogon) where available, otherwise calculated from PokeAPI '
               'by tools/build-best-sets.py. source: smogon or calc.',
    'dexes': {dex: build(dex, game) for dex, game in GAMES.items()},
}
with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
