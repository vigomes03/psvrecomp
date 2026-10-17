// Controller input for the Pokémon host (phase 5 start): nn::hid Npad state functions answered by the host, as
// LASRecomp's runtime/hle/input.c does (ported: same NpadXxxState layout, FullKey on player 1, docked).
//
// Window build (PVR_VULKAN): keyboard and any SDL gamepad, added to the script below.
//   Keyboard: WASD left stick, arrows d-pad, K/J/L/I = A/B/X/Y (Switch positions: A east, B south, X north, Y west),
//             Space = A, Q/E = L/R, 1/3 = ZL/ZR, Enter = Plus, Backspace = Minus, F/R = left/right stick click,
//             numpad 8/4/5/6 = right stick.  (Same layout as LASRecomp's defaults, plus Space.)
//   Gamepad:  by position (Switch layout): east = A, south = B, north = X, west = Y; shoulders L/R, triggers ZL/ZR,
//             Start = Plus, Back = Minus, sticks and d-pad as they are.
// Scripted input, so test runs follow the same path through the menus:
//   PVR_AUTOPRESS=<button>[:period_ms[:hold_ms[:start_ms]]]   e.g. A:1000:100:3000 (A for 100 ms every 1 s from 3 s)
//   PVR_INPUT=<start_ms>:<BUTTON>[:<len_ms>],...               e.g. 3000:A,4000:DOWN:200,5000:A
// Times are from the first state poll. Buttons: A B X Y LSTICK RSTICK L R ZL ZR PLUS MINUS LEFT UP RIGHT DOWN, and the
// left stick fully tilted: STICK_LEFT STICK_RIGHT STICK_UP STICK_DOWN (PVR_AUTOPRESS too, e.g. STICK_RIGHT:5000:300).
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "../hle.h"
#include "../kernel.h"
#include "../platform.h"

static const char *const names[] = {"A", "B", "X", "Y", "LSTICK", "RSTICK", "L", "R", "ZL", "ZR", "PLUS", "MINUS",
                                    "LEFT", "UP", "RIGHT", "DOWN"};

// NpadButton bits 16..19: left stick tilted left / up / right / down (the hardware sets them with the axes)
static const char *const stick_names[] = {"STICK_LEFT", "STICK_UP", "STICK_RIGHT", "STICK_DOWN"};

static int button_bit(const char *name) {
    for (int i = 0; i < 16; i++)
        if (!strcmp(name, names[i])) return i;
    for (int i = 0; i < 4; i++)
        if (!strcmp(name, stick_names[i])) return 16 + i;
    return -1;
}

static uint64_t script_buttons(uint64_t ms) {
    uint64_t b = 0;
    const char *ap = getenv("PVR_AUTOPRESS");
    if (ap) {
        char name[16] = "A";
        unsigned long period = 1000, hold = 100, start = 0;
        sscanf(ap, "%15[A-Z_]:%lu:%lu:%lu", name, &period, &hold, &start);
        int bit = button_bit(name);
        if (bit >= 0 && period && ms >= start && (ms - start) % period < hold) b |= 1ull << bit;
    }
    const char *spec = getenv("PVR_INPUT");
    if (spec) {
        static char buf[16384];
        snprintf(buf, sizeof buf, "%s", spec);
        char *save = NULL;
        for (char *tok = strtok_r(buf, ",", &save); tok; tok = strtok_r(NULL, ",", &save)) {
            unsigned long start = 0, len = 100;
            char name[32] = "";
            if (sscanf(tok, "%lu:%31[A-Z_0-9]:%lu", &start, name, &len) < 2) continue;
            int bit = button_bit(name);
            if (bit >= 0 && ms >= start && ms < start + len) b |= 1ull << bit;
        }
    }
    return b;
}

// ------------------------------------------------------------------ keyboard / gamepad (window build)
static _Atomic uint64_t host_buttons;
static _Atomic int32_t host_lx, host_ly, host_rx, host_ry;

#ifdef PVR_VULKAN
#include <SDL3/SDL.h>

