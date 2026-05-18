# EHORO VILLAGE — Living Technical Manifesto

> **This is a living document.** Every AI session that works on Ehoro Village should read this first and append their changes at the bottom in the Session Log. The owner (Ube / Super Ube LLC) carries this document + the current `index.html` into each new chat.

**Owner:** Super Ube LLC (ubseoul) — Ube, "Purple Prince"
**Supabase URL:** `https://eyqddqtlgthgkiqjavyx.supabase.co`
**Supabase Anon Key:** `sb_publishable_CsTLSJj1YwgiHMxUTa685Q_2TVvZa2Q`
**Hosting:** GitHub Pages at `ubseoul.github.io/ehoro_village_music/`
**Current Version:** V3.3 (as of May 16, 2026)

---

## RULES FOR AI ASSISTANTS

**Read these before writing any code.**

1. **Vanilla JS only.** No frameworks, no build tools, no npm. The entire app is one HTML file. Keep it that way.
2. **Do not refactor CSS.** Add new styles at the end. The existing CSS has been carefully built up over many sessions. Appending is safe. Rewriting is not.
3. **Companion, not game.** Do not add mechanics that demand active attention. The product rewards passive presence.
4. **Single file deployment.** `index.html` + `sprites/` folder + Supabase. No server, no build step.
5. **Test against actual DB schema.** ALWAYS verify column names before writing SQL. The schema has been patched many times. The `eggs` table has NO `created_at` column. The `hatchery` table has NO `created_at` column. The `expeditions` table has NO `created_at` column — use `id` for ordering.
6. **RPC over direct mutations.** All game state changes go through `SECURITY DEFINER` RPCs. The frontend has fallback direct inserts in `ensureStarterPack` only — everywhere else, use RPCs.
7. **Don't swallow errors.** Always `console.warn` on catch. Never empty catch blocks.
8. **Check actual data state, not profile flags.** The `starter_claimed`, `newbie_gift_claimed` flags are unreliable. Always check if spirits/emblems actually exist.
9. **When you finish your session**, append a dated entry to Section 12 (Session Log) documenting what you changed, what SQL you ran, what's still broken, and any new state fields.
10. **Dark theme is primary.** Light theme is warm parchment. Avoid saturated colors. Everything should feel like a cozy study room at night.
11. **Versioning standard.** Version numbers follow the format `X.Y`. Each update increments `Y` by 1 (e.g. 1.0 → 1.1 → 1.2). When `Y` reaches 9, the next update rolls over to `(X+1).0` (e.g. 1.9 → 2.0). The current version is always noted at the top of this document. Update it when shipping changes.
12. **Document naming.** This manifesto file should be named `EHORO_MANIFESTO_X.Y.md` matching the current version. When you ship changes, rename/save the manifesto with the new version number.
13. **Always DROP old function overloads before recreating RPCs.** If a function signature changes, the old signature stays in the DB as a separate overload. PostgREST 400s when it can't resolve ambiguity. Always `DROP FUNCTION IF EXISTS` all known signatures explicitly.
14. **localStorage keys for V2.9+ client state.** Building tiers, library research state, village last-seen timestamp, and first expedition tracking are all localStorage-only (no DB columns). Keys always include `S.user.id` to be user-scoped. See Section 8 for full key list.
15. **CSS fixes go at the bottom as a patch block.** From V3.0 onward, targeted UX/CSS fixes are appended as a clearly labeled patch comment block at the end of the `<style>` tag. Use `!important` sparingly and only when overriding legacy rules by class name. Do not touch existing CSS rules — append only.
16. **When asked to redesign visually, propose first — do not build.** Session 21 established that full CSS rewrites can break the product's established feel. Always present a written proposal and get approval before touching the style block structurally. Exception: targeted bug fixes (wrong color, wrong size, wrong layout) can be applied directly.

---

## 1. PRODUCT OVERVIEW

Ehoro Village is a lo-fi music streaming web app with a spirit collection game layer. Users listen to lo-fi streams, passively earn eggs and ingredients, hatch spirits, evolve them, and grow their village. It is designed as a **companion app** — it rewards presence, not attention.

**Stack:** Single HTML file + 19 PNG sprite files + Supabase backend (PostgreSQL + Auth + RPC)
**Auth:** Supabase email/password + Google OAuth + guest mode
**Target:** 17–20 year old college students, first 100 users
**Lo-Fi Stream:** Ehoro Village Radio — own 1hr lofi video (`ojyT8dK0ZiA`), looping.

---

## 2. THE `S` OBJECT — SINGLE SOURCE OF TRUTH

All client-side state lives in a single global object `S`. Every render function reads from `S`. Every RPC callback writes to `S` then calls `updateAllUI()`.

```javascript
let S = {
  // Auth
  user: null,
  isGuest: true,
  authMode: 'login',

  // Profile (from profiles table)
  profile: null,

  // Game data
  spirits: [],             // { id, user_id, spirit_type, name, evo_stage, xp, cultivation_stage }
  traits: {},              // Map: spirit_id -> [{ trait_name, trait_type, trait_category }]
  emblems: { cafe_bean: 0, wild_essence: 0, focus_shard: 0, ashe_essence: 0, spirit_essence: 0 },
  hatchery: [],            // { id, user_id, slot_number, unlocked, egg_id, started_at, hatch_duration_minutes }
  pendingEggs: [],
  allEggs: [],
  pillRecipes: [],
  expeditions: [],         // { id, user_id, slot_number, spirit_ids, duration_minutes, started_at, rest_until, location }
  _wickedPills: [],
  buildings: [],           // { id, user_id, building_type, is_unlocked, last_produced_at, research_data }
  buildingStaff: [],       // { id, user_id, building_type, spirit_id, role }
  buildingInventory: [],   // { id, user_id, item_type, item_id, item_name, quantity, xp_bonus, buff_type, buff_value, buff_expires_at, expires_at }
  materials: {},           // Map: item_id -> count (derived from buildingInventory)
  journal: {},             // Map: spirit_id -> [{ event_type, description, created_at }]

  // Streaming
  playing: false,
  currentStream: 'sakura',
  sessionId: null,
  sessionStartedAt: null,
  eggT: 0,
  eggAnchor: null,
  EGG_SEC: 3600,
  FIRST_EGG_SEC: 240,
  GUEST_EGG_SEC: 30,
  XP_PER_LEVEL: 150,
  XP_ACTIVE_INTERVAL: 300,

  // Listen time accumulation (for Àṣẹ tick)
  asheListenAccum: 0,
  asheListenTimer: 0,

  // Interval handles
  ticker: null,
  hatchTicker: null,
  cultTicker: null,        // Fires every 5min while playing
  jiggleTicker: null,
  expedTicker: null,       // Fires every 500ms when expeditions are active

  // UI
  theme: 'dark',
  obStep: 0,
  settingsOpen: false,
  selectedSpirit: null,
  firstIngredientGiven: false,
  craftHintShown: false,
  wbTimer: null,
  profStep: 0,
  chosenStarter: null,
  isGuest: true,
  guestEggGiven: false,
};
```

