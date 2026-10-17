/*
 * pv_zelda_stubs.c - inert stand-ins for the Zelda hooks the LAS Vulkan renderer references
 * PVRecomp phase 4
 * every hook is off
 */
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <SDL3/SDL.h>
#include "nvn/nvn.h"

bool bind_settings_load(const char *key, const char *val) {
    (void)key;
    (void)val;
    return false;
}

void bind_settings_save(FILE *f) {
    (void)f;
}

void escape_bottle_tint(int kind, const float *ui, uint32_t ui_size, float tint[8]) {
    (void)kind;
    (void)ui;
    (void)ui_size;
    (void)tint;  // tint arrives zeroed = no tint (1.0 everywhere would mix full white)
}

volatile int g_debug_frame_request;

// (sizes from settings.h: settings_load walks N_*_COLOURS entries; 7-entry arrays read past the end -> crash at
// start once the menu had saved "tunic = Default" into psvrecomp.ini, 16/10)
#include "settings.h"
const char *const g_heart_colours[N_HEART_COLOURS] = {"Default", "Blue", "Green", "Purple", "Gold", "Orange", "Pink", "-", "-"};

const char *const g_tunic_colours[N_TUNIC_COLOURS] = {"Default", "Purple", "Orange", "Yellow", "Pink", "Teal", "Sky",
                                                       "-", "-", "-", "-", "-", "-"};

const char *game_level_name(void) {
    return "";
}

void input_frame(uint64_t frame) {
    (void)frame;
}

// input_handle_event: real implementation in hle/input.c (keyboard / gamepad, PVRecomp phase 5)

bool pets_hide_item_cursor(void) {
    return false;
}

bool pot_glow_active(void) {
    return false;
}

void pot_gold_tint(float tint[8]) {
    (void)tint;  // tint arrives zeroed = no tint (1.0 everywhere would mix full white)
}

bool pot_instance_gold(const float *m) {
    (void)m;
    return false;
}

bool pot_level_active(void) {
    return false;
}

bool pot_tint(const float *m, float tint[8], uint64_t mesh) {
    (void)m;
    (void)mesh;
    (void)tint;  // tint arrives zeroed = no tint (1.0 everywhere would mix full white)
    return false;
}

void reboot_test_frame(uint64_t frame) {
    (void)frame;
}

void save_editor_frame(void) {
}

void warp_frame(uint64_t frame) {
    (void)frame;
}

bool widescreen_allowed(void) {
    return false;
}

void widescreen_backdrop_seen(uint64_t hash) {
    (void)hash;
}

float widescreen_effect_stretch(uint64_t fs_hash) {
    (void)fs_hash;
    return 1.0f;
}

void widescreen_frame_end(uint64_t frame) {
    (void)frame;
}

void widescreen_present_crop(uint64_t frame, double shape, float crop[4], double *vx, double *vy, double *vw, double *vh) {
    // No widescreen hack for Pokémon: full image (uv 0..1), viewport from output_scale left as is.
    // (The W11 stub set vw = vh = 1.0, a 1x1-pixel viewport, and left crop uninitialized: black window.)
    (void)frame; (void)shape; (void)vx; (void)vy; (void)vw; (void)vh;
    crop[0] = crop[1] = 0.0f;
    crop[2] = crop[3] = 1.0f;
}

void widescreen_scene_ubo(const float *u, uint64_t size) {
    (void)u;
    (void)size;
}

void widescreen_set_factor(float f) {
    (void)f;
}