enum { B_A, B_B, B_X, B_Y, B_LSTICK, B_RSTICK, B_L, B_R, B_ZL, B_ZR, B_PLUS, B_MINUS, B_LEFT, B_UP, B_RIGHT, B_DOWN };
static const struct { SDL_Scancode sc; int bit; } keymap[] = {
    {SDL_SCANCODE_K, B_A}, {SDL_SCANCODE_SPACE, B_A}, {SDL_SCANCODE_J, B_B}, {SDL_SCANCODE_I, B_X}, {SDL_SCANCODE_L, B_Y},
    {SDL_SCANCODE_Q, B_L}, {SDL_SCANCODE_E, B_R}, {SDL_SCANCODE_1, B_ZL}, {SDL_SCANCODE_3, B_ZR},
    {SDL_SCANCODE_RETURN, B_PLUS}, {SDL_SCANCODE_BACKSPACE, B_MINUS}, {SDL_SCANCODE_F, B_LSTICK}, {SDL_SCANCODE_R, B_RSTICK},
    {SDL_SCANCODE_LEFT, B_LEFT}, {SDL_SCANCODE_UP, B_UP}, {SDL_SCANCODE_RIGHT, B_RIGHT}, {SDL_SCANCODE_DOWN, B_DOWN},
};
static const struct { SDL_GamepadButton gb; int bit; } padmap[] = {
    {SDL_GAMEPAD_BUTTON_EAST, B_A}, {SDL_GAMEPAD_BUTTON_SOUTH, B_B}, {SDL_GAMEPAD_BUTTON_NORTH, B_X},
    {SDL_GAMEPAD_BUTTON_WEST, B_Y}, {SDL_GAMEPAD_BUTTON_LEFT_STICK, B_LSTICK}, {SDL_GAMEPAD_BUTTON_RIGHT_STICK, B_RSTICK},
    {SDL_GAMEPAD_BUTTON_LEFT_SHOULDER, B_L}, {SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER, B_R}, {SDL_GAMEPAD_BUTTON_START, B_PLUS},
    {SDL_GAMEPAD_BUTTON_BACK, B_MINUS}, {SDL_GAMEPAD_BUTTON_DPAD_LEFT, B_LEFT}, {SDL_GAMEPAD_BUTTON_DPAD_UP, B_UP},
    {SDL_GAMEPAD_BUTTON_DPAD_RIGHT, B_RIGHT}, {SDL_GAMEPAD_BUTTON_DPAD_DOWN, B_DOWN},
};
static uint8_t keys_down[SDL_SCANCODE_COUNT];
static uint64_t input_ms(void);
// A quick tap is released before the game samples the pad: each key-down keeps its button held for >= 120 ms.
static _Atomic uint64_t press_ms[16];
static SDL_Gamepad *pad;

static void recompute(void) {
    uint64_t b = 0;
    for (size_t i = 0; i < sizeof keymap / sizeof *keymap; i++)
        if (keys_down[keymap[i].sc]) b |= 1ull << keymap[i].bit;
    int32_t lx = (keys_down[SDL_SCANCODE_D] - keys_down[SDL_SCANCODE_A]) * 32767;
    int32_t ly = (keys_down[SDL_SCANCODE_W] - keys_down[SDL_SCANCODE_S]) * 32767;
    int32_t rx = (keys_down[SDL_SCANCODE_KP_6] - keys_down[SDL_SCANCODE_KP_4]) * 32767;
    int32_t ry = (keys_down[SDL_SCANCODE_KP_8] - keys_down[SDL_SCANCODE_KP_5]) * 32767;
    if (pad) {
        for (size_t i = 0; i < sizeof padmap / sizeof *padmap; i++)
            if (SDL_GetGamepadButton(pad, padmap[i].gb)) b |= 1ull << padmap[i].bit;
        if (SDL_GetGamepadAxis(pad, SDL_GAMEPAD_AXIS_LEFT_TRIGGER) > 16000) b |= 1ull << B_ZL;
        if (SDL_GetGamepadAxis(pad, SDL_GAMEPAD_AXIS_RIGHT_TRIGGER) > 16000) b |= 1ull << B_ZR;
        int32_t px = SDL_GetGamepadAxis(pad, SDL_GAMEPAD_AXIS_LEFTX), py = -SDL_GetGamepadAxis(pad, SDL_GAMEPAD_AXIS_LEFTY);
        int32_t qx = SDL_GetGamepadAxis(pad, SDL_GAMEPAD_AXIS_RIGHTX), qy = -SDL_GetGamepadAxis(pad, SDL_GAMEPAD_AXIS_RIGHTY);
        if (px * px + py * py > 4000 * 4000) { lx = px; ly = py; }  // (dead zone: a resting stick doesn't hide the keys)
        if (qx * qx + qy * qy > 4000 * 4000) { rx = qx; ry = qy; }
    }
    host_buttons = b;
    host_lx = lx < -32767 ? -32767 : lx; host_ly = ly < -32767 ? -32767 : ly;
    host_rx = rx < -32767 ? -32767 : rx; host_ry = ry < -32767 ? -32767 : ry;
}