### Data flow pattern
1. User action → call Supabase RPC
2. RPC returns → `await loadUserData()` (re-fetches ALL tables)
3. `updateAllUI()` re-renders spirits, items, village tabs

---

## 3. DATABASE SCHEMA

**CRITICAL:** The schema has mixed provenance from multiple sprint iterations. Several `ALTER TABLE` and `DROP CONSTRAINT` patches have been applied. Always verify against the live DB before assuming column names.

### profiles
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | References auth.users(id) |
| username | TEXT | |
| created_at | TIMESTAMPTZ | |
| total_eggs | INT | Lifetime egg count |
| total_listen_seconds | INT | |
| total_listen_minutes | INT | Added V2.7 — for cultivation listen gates |
| last_egg_drop_at | TIMESTAMPTZ | Rate limiting for claim_egg_drop |
| newbie_gift_claimed | BOOLEAN | |
| onboarding_done | BOOLEAN | |
| last_seen | TIMESTAMPTZ | |
| last_seen_at | TIMESTAMPTZ | Added V2.7 — used by claim_passive_cultivation |
| first_egg_claimed | BOOLEAN | |
| starter_claimed | BOOLEAN | |
| streak_days | INT | |
| streak_last_date | DATE | |
| pills_crafted | INT | Achievement counter |
| expeds_completed | INT | Achievement counter |
| milestones_shown | JSONB | |
| last_rpc_at | TIMESTAMPTZ | Rate limiting |
| first_exped_night_market | BOOLEAN DEFAULT FALSE | Added V3.2. Replaces localStorage. |
| first_exped_bamboo_highlands | BOOLEAN DEFAULT FALSE | Added V3.2. Replaces localStorage. |
| first_exped_frozen_ruins | BOOLEAN DEFAULT FALSE | Added V3.2. Replaces localStorage. |

### spirits
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK | |
| spirit_type | TEXT | One of 6 types |
| name | TEXT | User-given name |
| xp | INT | Cumulative XP |
| evo_stage | INT | 0=Seedling, 1=Awakened, 2=Ascended |
| cultivation_stage | INT | 0–5; still in DB but UI removed in V2.8 |
| alignment | TEXT | 'neutral', 'wicked', 'heavenly' |
| bio | TEXT | Optional flavor bio |

### spirit_traits
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| spirit_id | UUID FK | |
| user_id | UUID FK | |
| trait_name | TEXT | |
| trait_type | TEXT | |
| trait_category | TEXT | 'expedition', 'growth', 'affinity' |
| slot_index | INT | Which trait slot (0, 1, 2) |

### eggs
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK | |
| rarity | TEXT | 'mundane', 'uncommon', 'rare', 'illustrious' |
| playlist | TEXT | |
| status | TEXT | 'pending', 'incubating', 'hatched' |
| **⚠️ NO created_at column** | | |

### hatchery
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK | |
| slot_number | INT | 1–5 |
| unlocked | BOOLEAN | |
| egg_id | UUID FK NULLABLE | |
| started_at | TIMESTAMPTZ NULLABLE | |
| hatch_duration_minutes | INT | |
| **⚠️ NO created_at column** | | |

### expeditions
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK | |
| slot_number | INT | |
| spirit_ids | UUID[] | |
| duration_minutes | INT | |
| duration_type | TEXT | 'short', 'medium', 'long' |
| started_at | TIMESTAMPTZ | |
| completed_at | TIMESTAMPTZ | When expedition ends |
| rest_until | TIMESTAMPTZ | When rest period ends |
| location | TEXT | 'night_market', 'bamboo_highlands', 'frozen_ruins' |
| **⚠️ NO created_at column** | | Use `id` for ordering |
| UNIQUE (user_id, slot_number) | | Required for send_expedition upsert |

### buildings
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK | |
| building_type | TEXT | 'cafe', 'dojo', 'library', 'garden', 'studio' |
| is_unlocked | BOOLEAN | |
| last_produced_at | TIMESTAMPTZ | Added V2.7 |
| research_data | TEXT DEFAULT '[]' | Added V2.7; V3.2: now actively used by client to store library research JSON (cross-device) |
| tier | INT DEFAULT 1 | Added V3.2. Replaces localStorage. 1–3. |

### building_staff
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK | |
| building_type | TEXT | |
| spirit_id | UUID FK | |
| role | TEXT | 'manager' or 'worker' |

### building_inventory
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK | |
| item_type | TEXT NOT NULL DEFAULT 'material' | 'material' or 'drink' |
| item_id | TEXT | e.g. 'grinder_stone', 'house_brew' |
| item_name | TEXT | Display label |
| quantity | INT DEFAULT 1 | |
| xp_bonus | INT DEFAULT 0 | For drinks |
| buff_type | TEXT | For drinks |
| buff_value | NUMERIC | For drinks |
| buff_expires_at | TIMESTAMPTZ | For drinks |
| expires_at | TIMESTAMPTZ | Drink expiry (48hrs) |

### emblems
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK | |
| emblem_type | TEXT | 'cafe_bean', 'wild_essence', 'focus_shard', 'ashe_essence', 'spirit_essence' |
| quantity | INT | |
| UNIQUE (user_id, emblem_type) | | Required for upsert |

### spirit_journal
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| spirit_id | UUID FK | |
| user_id | UUID FK | |
| event_type | TEXT DEFAULT 'note' | 'evolution', 'expedition', 'hatch', 'note', 'cultivation' |
| description | TEXT | |
| created_at | TIMESTAMPTZ | Journal entries DO have created_at |

### wicked_pills
| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| user_id | UUID FK | |
| pill_name | TEXT | |
| xp_value | INT | |
| created_at | TIMESTAMPTZ | |

### pill_recipes (read-only reference table)
| Column | Type |
|--------|------|
| id | UUID PK |
| name | TEXT |
| cost_cafe_bean | INT |
| cost_wild_essence | INT |
| cost_focus_shard | INT |
| effect_type | TEXT |
| effect_value | INT |
| rarity | TEXT |

---

## 4. SPIRIT SYSTEM

### Spirit types (6)
`koa`, `luna`, `mochi`, `remy`, `sable`, `yuki`

