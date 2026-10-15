# W11 — inert stand-ins for the Zelda hooks the LAS Vulkan renderer references (`runtime/nvn/vulkan/pv_zelda_stubs.c`)

## Context
We are porting the LAS Recomp Vulkan renderer to Pokémon Violet. The renderer calls about 25 hooks that only make
sense for Zelda: widescreen hacks, coloured pots/tunics/hearts, warp/save-editor UI, key binding, input. The link
fails with `undefined symbol` for each of them. We need definitions that do **nothing visible**, so the renderer
behaves as if every Zelda feature were off.

The context file `W11-decls.txt` has one block per symbol:
- `== name`;
- the declaration lines found in the LAS sources (`file:line: declaration`);
- `uses:` followed by 1-2 lines of how our Vulkan code uses it.

## Task
Output ONE C file, `pv_zelda_stubs.c`, that DEFINES every one of these 25 symbols:
bind_settings_load bind_settings_save escape_bottle_tint g_debug_frame_request g_heart_colours g_tunic_colours
game_level_name input_frame input_handle_event pets_hide_item_cursor pot_glow_active pot_gold_tint pot_instance_gold
pot_level_active pot_tint reboot_test_frame save_editor_frame warp_frame widescreen_allowed widescreen_backdrop_seen
widescreen_effect_stretch widescreen_frame_end widescreen_present_crop widescreen_scene_ubo widescreen_set_factor

Rules:
- **Types and signatures exactly as in the declarations given.** For arrays (e.g. `g_heart_colours[...]`) use the
  same element type and size as the declaration. Use `void *` only if a declaration is truly not given:
  `save_editor_frame` has none, and from its use it is `void save_editor_frame(void)`.
- Neutral behaviour:
  - functions return `false` / `0` / `NULL`, do nothing, and mark unused parameters `(void)p;`;
  - "allowed/active/seen" predicates return false;
  - tint / colour outputs: when a function fills a `float` array out-parameter, write 1.0f to every element
    (no tint); when it returns a colour struct or value, return white/1.0;
  - globals are zero-initialised, except colour tables, which must be filled with 1.0f (white).
- `widescreen_present_crop` and `widescreen_set_factor`: copy the semantics of "no crop / factor 1" from their
  declarations' comments (e.g. leave output rectangles untouched, or set them to the full size if they are
  out-parameters).
- Includes: `<stdbool.h>`, `<stdint.h>`, `<stddef.h>`, `<SDL3/SDL.h>` (for `SDL_Event`), and `"../nvn.h"` (for
  `NvnTexture` and `Cpu` if needed). Do NOT include any LAS-only header (`rando.h`, `input_bind.h`, `ui/*.h`,
  `widescreen.h`...): if a declaration uses a type from such a header, replace that parameter with `const void *` and
  write a comment saying so.
- Start the file with a 3-line comment: what the file is, "PVRecomp phase 4", and "every hook is off".

## Acceptance (Claude runs it)
`bash recomp/build_host.sh lab/host-vk vulkan` links with no `undefined symbol` from this list, and no
`conflicting types` errors.