// The overlay menu opened or closed (runtime/ui/menu.cpp): nothing held carries over.
void input_reset(void) {
    memset(keys_down, 0, sizeof keys_down);
    for (int i = 0; i < 16; i++) press_ms[i] = 0;
    recompute();
}

// From the window's event loop (nvn/vulkan/device.c ui_run).
void input_handle_event(const SDL_Event *e) {
    switch (e->type) {
    case SDL_EVENT_KEY_DOWN:
    case SDL_EVENT_KEY_UP: {
        static int nkey;
        if (e->type == SDL_EVENT_KEY_DOWN && !e->key.repeat && nkey++ < 200)
            LOG("[input] key down scancode %d (%s)\n", (int)e->key.scancode, SDL_GetScancodeName(e->key.scancode));
        if (e->key.scancode < SDL_SCANCODE_COUNT) keys_down[e->key.scancode] = e->type == SDL_EVENT_KEY_DOWN;
        if (e->type == SDL_EVENT_KEY_DOWN && !e->key.repeat)
            for (size_t i = 0; i < sizeof keymap / sizeof *keymap; i++)
                if (keymap[i].sc == e->key.scancode) press_ms[keymap[i].bit] = input_ms() + 1;
        break;
    }
    case SDL_EVENT_WINDOW_FOCUS_GAINED: LOG("[input] window focus gained\n"); return;
    case SDL_EVENT_WINDOW_FOCUS_LOST: LOG("[input] window focus lost\n"); memset(keys_down, 0, sizeof keys_down); break;
    case SDL_EVENT_GAMEPAD_ADDED:
        if (!pad) {
            pad = SDL_OpenGamepad(e->gdevice.which);
            LOG("[input] gamepad: %s\n", pad ? SDL_GetGamepadName(pad) : SDL_GetError());
        }
        break;
    case SDL_EVENT_GAMEPAD_REMOVED:
        if (pad && SDL_GetGamepadID(pad) == e->gdevice.which) { SDL_CloseGamepad(pad); pad = NULL; LOG("[input] gamepad removed\n"); }
        break;
    case SDL_EVENT_GAMEPAD_BUTTON_DOWN: case SDL_EVENT_GAMEPAD_BUTTON_UP: case SDL_EVENT_GAMEPAD_AXIS_MOTION: break;
    default: return;
    }
    recompute();
}
#endif

static uint64_t input_ms(void) {
    static uint64_t t0;
    uint64_t now = plat_now_ns();
    if (!t0) t0 = now;
    return (now - t0) / 1000000ull;
}

// NpadXxxState (0x28): sampling_number, buttons, left stick x/y, right stick x/y, attributes (bit 0: connected)
static void fill_one(uint8_t *s, uint32_t id, int64_t sampling, uint64_t buttons) {
    int32_t hlx = host_lx, hly = host_ly;
    memset(s, 0, 0x28);
    *(int64_t *)s = sampling;
    if (id != 0) return;  // player 1 only (docked: no handheld), others disconnected
    *(uint64_t *)(s + 8) = buttons;
    int32_t lx = 0, ly = 0;  // left stick from the stick "buttons" (bits 16..19)
    if (buttons & (1ull << 16)) lx = -32767;
    if (buttons & (1ull << 18)) lx = 32767;
    if (buttons & (1ull << 17)) ly = 32767;
    if (buttons & (1ull << 19)) ly = -32767;
#ifdef PVR_VULKAN
    extern bool menu_input_captured(void);
    if (menu_input_captured()) hlx = hly = 0;
#endif
    if (!lx && !ly) { lx = hlx; ly = hly; }  // keyboard / gamepad stick
    // stick direction bits (16..19 left, 20..23 right) as the hardware sets them
    if (lx < -16000) buttons |= 1ull << 16;
    if (ly > 16000) buttons |= 1ull << 17;
    if (lx > 16000) buttons |= 1ull << 18;
    if (ly < -16000) buttons |= 1ull << 19;
    int32_t rx = host_rx, ry = host_ry;
#ifdef PVR_VULKAN
    if (menu_input_captured()) rx = ry = 0;
#endif
    if (rx < -16000) buttons |= 1ull << 20;
    if (ry > 16000) buttons |= 1ull << 21;
    if (rx > 16000) buttons |= 1ull << 22;
    if (ry < -16000) buttons |= 1ull << 23;
    *(uint64_t *)(s + 8) = buttons;
    *(int32_t *)(s + 24) = rx;
    *(int32_t *)(s + 28) = ry;
    *(int32_t *)(s + 16) = lx;
    *(int32_t *)(s + 20) = ly;
    *(uint32_t *)(s + 32) = 1;  // IsConnected
}