### Evolution stages
| Stage | Label | Trait Slots | Sprite suffix |
|-------|-------|-------------|---------------|
| 0 | Seedling | 1 | `_seedling.png` |
| 1 | Awakened | 2 | `_awakened.png` |
| 2 | Ascended | 3 | `_ascended.png` |

**Evolution cost:** 30× each ingredient (cafe_bean, wild_essence, focus_shard) + minimum level (Lv.5 for Awakened, Lv.10 for Ascended).

**Cultivation stage:** Still in DB (0–5), dead in UI as of V2.8. Do not re-expose without owner approval.

### Trait system (V2.6+)
Traits are passive buffs. A spirit can have 1 trait at Seedling, 2 at Awakened, 3 at Ascended. Traits are assigned by the `evolve_spirit` RPC on evolution.

**Categories:** expedition 🧭, growth 🌱, affinity ✦

**Full trait list:**
| Name | Category | Effect | Display |
|------|----------|--------|---------|
| Highlands Reader | expedition | +20% loot from highland expeditions | +20% highland loot |
| Market Sharp | expedition | +15% ingredient find rate | +15% ingredient drops |
| Frost-Hardened | expedition | Unlocks Frozen Ruins early | Frozen Ruins access |
| Wanderer | expedition | +10% loot all locations | +10% loot bonus |
| Lucky | expedition | +5% rare drop chance | +5% rare chance |
| Resilient | expedition | -15% rest time | -15% rest time |
| Instinctive | expedition | First expedition each day free | Free daily expedition |
| Patient | growth | -10% cultivation cost | -10% Àṣẹ cost |
| Studious | growth | +5% pill XP bonus | +5% pill XP |
| Deep Roots | growth | -10% cult cost reduction | -10% Àṣẹ cost |
| Focused | growth | Bonus XP while music plays | +10% active XP |
| Gentle | growth | Egg hatch time -5% | -5% hatch time |
| Archivist | affinity | +25% library research speed | +25% research speed |
| Disciplined | affinity | Dojo XP ×2 when manager | ×2 Dojo XP (manager) |
| Instinctive | affinity | Passive XP rate +5% | +5% passive XP |

---

## 5. EXPEDITION SYSTEM

### Locations
| ID | Label | Min Level | Min Evo | Durations |
|----|-------|-----------|---------|-----------|
| night_market | Night Market 🏮 | 1 | 0 (Seedling) | Short, Medium |
| bamboo_highlands | Bamboo Highlands 🎋 | 2 | 1 (Awakened) | Medium, Long |
| frozen_ruins | Frozen Ruins 🧊 | 4 | 2 (Ascended) | Long only |

### Durations
| Key | Duration | Rest | Base Mats | Bonus XP | Àṣẹ Chance |
|-----|----------|------|-----------|----------|------------|
| short | 10min | 3min | 2–4 | 8 | 1% |
| medium | 20min | 15min | 4–8 | 10 | 4% |
| long | 45min | 25min | 8–14 | 25 | 10% |

### Loot multiplier by spirit count
| Spirits | Multiplier |
|---------|-----------|
| 1 | 1× (base) |
| 2 | +40% |
| 3 | +90% |

### First-expedition guaranteed drops (localStorage-tracked)
- Night Market first visit → canvas_roll 🎨
- Bamboo Highlands first visit → grinder_stone 🪨
- Frozen Ruins first visit → ruin_fragment 🏚️

### Library research integration (V2.9)
When a location is researched (via Library building), its full loot table appears inline in the expedition location selector. Research state is tracked in localStorage (not `buildings.research_data` in DB — that column exists but is unused by client).

---

## 6. BUILDING SYSTEM

### Buildings
| ID | Label | Unlock Cost | Manager Role | Worker Role | Passive Buff |
|----|-------|-------------|--------------|-------------|--------------|
| cafe | The Café ☕ | 30× cafe_bean + 1× grinder_stone | Head Barista | Barista (×2) | +5% village XP |
| dojo | The Dojo ⚔️ | 25× ashe_essence + 1× training_scroll | Sensei | Trainee (×2) | -10% rest time |
| library | Village Library 📚 | 40× ashe_essence + 1× ancient_tome | Head Archivist | Researcher (×2) | +10% passive XP |
| garden | The Garden 🌿 | 25× wild_essence + 1× highland_orchid | Head Gardener | Farmer (×2) | +15% ingredient drops |
| studio | The Studio 🎨 | 20× spirit_essence + 1× canvas_roll | Lead Artist | Artist (×2) | +10% listen XP |

**Café starts unlocked for all users.** `ensureStarterPack()` auto-inserts the Café building row on first login.

### Building tiers (V2.9)
Tiers are tracked **client-side in localStorage** using keys `bldg_tier_{buildingId}_{userId}`. No DB column exists for tier.

| Building | Tier 1 | Tier 2 (upgrade cost) | Tier 3 (upgrade cost) |
|----------|--------|----------------------|----------------------|
| Café | House Brew only | +Village Blend & Reserve Roast (20× cafe_bean, 10× wild_essence) | +Grand Cru & Signature Reserve (2× grinder_stone, 15× focus_shard) |
| Dojo | +5 XP/tick | +10 XP/tick (2× training_scroll, 12× focus_shard) | +15 XP/tick + trait scroll chance (3× training_scroll, 15× ashe_essence) |
| Library | 60min research, loot table | 45min research, drop rates shown (2× ancient_tome, 15× wild_essence) | 30min research, all rates + rare bonus (3× ancient_tome, 20× ashe_essence) |
| Garden | 3–5 ingredients/cycle | 5–8 + rare mat chance (2× highland_orchid, 20× wild_essence) | 8–12 + guaranteed rare mat (3× highland_orchid, 20× focus_shard) |
| Studio | 1 village_record/cycle | 2 records + canvas chance (2× canvas_roll, 10× spirit_essence) | 3 records + guaranteed canvas (3× canvas_roll, 20× wild_essence) |

### Production schedule (server-side, `check_building_production` RPC)
- Café: drink every 4hrs if manager staffed
- Garden: ingredients every 20hrs
- Studio: village_record every 20hrs

`checkBuildingProduction()` fires **every 4 hours** via client-side `setInterval` and on login.

### Library research (V2.9 client-only)
- State stored in `localStorage` under key `lib_research_{userId}` as JSON: `{ [locId]: { status: 'idle'|'researching'|'done', startedListenMin: N, durationMin: N } }`
- Progress gated by listen time (`profiles.total_listen_minutes`)
- Only one location can be actively researched at a time
- Duration: 60min (Tier 1), 45min (Tier 2), 30min (Tier 3)
- Requires Head Archivist to be assigned to start research

