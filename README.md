# MyDex
Personal Pokédex tracker for myself. Works in the browser on Windows and Android, and can be installed as an app (PWA).

Live: https://xaelsx.github.io/MyDex/

## Features
- **Dex per game**: National plus regional dexes (Kanto through Paldea and the DLC dexes), in that dex's order and numbering. Marks are kept per dex.
- **Mark Pokémon**: tap a card for caught (✓); hold it for half a second for shiny (★). Uncaught cards are dimmed.
- **Living Dex**: double tap a card (triple click on PC) to mark it as part of your living dex (green). The *Living Dex* tab shows only those.
- **Origin**: the small "i" button on a card sets the game it was caught in; the game shows as a tag on the card.
- **Version exclusives**: in FireRed/LeafGreen, X/Y, Sun/Moon, Sword/Shield and Scarlet/Violet dexes, exclusive Pokémon get a version badge.
- **Views**: List, Grid · 3 columns, Grid · 6 columns, and Box (boxes of 30, like Pokémon HOME). Collapsed boxes are remembered.
- **Search** by name or number, with proper names (Mr. Mime, Type: Null, Flabébé…). Accents and punctuation don't matter.
- **Filters**: All, Caught, Missing, Shiny, Living Dex.
- **Progress**: "X / Y caught (Z%)" plus a shiny count for the selected dex; in the National dex also a bar per generation.
- **Backup**: export to `mydex-backup-YYYY-MM-DD.json` and import (merges, newest change wins). A banner reminds you when the last export is over 14 days old.
- **Sync between devices** through a private GitHub Gist.
- **Offline**: after the first visit the app and viewed sprites work without internet.

## Usage
- **Install**: open the live link in Chrome or Edge → menu → *Install app* / *Add to Home screen*.
- **Sync**: create a GitHub token with only the `gist` scope, open *Sync* in the app, paste it and press *Connect*. Do this on each device.
- **Backup**: *Sync* → *Export file*. To restore, *Import file*.

## Run locally
```
python -m http.server 8000
```
Then open http://localhost:8000.

## Tech
Plain HTML, CSS and JavaScript (ES modules), no build step. Data from [PokéAPI](https://pokeapi.co), sprites from [PokeAPI/sprites](https://github.com/PokeAPI/sprites). Marks and API responses are stored in IndexedDB. See `DECISIONS.md` for design choices.
