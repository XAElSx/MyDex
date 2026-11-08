# Decisions

Choices made where the spec was unclear or conflicted with the existing app.

## Name change
- IndexedDB renamed `cta-dex` → `mydex`. On first start, records from the old database are copied once, newest `updated` wins (flag: localStorage `dbMigrated`). The old database is not deleted, so it stays as a backup.
- Kept as `cta-dex` on purpose: the gist file `cta-dex.json` and the `app` field in sync/export files. The existing gist and devices still on an older version look for these names. Import accepts both `cta-dex` and `mydex`.
- No localStorage key contained the old name, so none were renamed.

## Part A
- **Record shape kept.** Records stay `{ id: '<dex>:<speciesId>', state: 'none'|'caught'|'shiny', updated }` instead of `{ id, caught, shiny, origin, updatedAt }` keyed by species id. Per-dex marks, tombstones and Gist sync already depend on it; changing it would split data across devices. `state` covers caught + shiny (shiny implies caught). `origin` is added as an extra field (Part B1).
- **Tap / long press.** Tap toggles caught (a shiny card goes back to not caught). Long press (500 ms, touch and mouse) toggles shiny (shiny → caught). Moving the finger more than 10 px cancels the long press, so scrolling still works. The old tap cycle (caught → shiny → none) is replaced.
- **ES modules.** The constraints ask for `db.js`, `api.js`, `ui.js`, `app.js` as ES modules, so the classic scripts were converted. `sync.js` stays its own module. Behaviour of existing code is unchanged.
- **API cache.** PokéAPI responses are stored in IndexedDB store `api` (keyed by URL). The old localStorage `dex:<name>` lists are moved there once and removed. Preferences (`game`, `view`, `filter`, `boxes:*`, gist settings) stay in localStorage.
- **Existing, left alone:** dex selector (22 dexes, remembered), search by name or number, import with merge, lazy-loaded sprites.
- **Export** file is now `mydex-backup-YYYY-MM-DD.json` (local date); the time of the last export is stored in localStorage `lastExport`.

## Part B
- **B1 Origin.** Stored as `origin` on the existing per-dex record (a short game code such as `SV`, shown as the tag). Saving uses read-modify-write, so tapping a card keeps its origin and the other way round; it syncs like any other change. The tag stays when a card is un-caught (the origin is not deleted by accident). The sheet is a native `<dialog>`: a bottom sheet on phones, centred on wide screens. The "i" button is 44 px in List view, 28 px in Grid · 3, but only 15 px in the 6-column views (Grid · 6, Box): a cell there is about 50 px wide at 360 px, so a 44 px button would cover the sprite. Use List view for easier tapping. Game list is main-series games plus GO and "Other".
- **B2 Box view** already existed (boxes of 30, 6 columns, collapsible, per-box progress). Only added the "Box N" header; the number range stays next to it.
- **B3 Compact view** already exists as the view menu (List, Grid · 3, Grid · 6, Box), remembered in localStorage. Kept as a 4-way switch instead of 3-way: it already includes Grid, Box and List. Not changed.
- **B4 Missing only** already exists as the "Missing" tab (All / Caught / Missing / Shiny). Not changed.
- **B5 Version exclusives.** `data/exclusives.json` covers Red/Blue, X/Y, Sun/Moon, Sword/Shield and Scarlet/Violet (base games). JSON has no comments, so the source note is in a `"_source"` field. Lists are from Serebii's exclusives pages; Red/Blue are the international lists. Left out: species whose *form* differs per version (Tauros in SV, Basculin and Indeedee in SwSh) and Mega Evolutions, since marks are per species. Dex → pair: `kanto` → Red/Blue (the dropdown also covers Yellow/FRLG, whose exclusives differ), `kalos-*` → X/Y, `original-alola` → Sun/Moon, `galar` → Sword/Shield, `paldea` → Scarlet/Violet. DLC dexes and other games get no badges. If the file fails to load, cards simply show no badges.
- **B6 Display names.** `js/names.js` title-cases API names and has a map only for names that need more than that (hyphens kept, punctuation, ♀/♂, accents). Paradox Pokémon and Tapus need no map entry: "great-tusk" → "Great Tusk". Search ignores case, accents and punctuation and matches both the display name and the API name, so "flabebe", "mr mime" and "farfetchd" all work.
- **B7 Generation progress.** Shown only for the National dex, as a collapsible panel under the main progress bar (closed by default to save space on phones; open/closed is remembered in localStorage `gensOpen`). Generations are split by National Dex number: 151, 251, 386, 493, 649, 721, 809, 905, 1025.
- **B8 Completion %** already existed as the progress panel (count, bar, %, live). Only the text changed to "X / Y caught (Z%)" and the shiny count (★ N) is now always shown instead of only when above 0. Percent is rounded down, so 100% means complete.
- **B9 Backup reminder.** Shows when the last export is more than 14 days old, or when there has never been an export and at least 10 entries are caught (across all dexes). Closing it hides it for 7 days (localStorage `backupSnooze`). Only a file export counts as a backup; Gist sync does not, because the spec ties the reminder to exports.

## Best catch
- **What.** The "Best catch" tab shows, per evolution line, only the most evolved stage that appears in the wild in the game, with its highest wild level and place (badge "Lv 27"; place shown in list view). Ties on stage: highest level wins. Gifts and eggs are not wild and are ignored; lines with no wild member get no card in this tab.
- **Data.** Built once by `tools/build-best-catch.py` into `data/best-catch.json` instead of ~380 PokéAPI calls at runtime. Only members inside the dex are considered. Only `kanto` (FireRed/LeafGreen, tags FR/LG) for now: PokéAPI encounter data is patchy from Gen 6 on, so other games need checking before they are added to `GAMES` in the script. The tab is hidden in dexes without data.
- **Different per game.** If FR and LG pick differently, the badge carries the game tag ("FR Lv 46").

## UI
- The top bar keeps its existing layout: title, dex selector and the Sync menu (which holds export/import) on top; search and the view switch below; the Missing filter is a tab. Nothing was moved, so existing users find everything where it was.

## Not done / to check by hand
- Service worker and offline mode can't be tested in headless Chrome (CacheStorage fails there); check on a real device.
- Long press was tested with simulated pointer events; check it once on the Android phone.
- The "i" button is smaller than 44 px in the 6-column views (see B1).

## Living Dex
- **Gesture.** Double tap on touch screens, triple click with a mouse, toggles "in living dex". Every tap still toggles caught at once (no delay on single taps); when the taps add up to a double tap / triple click, the card goes back to how it was before the first tap and only the living mark changes. Taps must be under 350 ms apart.
- **Data.** Stored as `living: true` on the existing record, so it syncs and exports. Living implies caught: marking a missing Pokémon as living also marks it caught, and un-catching it (single tap) removes it from the living dex. Long press (shiny) keeps the living mark.
- **Look.** Living cards get a green border and check; a shiny living card keeps its gold border with a green inner ring.
- **Tab.** "Living Dex" shows only living cards. Filters now apply 400 ms after a tap, so a card doesn't vanish from the Missing/Caught tab between the taps of a double tap.