---

## 7. RPCs (complete list, as of V2.7 + hotfixes)

All RPCs are `SECURITY DEFINER`, owned by `postgres`, granted to `authenticated` and `anon`.

| RPC | Description |
|-----|-------------|
| `evolve_spirit(p_spirit_id)` | Checks level+cost, deducts ingredients, updates evo_stage, assigns trait |
| `hatch_egg(p_slot_id)` | Hatches egg in slot, creates spirit, updates hatchery |
| `craft_pill(p_recipe_id, p_spirit_id)` | Deducts ingredients, applies XP, may create wicked pill |
| `use_wicked_pill(p_pill_id, p_spirit_id)` | Applies XP, sets alignment=wicked, deletes pill |
| `craft_heavenly_pill(p_recipe_id, p_spirit_id)` | Creates heavenly pill item, applies XP, sets alignment=heavenly |
| `claim_egg_drop(p_playlist, p_streak_bonus)` | Creates egg, rate-limited via last_egg_drop_at (30min), streak bonus server-side |
| `tick_active_cultivation()` | 5min listen tick XP to all spirits. Applies Café (+5%) and Library (+10% if staffed) buffs |
| `claim_passive_cultivation()` | Login gift XP based on hours_away (max 72hrs). Uses last_seen_at |
| `grant_village_gift(p_hours_away)` | Welcome-back ingredient gift. Formula: `LEAST(8, GREATEST(1, floor(hours/3)))` multiplier |
| `convert_ingredient(p_from, p_to, p_amount)` | 2:1 ratio conversion between ingredients |
| `send_expedition(p_slot, p_spirit_ids, p_duration, p_location)` | Upserts expedition row. Requires UNIQUE(user_id, slot_number) constraint |
| `claim_expedition(p_expedition_id)` | Returns loot_items[] JSONB array. Location-aware loot tables. Dojo -10% rest. Àṣẹ chances per location. V3.2: reads spirit traits + alignment for all bonuses. |
| `unlock_building(p_building_type)` | Validates + deducts materials, creates building row |
| `upgrade_building(p_building_type)` | Sets buildings.tier +1. Added V3.2. |
| `assign_building_staff(p_building_type, p_spirit_id, p_role)` | Assigns spirit to building role |
| `unassign_building_staff(p_staff_id)` | Removes staff row |
| `use_drink(p_inv_id, p_spirit_id)` | Applies drink XP bonus to spirit, deletes inventory row, writes journal |
| `check_building_production()` | Runs production for Café, Garden, Studio. V3.2: reads buildings.tier for output amounts. |
| `advance_cultivation(p_spirit_id)` | (Dead UI as of V2.8 but RPC still exists) |
| `dismiss_spirit(p_spirit_id)` | Dissolves spirit into spirit_essence |
| `jar_spirit(p_spirit_id)` | Dissolves wicked spirit into wicked pill |
| `set_first_expedition_flag(p_location)` | Idempotent. Sets profiles.first_exped_{location}=TRUE. Added V3.2. |

---

## 8. CLIENT-SIDE LOCALSTORAGE KEYS

All keys are user-scoped. Always append `_{userId}` to prevent cross-user pollution.

**V3.2 note:** Building tier, library research, and first expedition flags have all been moved to the DB. The remaining localStorage keys are UI-only state (safe to lose on device change).

| Key Pattern | Purpose | Format |
|-------------|---------|--------|
| `starter_pack_done_{userId}` | One-time flag: starter pack given | `'1'` |
| `village_last_seen_{userId}` | Timestamp of last village tab visit (UI only — cosmetic notif dot) | Unix timestamp string |
| `gift_toast_shown_{userId}` | One-time gift toast suppressor | `'1'` |

**Moved to DB (V3.2):**
| Old Key | Now lives in |
|---------|-------------|
| `bldg_tier_{buildingId}_{userId}` | `buildings.tier` column |
| `lib_research_{userId}` | `buildings.research_data` column (JSON) |
| `firstExped_{locId}_{userId}` | `profiles.first_exped_{location}` columns |

---

## 9. KNOWN DEAD CODE (harmless, do not remove)

- `openCultivateModal(spiritId)` — cultivation advance modal
- `doCultivate(spiritId)` — calls `advance_cultivation` RPC
- `CULT_STAGES`, `CULT_COSTS`, `CULT_LVL_REQ` — cultivation config arrays
- `CULT_LISTEN_REQ` — listen gate per cultivation stage
- `spirits.cultivation_stage` — loaded from DB, set to 0 if null, never displayed

The `cultivation_stage` column still exists in the DB and is loaded into `S.spirits`. Do not remove it.

---

## 10. MATERIALS REFERENCE

| ID | Emoji | Label | Primary Source |
|----|-------|-------|----------------|
| cafe_bean | ☕ | Café Bean | Passive drops |
| wild_essence | 🌿 | Wild Essence | Passive drops |
| focus_shard | ⚡ | Focus Shard | Passive drops (rare) |
| ashe_essence | 🔮 | Àṣẹ Essence | Expedition drops |
| spirit_essence | ✨ | Spirit Essence | Dismiss/jar spirit |
| grinder_stone | 🪨 | Grinder Stone | Night Market (first drop), expeditions |
| ancient_tome | 📖 | Ancient Tome | Bamboo Highlands |
| training_scroll | 📜 | Training Scroll | Bamboo Highlands, Frozen Ruins |
| highland_orchid | 🌸 | Highland Orchid | Bamboo Highlands (rare) |
| canvas_roll | 🎨 | Canvas Roll | Night Market (first drop), expeditions |
| ruin_fragment | 🏚️ | Ruin Fragment | Frozen Ruins (first drop), expeditions |
| wardens_crest | 👁️ | Warden's Crest | Frozen Ruins (rare) |
| village_record | 🎵 | Village Record | Studio production |

---

## 11. SPRITE FILES

All in `/sprites/` folder. Format: `{type}_{stage}.png`

| Spirit | Seedling | Awakened | Ascended |
|--------|----------|----------|----------|
| koa | koa_seedling.png | koa_awakened.png | koa_ascended.png |
| luna | luna_seedling.png | luna_awakened.png | luna_ascended.png |
| mochi | mochi_seedling.png | mochi_awakened.png | mochi_ascended.png |
| remy | remy_seedling.png | remy_awakened.png | remy_ascended.png |
| sable | sable_seedling.png | sable_awakened.png | sable_ascended.png |
| yuki | yuki_seedling.png | yuki_awakened.png | yuki_ascended.png |

