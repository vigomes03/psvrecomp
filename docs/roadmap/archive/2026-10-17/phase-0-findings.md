# Findings: phase 0 (acquisition)

> Metadata only (names, sizes, IDs). No game content.

## ROM files (`roms/`, private, ignored)

| File | Size | What |
|---|---:|---|
| `roms/Pokémon Violet.xci` | 7,985,954,816 | 8 GB cartridge, base game (v1.0.0 presumed ❓) |
| `roms/Pokémon Violet v4.0.0.nsp` | 5,235,895,884 | update **v4.0.0** (cleared by [USER] on 10/16: base of the recomp and of the reference Eden) |
| `roms/The Legend of Zelda Links Awakening [01006BB00C6F0000][v0].nsp` | 6,274,802,512 | Zelda LA v1.0.0. ⛔ **DO NOT USE** until it is confirmed it came from [USER]'s console/purchase |

**Decision (10/14, revised on 10/16):** base = **v1.0.0 cartridge** from [USER]'s console; the **v4.0.0** update was cleared
by [USER] and is the working version. Zelda only after its origin is confirmed.

## XCI (read without keys) ✅
HFS0 partitions: `update` (225 files, cartridge firmware), `logo`, `normal` (empty), `secure` (the game, encrypted NCAs).

## Update NSP (read without keys) ✅
- Title ID **`01008F6008C5E800`** (Violet update; base = `01008F6008C5E000`)
- Contents: `.cert`, `.tik` (ticket with the title key), 4 NCAs + `cnmt.nca`/`cnmt.xml`
- Largest NCA `d24a763a…` ≈ 5.2 GB: program patch (new exefs + romfs as BKTR over the base)

## v1.0.0 extraction (cartridge) ✅ 10/14
- Keys: `keys/prod.keys` from [USER]'s console. hactool (2023) aborts with the full file (`master_kek_source_*` with
  34 characters), so we use `keys/game.keys`, generated with only 111 content keys (`header_key`, `master_key_*`,
  `key_area_key_*`, `titlekek_*`), **none per-console**. Both ignored by git.
- ⚠️ Lesson: hactool prints key **values** in its `Failed to match key` warnings. Always filter the output
  (`sed -E 's/[0-9A-Fa-f]{32,}/<oculto>/g'` + `grep -v 'Failed to match key'`).
- `secure`: NCAs Program (6.7 GB), Control, Meta, 2× Manual; Title ID `01008F6008C5E000`.
- Output in `dumps/base/` (ignored): `exefs/` and `romfs/` (6.3 GB, only **24 files**).

## Executable inventory ✅ (`recomp/nso.py` + `analyze.py`)

| Module | build id (16) | .text | .rodata | .data | .bss | functions (`.eh_frame`) | named | imports |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `main` | `959ed651bf1ae0cc` | **48.1 MB** | 15.6 MB | 3.4 MB | 0.8 MB | **172,011** | **33** | 956 |
| `sdk` | `3644a6760469451c` | 5.8 MB | 6.7 MB | 0.4 MB | 0.7 MB | 30,320 | 23,656 | 14 |
| `subsdk0` | `d0f13015e5badf22` | 3.2 MB | 2.1 MB | 0.2 MB | 1.1 MB | 9,831 | 8,781 | 660 |

- SDK: `NintendoSdk_nnSdk-13_3_5-Release`.
- **`main` is practically symbol-free** (33 names in 172 thousand functions). The SDK and `subsdk0` have names (good for HLE).
  Function boundaries come from `.eh_frame`, so recompilation works the same. The difficulty is in **understanding**
  the game (phase 7/9): every name will be discovered through RE.
- `subsdk0` = Nintendo's multimedia library (`nn::movie`, codecs of Android origin, mkvparser, Opus/SILK).
- 📖 Middleware in `main` (string count; ❓ to confirm): **Wwise** (audio; `romfs/audio/wwise/.../Stream.pck` 930 MB,
  `PM.bnk`), **Havok** (`hk*` prefix), **Pia** (Nintendo networking), **Bink 2** (`.bk2` videos in `demo/movie`).
- romfs: `arc/data.trpfs` **5.15 GB** (single asset package) + `arc/data.trpfd` 11 MB (index), Wwise audio, Bink videos.

### Scale comparison with Zelda (❓ Zelda still needs to be measured with our own dump)
172k functions in 48 MB of `.text`. Estimate: generated C on the order of **several GB**. Phase 1.6 (measure 1% and extrapolate)
becomes a priority.

## Pending
- [x] `keys/prod.keys` (Lockpick_RCM on [USER]'s console)
- [x] Version decision: **cartridge v1.0.0** (switching to the update later = redo the generation, not the project)
- [x] Update v4.0.0 cleared by [USER] (10/16)
- [ ] Pipeline test with Zelda **if** [USER] owns the game (own dump)
