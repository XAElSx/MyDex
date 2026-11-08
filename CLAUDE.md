# MyDex

Personal Pokédex tracker (formerly "CTA Dex"). Static web app (HTML/CSS/JS), later a PWA for Windows PC and Android.

## Stack
- Plain HTML, CSS, vanilla JS — no framework, no build step
- Data: PokéAPI (responses cached in IndexedDB), sprites from PokeAPI/sprites on GitHub
- Storage: IndexedDB via `js/db.js`. ES modules (`type="module"`), no globals
- Local server: `python -m http.server 8000`
- Live: https://xaelsx.github.io/MyDex/ (GitHub Pages, deploys from `main` / root on push). Keep all paths relative — the site lives under `/MyDex/`
- Shell: Windows PowerShell

## Files
- `index.html` — loads `js/app.js` as a module; it imports the rest
- `js/db.js` — all IndexedDB code: `status` store (marks) and `api` store (PokéAPI cache by URL)
- `js/api.js` — PokéAPI fetches, each URL fetched once then read from IndexedDB
- `js/ui.js` — HTML builders (cards, boxes, icons); no state
- `js/names.js` — display names (title case + special cases) and `searchKey` for search
- `js/sync.js` — Gist sync + export/import; merge per record, newer `updated` wins. Fires `dex-synced` when local data changed
- `js/app.js` — state, render, events. Tap = caught on/off, long press 500 ms = shiny on/off, double tap (touch) / triple click (mouse) = living dex on/off. The "i" button opens the center peek (`#peek`): marks, caught-in game, exclusive and best-catch info
- localStorage also holds `lastExport`, `backupSnooze` (backup banner), `gensOpen` (generation panel) and `versionFilter` (Exclusives subtab)
- View modes (`list`, `grid3`, `grid6`, `box`) saved in localStorage `view`; Box = groups of 30, collapsed boxes saved per game in `boxes:<game>`
- IndexedDB is `mydex`; the old `cta-dex` database is copied once on start and kept as a backup. Old name kept on purpose in the gist file `cta-dex.json` and the `app` field of sync/export files
- `DECISIONS.md` — choices made where the spec was unclear
- `data/exclusives.json` — version exclusives per dex (badges on cards)
- `data/best-catch.json` — per evolution line, the most evolved wild-catchable stage with its top level and place, per game ("Best catch" tab). Built by `python tools/build-best-catch.py` from PokéAPI; only `kanto` (FireRed/LeafGreen) so far
- `data/best-sets.json` — best ability, nature and moves per species (center peek): Smogon sets, or calculated when none exists. Built by `python tools/build-best-sets.py`; only `kanto` (Gen 3) so far
- `ref/` — design screenshots, git-ignored (not published)
- `css/style.css` — styling
- `sw.js` — service worker: app files network-first, sprites cache-first. Bump `SHELL_CACHE` when the file list changes
- `manifest.webmanifest`, `icons/` — PWA install data

## Card states
`none`, `caught`, `shiny` (tap toggles caught, long press toggles shiny). Shiny counts as caught. `none` is stored as a tombstone record (not deleted) so un-marking syncs too; `getDexRecords` hides it. Records may also hold `origin` (game code) and `living` (true = in the living dex; implies caught). Each record has an `updated` timestamp for sync.

Marks are per game. DB key is `<dex>:<speciesId>` (e.g. `national:25`, `paldea:25`), where `<dex>` is the PokéAPI pokedex name. DB v2 migrated v1 numeric ids to `national:<id>`.

## Roadmap
1. Setup ✅
2. Grid from PokéAPI ✅
3. Caught/shiny + IndexedDB ✅
4. Dex per game ✅
5. Filters + search + progress counter ✅
6. PWA ✅
7. Deploy to GitHub Pages ✅
8. Sync between devices ✅

## How to work with me
- Do all steps of a task at once; no need to wait for **y** between steps.
- Explain what each extra part does and why the step is needed (short tables are fine).
- Keep text minimal and structured.
- Ask before running git commit or push.
