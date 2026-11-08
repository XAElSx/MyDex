// HTML building blocks. No state and no events here: app.js owns those.
import { displayName, searchKey } from './names.js';

const SPRITE_BASE = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon';

const svg = d => `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${d}"/></svg>`;
export const ICONS = {
  list: svg('M3 5h4v3H3zm6 0h12v3H9zm-6 5.5h4v3H3zm6 0h12v3H9zM3 16h4v3H3zm6 0h12v3H9z'),
  grid3: svg('M3 3h5v5H3zm6.5 0h5v5h-5zM16 3h5v5h-5zM3 9.5h5v5H3zm6.5 0h5v5h-5zm6.5 0h5v5h-5zM3 16h5v5H3zm6.5 0h5v5h-5zm6.5 0h5v5h-5z'),
  grid6: svg('M3 4h2.5v2.5H3zm5.2 0h2.5v2.5H8.2zm5.1 0h2.5v2.5h-2.5zm5.2 0H21v2.5h-2.5zM3 10.75h2.5v2.5H3zm5.2 0h2.5v2.5H8.2zm5.1 0h2.5v2.5h-2.5zm5.2 0H21v2.5h-2.5zM3 17.5h2.5V20H3zm5.2 0h2.5V20H8.2zm5.1 0h2.5V20h-2.5zm5.2 0H21V20h-2.5z'),
  box: svg('M19 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V5a2 2 0 0 0-2-2zm0 12h-4a3 3 0 0 1-6 0H5V5h14z'),
  check: svg('M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z'),
  chevron: svg('M7.41 15.41 12 10.83l4.59 4.58L18 14l-6-6-6 6z')
};

export const VIEWS = {
  list: 'List',
  grid3: 'Grid · 3 columns',
  grid6: 'Grid · 6 columns',
  box: 'Box'
};

// Games a Pokémon can be caught in: [code stored in the record = tag on the card, label]
export const ORIGINS = [
  ['RBY', 'Red / Blue / Yellow'],
  ['GSC', 'Gold / Silver / Crystal'],
  ['RSE', 'Ruby / Sapphire / Emerald'],
  ['FRLG', 'FireRed / LeafGreen'],
  ['DPPt', 'Diamond / Pearl / Platinum'],
  ['HGSS', 'HeartGold / SoulSilver'],
  ['BW', 'Black / White'],
  ['B2W2', 'Black 2 / White 2'],
  ['XY', 'X / Y'],
  ['ORAS', 'Omega Ruby / Alpha Sapphire'],
  ['SM', 'Sun / Moon'],
  ['USUM', 'Ultra Sun / Ultra Moon'],
  ['LGPE', "Let's Go Pikachu / Eevee"],
  ['SwSh', 'Sword / Shield'],
  ['BDSP', 'Brilliant Diamond / Shining Pearl'],
  ['PLA', 'Legends: Arceus'],
  ['SV', 'Scarlet / Violet'],
  ['PLZA', 'Legends: Z-A'],
  ['GO', 'Pokémon GO'],
  ['Other', 'Other']
];

export const originTag = origin => (origin ? `<span class="origin-tag">${origin}</span>` : '');

export const spriteFor = (id, state) =>
  state === 'shiny' ? `${SPRITE_BASE}/shiny/${id}.png` : `${SPRITE_BASE}/${id}.png`;

// Small corner badge for a version-exclusive species
const versionBadge = v =>
  (v ? `<span class="version" style="--v:${v.color}" title="${v.name} exclusive">${v.tag}</span>` : '');

// Games with the same level and place are merged; a game tag is added when they differ
// or when the Pokémon is not catchable in every game of the dex.
function bestGroups(best) {
  const groups = new Map();
  for (const [tag, [level, place]] of Object.entries(best.found)) {
    const key = level + '|' + place;
    groups.set(key, { tags: [...(groups.get(key)?.tags || []), tag], level, place });
  }
  const list = [...groups.values()];
  const tagged = list.length > 1 || list[0].tags.length < best.games.length;
  return list.map(g => ({ ...g, prefix: tagged ? g.tags.join('/') + ' ' : '' }));
}

export const bestText = best =>
  bestGroups(best).map(g => `${g.prefix}Lv ${g.level}, ${g.place}`).join(' · ');

// "Lv 27" on the most evolved stage of a line that can be caught in the wild; the place is in the peek
function bestBadge(best) {
  if (!best) return '';
  const label = bestGroups(best).map(g => `${g.prefix}Lv ${g.level}`).join(' · ');
  return `<span class="best" title="Best wild catch">${label}</span>`;
}

export function cardHTML(p, pad, { state, origin, living }, version, best) {
  const name = displayName(p.name);
  // Search matches the display name and the API name ("nidoran f", "farfetchd")
  const keys = [...new Set([searchKey(name), searchKey(p.name)])].join('|');
  return `
    <div class="card ${state}${living ? ' living' : ''}" data-id="${p.id}" data-state="${state}" data-living="${living ? 1 : 0}"
         data-num="${p.num}" data-name="${keys}">
      <img src="${spriteFor(p.id, state)}" alt="${name}" loading="lazy" crossorigin="anonymous" draggable="false">
      <span class="num">#${String(p.num).padStart(pad, '0')}</span>
      <span class="name">${name}</span>
      ${versionBadge(version)}
      ${bestBadge(best)}
      ${originTag(origin)}
      <button class="info" aria-label="Details of ${name}">i</button>
    </div>`;
}

export function boxHTML(chunk, index, pad, closed, recordOf, versionOf, bestOf) {
  return `
    <section class="box${closed ? ' collapsed' : ''}" data-box="${index}">
      <button class="box-head" aria-expanded="${!closed}">
        <span class="box-label">Box ${index + 1}</span>
        <span class="box-range">${chunk[0].num}–${chunk[chunk.length - 1].num}</span>
        <span class="bar"><span class="bar-fill"></span></span>
        <span class="box-count"></span>
        <span class="chevron">${ICONS.chevron}</span>
      </button>
      <div class="box-grid">${chunk.map(p => cardHTML(p, pad, recordOf(p.id), versionOf(p.id), bestOf(p.id))).join('')}</div>
    </section>`;
}