static void fill_state(Cpu *c, int n) {
    uint8_t *s = (uint8_t *)(uintptr_t)c->x[0];
    uint32_t id = *(uint32_t *)(uintptr_t)c->x[n ? 2 : 1];
    static int64_t sampling;
    int64_t smp = __atomic_add_fetch(&sampling, 1, __ATOMIC_RELAXED);
    uint64_t ms = input_ms(), b = script_buttons(ms) | host_buttons;
#ifdef PVR_VULKAN
    for (int i = 0; i < 16; i++)
        if (press_ms[i] && ms + 1 - press_ms[i] < 120) b |= 1ull << i;
    extern bool menu_input_captured(void);  // (runtime/ui/menu.cpp: the menu has the keyboard / controller)
    if (menu_input_captured()) b = script_buttons(ms);
#endif
    static uint64_t last_b = ~0ull;
    if (id == 0 && b != last_b) {  // (also logs keyboard / gamepad: proves the game reads them)
        LOG("[input] t=%llu ms buttons %#llx\n", (unsigned long long)ms, (unsigned long long)b);
        last_b = b;
    }
    static int32_t last_lx, last_ly;
    if (id == 0 && (host_lx != last_lx || host_ly != last_ly)) {
        last_lx = host_lx; last_ly = host_ly;
        LOG("[input] t=%llu ms left stick %d %d\n", (unsigned long long)ms, (int)last_lx, (int)last_ly);
    }
    if (!n) { fill_one(s, id, smp, b); return; }
    int cnt = (int)c->x[1];  // GetNpadStates(out, count, id): newest first; we keep one sample, repeated
    for (int i = 0; i < cnt; i++) fill_one(s + 0x28 * i, id, smp - i, b);
    c->x[0] = (uint64_t)(cnt > 0 ? cnt : 0);
}

HLE_FUNC("_ZN2nn3hid12GetNpadStateEPNS0_16NpadFullKeyStateERKj", pv_hid_state_fullkey) { fill_state(c, 0); }
HLE_FUNC("_ZN2nn3hid12GetNpadStateEPNS0_16NpadJoyDualStateERKj", pv_hid_state_dual) { fill_state(c, 0); }
HLE_FUNC("_ZN2nn3hid12GetNpadStateEPNS0_16NpadJoyLeftStateERKj", pv_hid_state_left) { fill_state(c, 0); }
HLE_FUNC("_ZN2nn3hid12GetNpadStateEPNS0_17NpadHandheldStateERKj", pv_hid_state_handheld) { fill_state(c, 0); }
HLE_FUNC("_ZN2nn3hid12GetNpadStateEPNS0_17NpadJoyRightStateERKj", pv_hid_state_right) { fill_state(c, 0); }
HLE_FUNC("_ZN2nn3hid13GetNpadStatesEPNS0_16NpadFullKeyStateEiRKj", pv_hid_states_fullkey) { fill_state(c, 1); }
HLE_FUNC("_ZN2nn3hid13GetNpadStatesEPNS0_16NpadJoyDualStateEiRKj", pv_hid_states_dual) { fill_state(c, 1); }
HLE_FUNC("_ZN2nn3hid13GetNpadStatesEPNS0_16NpadJoyLeftStateEiRKj", pv_hid_states_left) { fill_state(c, 1); }
HLE_FUNC("_ZN2nn3hid13GetNpadStatesEPNS0_17NpadHandheldStateEiRKj", pv_hid_states_handheld) { fill_state(c, 1); }
HLE_FUNC("_ZN2nn3hid13GetNpadStatesEPNS0_17NpadJoyRightStateEiRKj", pv_hid_states_right) { fill_state(c, 1); }

// FullKey (bit 0) for player 1 only
HLE_FUNC("_ZN2nn3hid15GetNpadStyleSetERKj", pv_hid_style_set) {
    uint32_t id = *(uint32_t *)(uintptr_t)c->x[0];
    c->x[0] = id == 0 ? 1 : 0;
}

