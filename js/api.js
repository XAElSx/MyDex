// PokéAPI access. Every response is cached in IndexedDB, so each URL is fetched once.
import { cacheGet, cachePut } from './db.js';

const API = 'https://pokeapi.co/api/v2/';

async function getJSON(path) {
  const url = API + path;
  const cached = await cacheGet(url);
  if (cached) return cached;

  let res;
  try {
    res = await fetch(url);
  } catch {
    throw new Error('Could not reach PokéAPI. Check your connection.');
  }
  if (!res.ok) throw new Error(`PokéAPI answered with error ${res.status}.`);
  const data = await res.json();
  await cachePut(url, data);
  return data;
}

// Entries of one pokedex, in that dex's order and numbering.
export async function loadDex(name) {
  const data = await getJSON('pokedex/' + name);
  return data.pokemon_entries.map(e => ({
    num: e.entry_number,
    id: Number(e.pokemon_species.url.split('/').filter(Boolean).pop()),
    name: e.pokemon_species.name
  }));
}

// Version exclusives for one dex: Map speciesId -> { name, tag, color }.
// Empty when the dex has none, or when the file can't be loaded (badges are optional).
let exclusives;
export async function loadExclusives(dex) {
  exclusives ??= fetch('data/exclusives.json')
    .then(res => (res.ok ? res.json() : { pairs: [] }))
    .catch(() => ({ pairs: [] }));
  const { pairs } = await exclusives;
  const map = new Map();
  pairs.filter(p => p.dexes.includes(dex)).forEach(p =>
    p.versions.forEach(({ name, tag, color, ids }) =>
      ids.forEach(id => map.set(id, { name, tag, color }))));
  return map;
}

// Best wild catch per evolution line for one dex: Map speciesId -> { games, found },
// found = { FR: [level, place], ... }. Empty when the dex has no data (the tab is hidden then).
let bestCatch;
export async function loadBestCatch(dex) {
  bestCatch ??= fetch('data/best-catch.json')
    .then(res => (res.ok ? res.json() : { dexes: {} }))
    .catch(() => ({ dexes: {} }));
  const { games = [], picks = {} } = (await bestCatch).dexes[dex] || {};
  return new Map(Object.entries(picks).map(([id, found]) => [Number(id), { games, found }]));
}

// Older versions cached dex lists in localStorage as dex:<name>. Move them over once.
export async function moveLocalCache() {
  localStorage.removeItem('species'); // step-2 cache, no longer used
  const keys = Object.keys(localStorage).filter(k => k.startsWith('dex:'));
  for (const key of keys) {
    try {
      const list = JSON.parse(localStorage.getItem(key));
      const entries = list.map(p => ({
        entry_number: p.num,
        pokemon_species: { name: p.name, url: `${API}pokemon-species/${p.id}/` }
      }));
      await cachePut(API + 'pokedex/' + key.slice(4), { pokemon_entries: entries });
    } catch { /* broken entry: it will simply be fetched again */ }
    localStorage.removeItem(key);
  }
}