Plus: `egg_mundane.png`, `egg_uncommon.png`, `egg_rare.png`, `egg_illustrious.png`

---

## 12. SESSION LOG

### Sessions 1–14 (Pre-manifesto)
Core game loop established. Supabase auth, spirit hatching, cultivation, ingredient drops, pill crafting, village system skeleton. Exact dates and details not captured.

---

### Session 15 — February 18, 2026 — Claude Sonnet 4.6
**V2.6: Client Patch Sprint — 18 fixes, full trait system, expedition locations, building UI**

Major client-side overhaul. No SQL shipped in this session.

**Key changes:**
- Trait system: 15+ traits fully defined with slot system (1/2/3 by evo stage). Three categories: expedition, growth, affinity.
- Journal system: event log per spirit (evolution, expedition, hatch). Rendered in spirit detail.
- Village buildings grid: 2×N tile layout with staff pips, emoji, badges.
- Expedition locations (3): Night Market, Bamboo Highlands, Frozen Ruins — each with different loot tables, level gates, duration restrictions.
- Expedition loot reveal: animated full-screen overlay showing what spirits brought back.
- Spirit detail overlay: XP bar, trait display, alignment badge, journal feed, evolve button.
- Streak system: daily login streak counter, streak bonus ingredients.
- Welcome-back cultivation: passive XP granted on return based on hours away.
- Multiple economy tuning passes.

**Deferred to V2.7:** Full backend RPC layer.

---

### Session 16 — February 18, 2026 — Claude Sonnet 4.6
**V2.7 Pre-build Audit — Economy + Schema Audit Document**

Delivered `EHORO_V26_PATCH_AUDIT.docx` — professional audit with economy math, schema gaps, sprint roadmap. No code changes in this session.

---

### Session 17 — February 18, 2026 — Claude Sonnet 4.6
**V2.7: Backend Patch — All RPCs Written**

Delivered `ehoro_v26_backend_patch.sql`. All 11 server-side RPCs written from scratch. Schema columns added via `ADD COLUMN IF NOT EXISTS`. RLS policies, performance indexes.

**Schema additions:**
- `buildings`: `last_produced_at TIMESTAMPTZ`, `research_data TEXT DEFAULT '[]'`
- `building_inventory`: `item_type`, `expires_at`, `xp_bonus`, `buff_type`, `buff_value`, `buff_expires_at`
- `spirit_journal`: `description TEXT`, `event_type TEXT`
- `profiles`: `total_listen_minutes INT`, `last_seen_at TIMESTAMPTZ`, `last_egg_drop_at TIMESTAMPTZ`
- `expeditions`: `location TEXT DEFAULT 'night_market'`

---

### Session 18 — February 18, 2026 — Claude Sonnet 4.6
**V2.7 Hotfixes — send_expedition 400 errors**

Root causes: `expeditions` has no `created_at` (fixed to use `id`); function overload conflict (old 3-param signature still in DB); missing `UNIQUE (user_id, slot_number)` constraint.

Delivered `ehoro_v27_hotfix2.sql` — the working fix. Do not use `ehoro_v27_hotfix.sql` (broken).

**Critical rule added:** Always `DROP FUNCTION IF EXISTS` all known signatures before recreating RPCs.

---

### Session 19 — February 18, 2026 — Claude Sonnet 4.6
**V2.8: Full Client Feature Sprint — 10 changes**

All client-side, no SQL changes required.

1. Light theme readability — CSS variables darkened for high contrast on parchment.
2. Trait definitions complete — All 15+ traits fully defined. Four new traits added. Category "Cultivation" renamed to "Growth."
3. Cultivation UI removed — dead code preserved, RPC still exists.
4. Spirit naming at hatch — modal with name input. Rename button added to spirit detail.
5. Village buildings grid — new 2×N tile layout.
6. Building modal — full bottom-sheet with staff rows, Café drink menu, unlock cost.
7. Café starts unlocked — `ensureStarterPack()` auto-inserts Café building.
8. First expedition drops — guaranteed material, localStorage-tracked, gold border badge.
9. Evolution ceremony enhanced — white flash, 3 particle wave bursts, pulsing rings, trait slot count.
10. Expedition loot multiplier preview — green hint bar shows bonus per spirit count.

**File state:** V2.8 complete. `index.html` ~3,370 lines.

---

### Session 20 — February 18, 2026 — Claude Sonnet 4.6
**V2.9: Quality of Life + Building Depth Sprint — 7 features**

All client-side. No SQL changes required.

1. **Library research UI** — Full research flow. State in `lib_research_{userId}` localStorage.
2. **Building production ticker** — `checkBuildingProduction()` fires every 4 hours via `setInterval`.
3. **Resting countdown on spirit cards** — Live 💤 timer badge, updates every 500ms.
4. **Hatch-ready pulse on Items tab** — 🐣 emoji animates on tab when egg ready.
5. **Dojo XP float animation** — `+X XP` float on spirit card. Tier-aware: T1=5, T2=10, T3=15.
6. **Building tier upgrades (T1→T2→T3)** — All 5 buildings, costs defined, localStorage-only.
7. **Village tab notification dot** — Pulsing green dot when building produced since last visit.

**File state:** V2.9 complete. `index.html` 3,725 lines.

**Deferred to V3.0+:**
- Building tiers → DB persistence (localStorage lost on new device)
- Library research state → DB persistence
- `check_building_production` RPC should account for building tier
- `tick_active_cultivation` RPC should use Dojo tier
- Resting countdown 500ms re-render may cause jank at scale
- Studio/Garden tier benefits displayed but not enforced by RPC

---

### Session 21 — February 18, 2026 — Claude Sonnet 4.6
**V3.0 attempt: Glassmorphism redesign — REVERTED by owner**

A full CSS rewrite was attempted replacing all variables with a new glass system (`--glass-edge-top`, `--glass-edge-bottom`, layered shadows, `rgba(255,255,255,.11)` surfaces). Owner reviewed the result and found it visually worse than V2.9. **The rewrite was discarded.** The V2.9 file (`index__43_.html`) was restored as the working baseline.

**Lessons learned (added as Rules 15 and 16):**
- CSS rewrites are high-risk. Always propose before building.
- The existing CSS, while imperfect, has a coherent feel built over 20 sessions. Incremental patches are safer than wholesale rewrites.
- True glassmorphism requires `rgba(255,255,255,.10+)` surfaces, `blur(28px+)`, and luminous `rgba(255,255,255,.22)` top borders. Documented for future reference but not implemented.

**No file shipped from this session.**

---