// Signaled once so the game sees a controller connected (LAS: same).
HLE_FUNC("_ZN2nn3hid27BindNpadStyleSetUpdateEventERKjPNS_2os15SystemEventTypeENS3_14EventClearModeE", pv_hid_bind_style_event) {
    uint32_t w, r;
    KEvent *ev = kernel_create_event_pair(&w, &r);
    pthread_mutex_lock(&g_klock);
    kernel_signal((KObject *)ev);
    pthread_mutex_unlock(&g_klock);
    uint64_t clear_mode = c->x[2];
    c->x[0] = c->x[1];
    c->x[1] = r;
    c->x[2] = 0;
    c->x[3] = clear_mode;
    guest_call(c, guest_sym("_ZN2nn2os33AttachReadableHandleToSystemEventEPNS0_15SystemEventTypeEjbNS0_14EventClearModeE"));
    LOG("[input] style set update event bound\n");
}

// Vibration devices: accepted but inert (LAS: same). Without these the SDK talks to the missing hid service.
HLE_FUNC("_ZN2nn3hid25InitializeVibrationDeviceERKNS0_21VibrationDeviceHandleE", pv_hid_init_vibration) { (void)c; }
HLE_FUNC("_ZN2nn3hid18SendVibrationValueERKNS0_21VibrationDeviceHandleERKNS0_14VibrationValueE", pv_hid_send_vibration) { (void)c; }
HLE_FUNC("_ZN2nn3hid25GetVibrationDeviceHandlesEPNS0_21VibrationDeviceHandleEiRKjNS_4util10BitFlagSetILi32ENS0_12NpadStyleTagEEE", pv_hid_vibration_handles) {
    uint32_t *out = (uint32_t *)(uintptr_t)c->x[0];
    int n = (int)c->x[1] < 2 ? (int)c->x[1] : 2;
    uint32_t id = *(uint32_t *)(uintptr_t)c->x[2];
    for (int i = 0; i < n; i++) out[i] = (id & 0xFF) << 8 | (uint32_t)i | 0x03000000u;  // type, player, position
    c->x[0] = (uint64_t)(n > 0 ? n : 0);
}
HLE_FUNC("_ZN2nn3hid22GetVibrationDeviceInfoEPNS0_19VibrationDeviceInfoERKNS0_21VibrationDeviceHandleE", pv_hid_vibration_info) {
    uint32_t *info = (uint32_t *)(uintptr_t)c->x[0];
    uint32_t h = *(uint32_t *)(uintptr_t)c->x[1];
    info[0] = 1;      // VibrationDeviceType_LinearResonantActuator
    info[1] = h & 1;  // position: left / right
}

// Six-axis sensor: handles exist, the sensor reports nothing (at rest).
HLE_FUNC("_ZN2nn3hid23GetSixAxisSensorHandlesEPNS0_19SixAxisSensorHandleEiRKjNS_4util10BitFlagSetILi32ENS0_12NpadStyleTagEEE", pv_hid_sixaxis_handles) {
    uint32_t *out = (uint32_t *)(uintptr_t)c->x[0];
    int n = (int)c->x[1] < 2 ? (int)c->x[1] : 2;
    uint32_t id = *(uint32_t *)(uintptr_t)c->x[2];
    for (int i = 0; i < n; i++) out[i] = (id & 0xFF) << 8 | (uint32_t)i | 0x03000000u;
    c->x[0] = (uint64_t)(n > 0 ? n : 0);
}
HLE_FUNC("_ZN2nn3hid18StartSixAxisSensorERKNS0_19SixAxisSensorHandleE", pv_hid_sixaxis_start) { (void)c; }
HLE_FUNC("_ZN2nn3hid17StopSixAxisSensorERKNS0_19SixAxisSensorHandleE", pv_hid_sixaxis_stop) { (void)c; }
HLE_FUNC("_ZN2nn3hid21IsSixAxisSensorAtRestERKNS0_19SixAxisSensorHandleE", pv_hid_sixaxis_rest) { c->x[0] = 1; }
HLE_FUNC("_ZN2nn3hid21GetSixAxisSensorStateEPNS0_18SixAxisSensorStateERKNS0_19SixAxisSensorHandleE", pv_hid_sixaxis_state) {
    memset((void *)(uintptr_t)c->x[0], 0, 0x60);
}
HLE_FUNC("_ZN2nn3hid22GetSixAxisSensorStatesEPNS0_18SixAxisSensorStateEiRKNS0_19SixAxisSensorHandleE", pv_hid_sixaxis_states) {
    int n = (int)c->x[1];
    if (n > 0) memset((void *)(uintptr_t)c->x[0], 0, 0x60ull * (uint64_t)n);
    c->x[0] = 0;  // no samples
}
