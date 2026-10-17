// PVRecomp (phase 4): stand-ins for LAS pieces the Vulkan renderer references that are Zelda-specific or not ported
// yet: texture patches (texpatch.c: Zelda button prompts / bottle / hearts), the ImGui menu (ui/), the shipped icon.
// Each returns "nothing to do", so the renderer draws the game's own frames unchanged.
#include <SDL3/SDL.h>
#include <stdbool.h>
#include <stdint.h>

#include "../nvn.h"

// texpatch.h
int texpatch_identify(const NvnTexture *t) { (void)t; return -1; }
int texpatch_bottle_kind(int id) { (void)id; return 0; }
bool texpatch_is_item_cursor(int id) { (void)id; return false; }
uint32_t texpatch_generation(void) { return 0; }
void texpatch_apply(int id, uint32_t lv, uint8_t *blocks, uint32_t w, uint32_t h, uint32_t row) {
    (void)id; (void)lv; (void)blocks; (void)w; (void)h; (void)row;
}
int texpatch_heart_kind(int id) { (void)id; return 0; }
void texpatch_heart_tint(int kind, float tint[8]) { (void)kind; (void)tint; }  // zeroed tint = none

// paths.h
void rt_window_icon(SDL_Window *w) { (void)w; }