### Session 22 — February 18, 2026 — Claude Sonnet 4.6
**V3.0: UX Bug Fix Patch — 11 targeted CSS fixes**

Working from `index__43_.html` (V2.9 baseline). Pure CSS patch appended at end of `<style>` block. Zero JS changes. Zero structural changes. Zero SQL changes.

**Fixes applied:**
1. **Building modal centering** — Desktop: `align-items:center` (was `flex-end`). Modal floats as centered card with spring animation. Mobile: stays as bottom sheet with drag handle and `sheetUp` animation.
2. **Mobile video 50vh minimum** — `flex:0 0 50vh` on `.video-area`. Hard-locked so no content can shrink it. Was `50vh` height but competing flex rules could override it.
3. **Expedition button dark theme** — `background:var(--t1); color:var(--bg)` enforced. Was rendering as an unstyled white block on mobile.
4. **Expedition slot container** — Added `background:var(--card-bg); border:1px solid var(--card-border)` so button has visual context.
5. **Tab bar contrast** — Inactive: `var(--t3)`. Active: `var(--t1)` bold. Was too low contrast on mobile.
6. **Tab touch targets** — `min-height:38px` on mobile tab buttons.
7. **Ingredient rows** — `padding:9px 12px`, `gap:5px` between rows. Was cramped.
8. **Hatchery slots on mobile** — `min-height:56px`, `max-height:72px` — was ballooning.
9. **Village rank bar** — `height:4px`, `min-width:4px` so 0% still shows a sliver. Was invisible.
10. **Stream pills active state** — Active pill now solid `var(--t1)` fill with `var(--bg)` text. Was nearly identical to inactive.
11. **Guest banner scroll clearance** — Tab panels get `padding-bottom:84px` on mobile so last content row is never hidden under the banner.
12. **Section labels** — `color:var(--t2)` and `font-weight:600`. Was `var(--t3)` weight 500 — too faint on mobile.

**File state:** V3.0 complete. `index.html` 3,958 lines (233 lines added as patch block).
**No SQL ran. No JS touched.**

---

### Session 23 — February 18, 2026 — Claude Sonnet 4.6
**V3.1: Expedition claim RPC fix + material persistence fix + third stream added**

Three separate fixes in this session. No CSS changes.

#### Fix 1 — `claim_expedition` RPC (two-step debug)

**Root cause 1 (400 overload):** PostgREST was finding multiple `claim_expedition` signatures. Fixed by dropping all known overloads before recreating. Manifesto Rule 13 confirmed critical.

**Root cause 2 (expedition_not_found_or_not_complete):** The RPC was checking `completed_at <= NOW()` but `completed_at` is never set by `send_expedition` — the client determines completion via `started_at + duration_minutes` time math. Fixed the WHERE clause to match:
```sql
AND (started_at + (duration_minutes || ' minutes')::INTERVAL) <= NOW()
```
Also changed the post-claim update from `completed_at = NULL` to `started_at = NULL` so `getExpedStatus()` correctly returns `'idle'` after claiming.

**Root cause 3 (column "item_id" does not exist):** The RPC was trying to insert loot into `building_inventory` with an `item_id` column that doesn't exist. Confirmed actual `building_inventory` columns: `id, user_id, item_type, item_name, item_tier, expires_at, created_at, xp_bonus, buff_type, buff_value, buff_expires_at`. **No `item_id`, no `quantity` column.**

Resolution: Materials from expeditions (`canvas_roll`, `grinder_stone`, etc.) are **display-only** in the loot reveal — not persisted to DB. Only emblem types (`cafe_bean`, `wild_essence`, `focus_shard`, `ashe_essence`, `spirit_essence`) are persisted, going into the `emblems` table via upsert. The RPC no longer touches `building_inventory` for loot.

**Schema note added:** `building_inventory` has NO `item_id` column and NO `quantity` column. Do not reference these in future RPCs.

#### Fix 2 — Material persistence + Studio unlock

`syncMaterialsFromInventory()` was building `S.materials` from `building_inventory` rows with `item_type='material'` — but expedition loot was never actually being written there (RPC was failing on `item_id`). Result: `hasMaterial('canvas_roll', 1)` always returned 0, making all building unlocks that require physical materials (Studio, Dojo, Library, Garden) impossible.

Two-part fix:
1. SQL: `ALTER TABLE building_inventory ADD COLUMN IF NOT EXISTS item_id TEXT` + `ADD COLUMN IF NOT EXISTS quantity INT NOT NULL DEFAULT 1`
2. Client: Updated `syncMaterialsFromInventory()` to key off `item_id || item_name` and sum `quantity` instead of always counting 1 per row

The RPC now correctly writes material drops to `building_inventory` (for emblem types → `emblems` table; for physical materials → `building_inventory` with `item_id`).

#### Fix 3 — Third stream added as new default

New stream `VrnORnrOphA` added as **Ehoro Village Radio** (`🌙`), now the primary default stream. Stream order: Ehoro Radio → Sakura Jazz → Lo-Fi Tape V1.

**Changes made (client only, no SQL):**
- Added `const STREAM_EHORO='VrnORnrOphA'`
- Updated `STREAM_YT` legacy alias to point to `STREAM_EHORO`
- Added `ehoro` key to `STREAM_META` object as first entry
- `S.currentStream` default changed from `'sakura'` to `'ehoro'`
- Login reset block updated to default to Ehoro Radio
- `getStreamMeta()` fallback updated from `sakura` to `ehoro`
- HTML stream-switcher: 3 pills now — `🌙 Ehoro Radio`, `🌸 Sakura Jazz`, `📼 Lo-Fi Tape` (labels shortened to fit mobile)
- Player strip and video placeholder default to Ehoro Radio
- `switchStream()` emoji logic extended to handle `'ehoro'` key (existing `key.charAt(0).toUpperCase()` pattern resolved `pillEhoro` automatically)

**Stream registry (current):**
| Key | Video ID | Label | Emoji |
|-----|----------|-------|-------|
| `ehoro` | `VrnORnrOphA` | Ehoro Village Radio | 🌙 |
| `sakura` | `rESYC5ikn58` | Sakura Jazz | 🌸 |
| `lofi` | `ojyT8dK0ZiA` | Lo-Fi Tape V1 | 📼 |

**File state:** V3.1 complete. `index.html` 3,727 lines.
**SQL run:** Two ALTER TABLE statements (add `item_id`, add `quantity` to `building_inventory`). Full `claim_expedition` RPC rewritten.

**Schema additions this session:**
- `building_inventory.item_id TEXT`
- `building_inventory.quantity INT DEFAULT 1`

---

### Session 24 — February 19, 2026 — Claude Sonnet 4.6
**V3.2: Full Trait + Alignment Implementation + localStorage → DB Migration**

Two SQL files ship with this session. Run `ehoro_v32_migration.sql` first, then `ehoro_v32_addendum.sql`.

#### What was implemented

**1. Material persistence bug fixed**
`syncMaterialsFromInventory()` was keying off `item_name` (display string) instead of `item_id`, and always counting 1 per row ignoring `quantity`. Fixed to key off `item_id || item_name` and sum `quantity`. This was the root cause of expedition materials never counting toward building unlocks.

**2. localStorage → DB (cross-device persistence)**
- Building tier: was `bldg_tier_{id}_{userId}` localStorage → now `buildings.tier` INT column. `getBuildingTier()` reads `S.buildings`. `upgradeBuilding()` now async, calls `upgrade_building` RPC.
- Library research: was `lib_research_{userId}` localStorage → now `buildings.research_data` TEXT column. `getLibraryResearch()` reads from `S.buildings`. `setLibraryResearch()` is now async and writes to DB.
- First expedition flags: were `firstExped_{loc}_{userId}` localStorage → now `profiles.first_exped_{location}` BOOLEAN columns. Set server-side inside `claim_expedition` RPC, with `set_first_expedition_flag` RPC as belt-and-suspenders.

**3. Expedition traits fully implemented (server-side)**
`claim_expedition` RPC rewritten to read `spirit_traits` for all spirits on the expedition and apply:
- `Wild` +15%, `Adventurous` +10%, `Scout` +20% → mat quantity multiplier
- `Highlands Reader` +30%, `Market Sharp` +30%, `Frost-Hardened` +40% → location-specific mat multiplier
- `Lucky` +8%, `Instinctive` +15% → rare drop chance bonus
- `Resilient` -20%, `Patient` -35% → rest duration multiplier
- `Wanderer` +10% → XP multiplier

**4. Building tier → production fully implemented (server-side)**
`check_building_production` RPC rewritten to read `buildings.tier`:
- Café: T1=House Brew (7% XP), T2=Village Blend (12%), T3=Reserve Roast (20%)
- Garden: T1=4 ingredients, T2=6 + highland_orchid chance, T3=10 + guaranteed rare
- Studio: T1=1 record, T2=2 + canvas chance, T3=3 + guaranteed canvas

**5. Tick XP now reads tier + drink buffs (server-side)**
`tick_active_cultivation` RPC rewritten:
- Café bonus: T1=+5%, T2=+8%, T3=+12% (manager required)
- Library bonus: T1=+10%, T2=+15%, T3=+20% (manager required)
- Active drink buffs (`buff_expires_at > NOW()`): reads `xp_flat` and `xp_pct` from `building_inventory`
- Spirit traits on the spirit itself: Focused +10%, Disciplined +25%, Meditative +15%, Calm +15%
- Client-side trait XP hack removed from ticker.

**6. Deep Roots evolution cost discount (server-side + client display)**
`evolve_spirit` RPC rewritten to check if the spirit has `Deep Roots` trait and apply -10% cost (27 instead of 30). Spirit detail UI updated to show the discounted cost with a green "Deep Roots -10%" tag when active.

**7. Gentle hatch time reduction (server-side)**
`place_egg_in_slot` RPC rewritten to check if any spirit in the user's village has the `Gentle` trait and reduce `hatch_duration_minutes` by 5% before writing to the `hatchery` row. The timer display was already reading `hatch_duration_minutes` from DB so it reflects the reduction automatically.

**8. Archivist research speed (client-side)**
`getResearchDurationMin()` now checks if the library manager has `research_speed` trait effect (Archivist) and applies -25% to the duration. T1+Archivist = 45min, T2+Archivist = 34min, T3+Archivist = 23min.

**9. Head Barista drink unlock (client-side)**
Café modal now checks if the manager spirit has `cafe_tier` trait effect (Head Barista trait). If yes, `effectiveCafeTier = max(buildingTier, 2)`, unlocking T2 drinks even at T1 building. A green hint shows when the trait is active.

**10. Alignment now has mechanical effects**
- Wicked alignment: `claim_expedition` applies +10% mat quantity multiplier per wicked spirit
- Heavenly alignment: `tick_active_cultivation` applies +15% XP per tick per heavenly spirit
- Spirit detail badges updated to show "+10% mats" / "+15% XP" next to alignment name

**11. Warm + village_presence — intentionally NOT implemented**
`Warm` trait (`village_presence`) is display-only. There is no prestige system for it to feed. Do not attempt to implement until a prestige/ranking system is designed. Leave as flavor text.

#### SQL run this session
- `ALTER TABLE buildings ADD COLUMN IF NOT EXISTS tier INT NOT NULL DEFAULT 1`
- `ALTER TABLE profiles ADD COLUMN IF NOT EXISTS first_exped_night_market BOOLEAN NOT NULL DEFAULT FALSE`
- `ALTER TABLE profiles ADD COLUMN IF NOT EXISTS first_exped_bamboo_highlands BOOLEAN NOT NULL DEFAULT FALSE`
- `ALTER TABLE profiles ADD COLUMN IF NOT EXISTS first_exped_frozen_ruins BOOLEAN NOT NULL DEFAULT FALSE`
- `ALTER TABLE building_inventory ADD COLUMN IF NOT EXISTS item_id TEXT` (V3.1, safe to re-run)
- `ALTER TABLE building_inventory ADD COLUMN IF NOT EXISTS quantity INT NOT NULL DEFAULT 1` (V3.1, safe to re-run)
- Full rewrites: `place_egg_in_slot`, `evolve_spirit`, `claim_expedition`, `tick_active_cultivation`, `check_building_production`
- New RPCs: `upgrade_building`, `set_first_expedition_flag`

**File state:** V3.2 complete. `index.html` 3,773 lines.

**Deferred / still not implemented:**
- `Warm` / `village_presence` — no prestige system to attach to
- `Studious` pill XP bonus — client-side only, not re-validated server-side (acceptable for companion app)
- Library research progress does not persist `startedListenMin` changes in real-time (only saves on complete or start) — low impact

---

### Session 25 — May 16, 2026 — Claude Opus 4.7
**V3.3: Recruiter-Level Polish Pass — typography fix, loading state, login rhythm, patch notes refresh**

Working from V3.2 baseline. Triggered by an outside design review (60-second recruiter walkthrough of `ehorovillage.com`) that flagged: "browser-default" typography, alarming "Reconnecting…" surface, login feels tacked-on, stale February 2026 patch date, mixed iconography. Triage:

#### Root cause of the "browser-default" perception — **THE big fix**

The CSS had **44 broken `font-family` declarations** and **17 broken `content:` pseudo-element rules** because curly typographic quotes (`'` U+2018/U+2019 and `"` U+201C/U+201D) had been substituted for straight ASCII quotes everywhere — likely from a copy-paste through a smart-quote tool somewhere in the manifesto-handoff chain.

Browsers silently ignore `font-family: 'Fraunces', serif` (curly quotes) and fall back to default. That's why Fraunces wasn't rendering anywhere except where the inline `'EhoroBrand'` override was applied at the bottom of the style block. Same for `[data-theme="light"]` attribute selectors — the light theme rules were dead.

**Resolution:** PowerShell pass on the index.html replacing only the structurally broken patterns:
- `'Fraunces'` / `'JetBrains Mono'` / `'Outfit'` / `'EhoroBrand'` → straight-quoted variants (44 instances)
- `content:''` and `content:'<emoji>'` with curly quote delimiters → straight quotes (17 instances)
- `[data-theme="light"]` and `[data-theme="dark"]` with curly bracket-quotes → straight quotes (4 instances)

User-facing prose with legitimate curly apostrophes (`Nature's Grace`, `Àṣẹ Essence`) was preserved.

**This is the single highest-impact change of the session.** Every Fraunces heading, every JetBrains Mono number readout, and every light-theme rule that was silently broken is now alive. The recruiter's "no clear font strategy, appears browser-default" call was diagnostically correct — the strategy existed in the CSS, the strategy just wasn't reaching the browser.

#### Other targeted fixes (Manifesto Rule 16 — direct, no proposal)

**1. Reconnecting overlay → "Settling in"**
- Title: "Reconnecting…" → "Settling in"
- Sub: "Trying to reach Ehoro Village servers" → "Your village is almost ready"
- Icon: `🔄` (spinning fast, alarm read) → `🌙` (spinning slowly, calm read)
- Retry message: "Retry attempt N…" → "Still settling in… (N)"
- **Added 2.5s debounce on `showReconnectOverlay()`** so transient network blips no longer flash this surface. Introduced `_reconnectShowTimer` and clears it in `hideReconnectOverlay()` so a fast-recovering connection never reveals the overlay at all.

**2. Patch notes refreshed**
- Banner: "Traits & Alignment" → "Polish & Performance"
- Date: "February 2026" → "May 2026"
- New top-line entry "Cleaner Type, Calmer Loading 🌙" explaining the typography fix and softer loading state in product-facing language

**3. Login spacing — the "tacked on" feel**
- Removed the inline `style="margin:-24px 0 28px"` hack on the tagline. Replaced with a `.login-tagline` class managed in the patch block.
- Added a coherent spacing scale in the patch block: brand margin, button rhythm, divider rhythm, focus-ring glow.

**4. Iconography unification — DEFERRED**
Recruiter flagged emoji + text mixing as "no unified system." Concluded these emojis (🥚 🌙 🥚 🧭 ✦) are intentional product personality, not arbitrary placeholders. Replacing them with an SVG icon set would cross from "targeted fix" into redesign territory, which Rule 16 says requires owner approval first. **Action:** Tighten surrounding spacing/typography via the patch block so the emojis read as deliberate, not random. Full icon-set proposal queued for V3.4 if the owner wants to push further.

#### CSS appended (V3.3 POLISH PATCH block at end of `<style>`)

Targeted rules, all in a clearly labeled patch comment block:
- `.login-tagline` — replaces the inline-style hack
- `.login-brand` margin tightened to 20px (was 48px — too much air)
- `.l-btn`, `.l-div`, `.l-secondary` margins forced to a single scale via `!important`
- `.login .l-btn:first-of-type` — guest button gets primary visual weight
- `.reconnect-icon` — slower (6s) rotation, calmer 2rem size, .85 opacity
- `.reconnect-title`/`.reconnect-sub` — colors softened to `--t2` / `--t4`
- `.login-field input:focus` — added soft glow (3px outset shadow) so active field reads at a glance
- `.tab-btn` — added color/background transition for taste
- `.settings-drop` — added a subtle outer ring shadow so it feels anchored
- `.patch-date` — color bumped from `--t4` to `--t3` so the date doesn't disappear
- `[data-theme="light"] .reconnect-icon` — opacity reduced to .65 (was nearly invisible on parchment)

All rules respect Rule 15: append-only, `!important` only when overriding inline styles or established cascade.

#### SQL run this session
**None.** Pure HTML + CSS + JS client patch. No schema changes, no RPC changes.

#### What's still broken / deferred to V3.4
- **Iconography proposal** — owner decides whether to unify emoji set with SVG icons or keep the current personality-driven mix
- **Background tab throttling** (carried from V1.x) — egg timer still drifts slow when backgrounded
- **`sendBeacon` on page close** (carried from V1.x) — session end isn't reliably recorded without the auth header
- **`Warm` / `village_presence`** — still needs a prestige system to attach to
- **Library research `startedListenMin` real-time persistence** — saves on start/complete only

#### Files touched
- `index.html` — 4 surgical edits (login tagline HTML, reconnect overlay HTML, reconnect overlay JS, V3.3 polish patch block) + 1 global PowerShell pass (curly-quote → straight-quote)
- `EHORO_MANIFESTO_3_3.md` — version bump (V3.2 → V3.3), Session 25 entry (this entry)

#### Backup
- `index.backup.html` saved alongside `index.html` before any edits — restore from there if anything broke

**File state:** V3.3 complete. `index.html` ~3,830 lines (≈55 lines added net: patch block, debounce timer, two HTML rewrites).

#### Recruiter recheck — what should change with this pass
1. **"Browser-default typography" → resolved.** Fraunces now reaches every header it was meant to.
2. **"Patch notes February 2026 (stale)" → resolved.** May 2026, with a fresh top-line entry.
3. **"Reconnecting… reads broken" → resolved.** Calmer wording, calmer motion, debounced so it doesn't flash on cold start.
4. **"Login tacked on" → improved, not perfect.** Spacing rhythm is now coherent. A full visual hierarchy proposal is the next step if owner wants to push further.
5. **"Emoji + text mixed iconography" → unchanged but flagged as a redesign decision for owner.** Not a bug.
6. **"Placeholder image paths (sprites/mowang_3.png)" → not actually placeholders.** Professor Mowang's portrait is a legitimate sprite reuse. No action.

If the recruiter rewalk shows lingering "amateur" reads after this lands in production, the next move is the iconography proposal — not more patch CSS.
