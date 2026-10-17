// In-game overlay menu (Dear ImGui on the Vulkan renderer; input fed from SDL events). Adapted from LAS Recomp's
// runtime/ui/menu.mm (MIT): same look (option rows, Baloo 2, gold on green), same controls - F1 / Esc, or the
// controller's Home button / Back + Start, opens and closes it; L / R (Q / E) switch tabs; B (Esc) backs out.
// Tabs: Controls (the key / button layout), Video, Audio, Quit. The game gets no input while it is open.
//
// Threads: SDL events arrive on the main thread and are queued; the menu is laid out and drawn on the render thread
// inside the window image's rendering (device.c menu_render), after the game image.
#include <SDL3/SDL.h>
#include <math.h>
#include <pthread.h>
#include <stdio.h>
#include <string.h>
#include <atomic>
#include <vector>

#include "imgui.h"
#include "imgui_impl_vulkan.h"
#include "imgui_internal.h"  // (NavCursorVisible)
#include "option_rows.h"
#include "osk.h"

extern "C" {
#include "../hle.h"
#include "../settings.h"
#include "menu.h"
bool vk_imgui_backend_init(void);  // runtime/nvn/vulkan/imgui_glue.cpp
void input_reset(void);            // runtime/hle/input.c
void renderer_get_scale(float *sx, float *sy);
double output_scale_dynamic_factor(void);
void ui_request_swapchain(void);   // runtime/nvn/vulkan/device.c (VSync changed)
int g_title_fps10_get(void);       // device.c: the game's frame rate x10 (-1: not yet)
}

// ------------------------------------------------------------------ state shared with the main thread
static std::atomic<bool> g_open{false};
static std::atomic<bool> g_want_fullscreen_apply{false};
static std::atomic<bool> g_want_display_apply{false};

struct QEvent {
    enum { KEY, ANALOG, MOUSE_POS, MOUSE_BUTTON, WHEEL, TEXT } kind;
    ImGuiKey key;
    bool down;
    float value, x, y;
    int button;
    char text[32];
};
static pthread_mutex_t q_lock = PTHREAD_MUTEX_INITIALIZER;
static std::vector<QEvent> q_events;
static float g_pixel_density = 1;

static void push(const QEvent &e) {
    pthread_mutex_lock(&q_lock);
    q_events.push_back(e);
    pthread_mutex_unlock(&q_lock);
}

bool menu_is_open(void) { return g_open.load(); }
extern "C" bool menu_input_captured(void) { return g_open.load(); }  // (runtime/hle/input.c: the game sees nothing)
static void set_open(bool open);
static int g_tab_request_ext = -1;
extern "C" void menu_test_open(void) {  // (test) LARECOMP_MENU_AT=<frame> [LARECOMP_MENU_TAB=<id>]
    set_open(true);
    if (getenv("LARECOMP_MENU_TAB")) g_tab_request_ext = atoi(getenv("LARECOMP_MENU_TAB"));
}

// (test) PVR_MENU_KEYS=<frame>:<key>,... : key presses (SDL scancode names: F1, Down, Right, E, Escape, K) pushed
// into the window's event loop at those presented frames, so a run drives the menu like a player.
extern "C" void menu_test_keys(uint64_t frame) {
    static const char *spec = getenv("PVR_MENU_KEYS");
    if (!spec) return;
    char buf[2048];
    snprintf(buf, sizeof buf, "%s", spec);
    char *save = NULL;
    for (char *tok = strtok_r(buf, ",", &save); tok; tok = strtok_r(NULL, ",", &save)) {
        unsigned long long at = 0;
        char name[32] = "";
        if (sscanf(tok, "%llu:%31[^,]", &at, name) != 2 || at != frame) continue;
        SDL_Scancode sc = SDL_GetScancodeFromName(name);
        if (sc == SDL_SCANCODE_UNKNOWN) { LOG("[menu] test key %s: unknown\n", name); continue; }
        SDL_Event e = {};
        e.type = SDL_EVENT_KEY_DOWN;
        e.key.scancode = sc;
        e.key.down = true;
        SDL_PushEvent(&e);
        e.type = SDL_EVENT_KEY_UP;
        e.key.down = false;
        SDL_PushEvent(&e);
        LOG("[menu] test key %s at frame %llu\n", name, at);
    }
}

static void menu_tabs_focus(bool first_tab);
static void set_open(bool open) {
    if (open == g_open.load()) return;
    g_open.store(open);
    input_reset();  // nothing held while the menu had focus leaks into the game
    static Settings before;  // (closed with changes: watch the next frames - a crash restarts on the defaults)
    if (open) {
        before = g_settings;
        static bool opened;  // the controller's cursor: the first tab the first time this session, later the selected one
        menu_tabs_focus(!opened);
        opened = true;
    }
    else {
        settings_save();
        if (memcmp(&before, &g_settings, sizeof before)) settings_arm_check();
        osk_cancel();
    }
    LOG("[menu] %s\n", open ? "opened" : "closed");
}

static ImGuiKey key_from_scancode(SDL_Scancode sc) {
    switch (sc) {
    case SDL_SCANCODE_UP: return ImGuiKey_UpArrow;
    case SDL_SCANCODE_DOWN: return ImGuiKey_DownArrow;
    case SDL_SCANCODE_LEFT: return ImGuiKey_LeftArrow;
    case SDL_SCANCODE_RIGHT: return ImGuiKey_RightArrow;
    case SDL_SCANCODE_RETURN: return ImGuiKey_Enter;
    case SDL_SCANCODE_KP_ENTER: return ImGuiKey_KeypadEnter;
    case SDL_SCANCODE_SPACE: return ImGuiKey_Space;
    case SDL_SCANCODE_TAB: return ImGuiKey_Tab;
    case SDL_SCANCODE_BACKSPACE: return ImGuiKey_Backspace;
    case SDL_SCANCODE_HOME: return ImGuiKey_Home;
    case SDL_SCANCODE_END: return ImGuiKey_End;
    case SDL_SCANCODE_PAGEUP: return ImGuiKey_PageUp;
    case SDL_SCANCODE_PAGEDOWN: return ImGuiKey_PageDown;
    case SDL_SCANCODE_LSHIFT: return ImGuiKey_LeftShift;
    case SDL_SCANCODE_RSHIFT: return ImGuiKey_RightShift;
    case SDL_SCANCODE_LCTRL: return ImGuiKey_LeftCtrl;
    case SDL_SCANCODE_RCTRL: return ImGuiKey_RightCtrl;
    case SDL_SCANCODE_Q: return ImGuiKey_Q;  // previous tab
    case SDL_SCANCODE_E: return ImGuiKey_E;  // next tab
    // the game's own confirm / back keys work in the menu too: K / Space confirm, J backs out
    case SDL_SCANCODE_K: return ImGuiKey_Space;
    case SDL_SCANCODE_J: return ImGuiKey_Escape;
    default: return ImGuiKey_None;
    }
}

// Nintendo layout, as in the game: the right face button (A) confirms, the bottom one (B) goes back.
static ImGuiKey key_from_pad(Uint8 b) {
    switch (b) {
    case SDL_GAMEPAD_BUTTON_EAST: return ImGuiKey_GamepadFaceDown;   // activate
    case SDL_GAMEPAD_BUTTON_SOUTH: return ImGuiKey_GamepadFaceRight; // cancel / back
    case SDL_GAMEPAD_BUTTON_NORTH: return ImGuiKey_GamepadFaceUp;
    case SDL_GAMEPAD_BUTTON_WEST: return ImGuiKey_GamepadFaceLeft;
    case SDL_GAMEPAD_BUTTON_DPAD_UP: return ImGuiKey_GamepadDpadUp;
    case SDL_GAMEPAD_BUTTON_DPAD_DOWN: return ImGuiKey_GamepadDpadDown;
    case SDL_GAMEPAD_BUTTON_DPAD_LEFT: return ImGuiKey_GamepadDpadLeft;
    case SDL_GAMEPAD_BUTTON_DPAD_RIGHT: return ImGuiKey_GamepadDpadRight;
    case SDL_GAMEPAD_BUTTON_LEFT_SHOULDER: return ImGuiKey_GamepadL1;
    case SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER: return ImGuiKey_GamepadR1;
    case SDL_GAMEPAD_BUTTON_START: return ImGuiKey_GamepadStart;
    case SDL_GAMEPAD_BUTTON_BACK: return ImGuiKey_GamepadBack;
    default: return ImGuiKey_None;
    }
}

bool menu_handle_event(const SDL_Event *e) {
    static bool back_down, start_down;
    bool typing = g_open.load() && ui_text_busy();
    switch (e->type) {
    case SDL_EVENT_KEY_DOWN:
        if (!e->key.repeat && (e->key.scancode == SDL_SCANCODE_F1 ||
                               (e->key.scancode == SDL_SCANCODE_ESCAPE && !g_open.load()))) {
            if (!typing) set_open(!g_open.load());  // (Esc with the menu open goes to ImGui below: it backs out)
            return true;
        }
        if (!e->key.repeat && (e->key.scancode == SDL_SCANCODE_F11 ||
                               (e->key.scancode == SDL_SCANCODE_RETURN && (e->key.mod & SDL_KMOD_ALT)))) {
            g_settings.fullscreen = !g_settings.fullscreen;
            g_want_fullscreen_apply.store(true);
            settings_save();
            return true;
        }
        /* fallthrough */
    case SDL_EVENT_KEY_UP: {
        if (!g_open.load()) return false;
        bool down = e->type == SDL_EVENT_KEY_DOWN;
        if (down && e->key.scancode == SDL_SCANCODE_ESCAPE) {  // Esc: back out of popups, else close
            QEvent q = {};
            q.kind = QEvent::KEY; q.key = ImGuiKey_Escape; q.down = true; push(q);
            q.down = false; push(q);
            return true;
        }
        ImGuiKey k = key_from_scancode(e->key.scancode);
        if (k != ImGuiKey_None) { QEvent q = {}; q.kind = QEvent::KEY; q.key = k; q.down = down; push(q); }
        return true;
    }
    case SDL_EVENT_TEXT_INPUT:
        if (!g_open.load()) return false;
        { QEvent q = {}; q.kind = QEvent::TEXT; snprintf(q.text, sizeof q.text, "%s", e->text.text); push(q); }
        return true;
    case SDL_EVENT_GAMEPAD_BUTTON_DOWN: case SDL_EVENT_GAMEPAD_BUTTON_UP: {
        bool down = e->type == SDL_EVENT_GAMEPAD_BUTTON_DOWN;
        if (e->gbutton.button == SDL_GAMEPAD_BUTTON_BACK) back_down = down;
        if (e->gbutton.button == SDL_GAMEPAD_BUTTON_START) start_down = down;
        if (down && !typing && ((back_down && start_down) || e->gbutton.button == SDL_GAMEPAD_BUTTON_GUIDE)) {
            set_open(!g_open.load());
            return true;
        }
        if (!g_open.load()) return false;
        ImGuiKey k = key_from_pad(e->gbutton.button);
        if (k != ImGuiKey_None) { QEvent q = {}; q.kind = QEvent::KEY; q.key = k; q.down = down; push(q); }
        return true;
    }
    case SDL_EVENT_GAMEPAD_AXIS_MOTION: {
        if (!g_open.load()) return false;
        float v = e->gaxis.value / 32767.0f;
        QEvent q = {};
        q.kind = QEvent::ANALOG;
        switch (e->gaxis.axis) {
        case SDL_GAMEPAD_AXIS_LEFTX:
            q.key = ImGuiKey_GamepadLStickLeft; q.value = v < -0.3f ? -v : 0; push(q);
            q.key = ImGuiKey_GamepadLStickRight; q.value = v > 0.3f ? v : 0; push(q);
            break;
        case SDL_GAMEPAD_AXIS_LEFTY:
            q.key = ImGuiKey_GamepadLStickUp; q.value = v < -0.3f ? -v : 0; push(q);
            q.key = ImGuiKey_GamepadLStickDown; q.value = v > 0.3f ? v : 0; push(q);
            break;
        default: break;
        }
        return true;
    }
    case SDL_EVENT_MOUSE_MOTION:
        if (!g_open.load()) return false;
        { QEvent q = {}; q.kind = QEvent::MOUSE_POS; q.x = e->motion.x * g_pixel_density; q.y = e->motion.y * g_pixel_density; push(q); }
        return true;
    case SDL_EVENT_MOUSE_BUTTON_DOWN: case SDL_EVENT_MOUSE_BUTTON_UP:
        if (!g_open.load()) return false;
        {
            QEvent q = {};
            q.kind = QEvent::MOUSE_BUTTON;
            q.button = e->button.button == SDL_BUTTON_LEFT ? 0 : e->button.button == SDL_BUTTON_RIGHT ? 1 : 2;
            q.down = e->type == SDL_EVENT_MOUSE_BUTTON_DOWN;
            push(q);
        }
        return true;
    case SDL_EVENT_MOUSE_WHEEL:
        if (!g_open.load()) return false;
        { QEvent q = {}; q.kind = QEvent::WHEEL; q.x = e->wheel.x; q.y = e->wheel.y; push(q); }
        return true;
    default:
        return false;
    }
}

// The monitors, for the Video tab (main thread fills it; names stay valid while SDL runs).
enum { MAX_DISPLAYS = 8 };
static std::atomic<int> g_ndisplays{0};
static char g_display_names[MAX_DISPLAYS][96];

void menu_apply_window_requests(void *win) {
    SDL_Window *w = (SDL_Window *)win;
    g_pixel_density = SDL_GetWindowPixelDensity(w);
    static bool text_input;
    bool want_text = g_open.load();
    if (want_text != text_input) {
        if (want_text) SDL_StartTextInput(w);
        else SDL_StopTextInput(w);
        text_input = want_text;
    }
    static uint64_t last_list;
    uint64_t now = SDL_GetTicks();
    int nd = 0;
    SDL_DisplayID *ds = SDL_GetDisplays(&nd);
    if (!last_list || now - last_list > 2000) {  // (monitors come and go)
        last_list = now;
        int n = nd < MAX_DISPLAYS ? nd : MAX_DISPLAYS;
        for (int i = 0; i < n; i++) {
            SDL_Rect r = {};
            SDL_GetDisplayBounds(ds[i], &r);
            const char *nm = SDL_GetDisplayName(ds[i]);
            snprintf(g_display_names[i], sizeof g_display_names[i], "%d: %s (%dx%d)", i + 1, nm ? nm : "Display", r.w, r.h);
        }
        g_ndisplays = n;
    }
    if (g_want_display_apply.exchange(false) && ds && g_settings.display >= 1 && g_settings.display <= nd) {
        SDL_DisplayID d = ds[g_settings.display - 1];
        bool fs = g_settings.fullscreen;
        if (fs) SDL_SetWindowFullscreen(w, false);
        SDL_SetWindowPosition(w, SDL_WINDOWPOS_CENTERED_DISPLAY(d), SDL_WINDOWPOS_CENTERED_DISPLAY(d));
        if (fs) SDL_SetWindowFullscreen(w, true);
        LOG("[menu] window -> monitor %d\n", g_settings.display);
    }
    SDL_free(ds);
    static bool first = true;
    if (first || g_want_fullscreen_apply.exchange(false)) {
        bool test = getenv("LARECOMP_WINDOW") || getenv("LARECOMP_HIDDEN");  // (test windows stay windows)
        if (!first || !test) SDL_SetWindowFullscreen(w, g_settings.fullscreen && !(first && test));
        first = false;
    }
}

// ------------------------------------------------------------------ render thread
static bool g_inited;
static ImGuiContext *g_ctx;
static ImFont *g_font, *g_font_big;
static ImFont *g_menu_font, *g_menu_font_big;  // the menu window (Baloo 2); the FPS counter keeps g_font
static int g_tab, g_tab_request = -2;  // (-2: no request)
static int g_focus_tab = -99;  // put the nav cursor on this tab next frame (-100: the selected one; -99: none)
static int g_focus_frames;

enum { TAB_CONTROLS, TAB_VIDEO, TAB_AUDIO, TAB_QUIT, NTABS };
static void menu_tabs_focus(bool first_tab) { g_focus_tab = first_tab ? TAB_CONTROLS : -100, g_focus_frames = 0; }

static void style_init(void) {
    ImGuiStyle &s = ImGui::GetStyle();
    ImGui::StyleColorsDark();
    s.WindowRounding = 14; s.FrameRounding = 8; s.GrabRounding = 8; s.TabRounding = 8; s.ChildRounding = 10;
    s.WindowPadding = ImVec2(28, 24); s.FramePadding = ImVec2(14, 8); s.ItemSpacing = ImVec2(14, 12);
    s.WindowBorderSize = 0; s.ScrollbarSize = 18;
    ImVec4 *c = s.Colors;
    ImVec4 gold(0.93f, 0.76f, 0.33f, 1), gold_dim(0.62f, 0.49f, 0.20f, 1), green(0.15f, 0.36f, 0.25f, 1);
    c[ImGuiCol_WindowBg] = ImVec4(0.06f, 0.09f, 0.08f, 0.94f);
    c[ImGuiCol_ChildBg] = ImVec4(0.09f, 0.13f, 0.11f, 0.85f);
    c[ImGuiCol_PopupBg] = ImVec4(0.07f, 0.10f, 0.09f, 0.98f);
    c[ImGuiCol_Text] = ImVec4(0.96f, 0.94f, 0.88f, 1);
    c[ImGuiCol_TextDisabled] = ImVec4(0.62f, 0.64f, 0.58f, 1);
    c[ImGuiCol_FrameBg] = ImVec4(0.13f, 0.19f, 0.16f, 1);
    c[ImGuiCol_FrameBgHovered] = green;
    c[ImGuiCol_FrameBgActive] = ImVec4(0.19f, 0.45f, 0.31f, 1);
    c[ImGuiCol_Button] = ImVec4(0.14f, 0.22f, 0.18f, 1);
    c[ImGuiCol_ButtonHovered] = green;
    c[ImGuiCol_ButtonActive] = ImVec4(0.21f, 0.50f, 0.34f, 1);
    c[ImGuiCol_Header] = green;
    c[ImGuiCol_HeaderHovered] = ImVec4(0.19f, 0.45f, 0.31f, 1);
    c[ImGuiCol_HeaderActive] = ImVec4(0.21f, 0.50f, 0.34f, 1);
    c[ImGuiCol_Tab] = ImVec4(0.12f, 0.18f, 0.15f, 1);
    c[ImGuiCol_TabHovered] = green;
    c[ImGuiCol_TabSelected] = ImVec4(0.21f, 0.44f, 0.31f, 1);
    c[ImGuiCol_TabSelectedOverline] = gold;
    c[ImGuiCol_CheckMark] = gold;
    c[ImGuiCol_SliderGrab] = gold_dim;
    c[ImGuiCol_SliderGrabActive] = gold;
    c[ImGuiCol_NavCursor] = gold;
    c[ImGuiCol_Separator] = ImVec4(0.30f, 0.36f, 0.30f, 1);
    c[ImGuiCol_TitleBg] = c[ImGuiCol_TitleBgActive] = c[ImGuiCol_WindowBg];
}

// A shipped file: next to pvhost.exe, else in the source tree (dev runs start from the repo root or lab/...).
static bool find_resource(const char *rel, char *out, size_t n) {
    char exe[1024];
    const char *base = SDL_GetBasePath();  // (ends with a separator)
    const char *tries[] = {"%s%s", "%s../../psvrecomp/%s", "%s../../../psvrecomp/%s"};
    for (const char *t : tries) {
        snprintf(exe, sizeof exe, t, base ? base : "", rel);
        if (FILE *f = fopen(exe, "rb")) { fclose(f); snprintf(out, n, "%s", exe); return true; }
    }
    snprintf(exe, sizeof exe, "D:/Dev/REA/psvrecomp/%s", rel);  // (the workspace)
    if (FILE *f = fopen(exe, "rb")) { fclose(f); snprintf(out, n, "%s", exe); return true; }
    return false;
}

static void init(void) {
    IMGUI_CHECKVERSION();
    g_ctx = ImGui::CreateContext();
    ImGui::SetCurrentContext(g_ctx);
    ImGuiIO &io = ImGui::GetIO();
    io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard | ImGuiConfigFlags_NavEnableGamepad;
    io.BackendFlags |= ImGuiBackendFlags_HasGamepad;
    io.IniFilename = NULL;
    ImFontConfig cfg;
    cfg.OversampleH = 2;
    const char *sys = "C:/Windows/Fonts/segoeui.ttf";
    if (FILE *f = fopen(sys, "rb")) {  // (a missing file is an assertion in ImGui, not a NULL return)
        fclose(f);
        g_font = io.Fonts->AddFontFromFileTTF(sys, 34, &cfg);
        g_font_big = io.Fonts->AddFontFromFileTTF(sys, 56, &cfg);
    }
    char baloo[1024];
    if (find_resource("third_party/fonts/Baloo2/Baloo2-SemiBold.ttf", baloo, sizeof baloo)) {
        g_menu_font = io.Fonts->AddFontFromFileTTF(baloo, 39, &cfg);
        g_menu_font_big = io.Fonts->AddFontFromFileTTF(baloo, 72, &cfg);
    }
    if (!g_font) g_font = io.Fonts->AddFontDefault();
    if (!g_font_big) g_font_big = g_font;
    if (!g_menu_font || !g_menu_font_big) g_menu_font = g_font, g_menu_font_big = g_font_big;
    style_init();
    vk_imgui_backend_init();
    g_inited = true;
}

static void drain_events(ImGuiIO &io) {
    pthread_mutex_lock(&q_lock);
    std::vector<QEvent> ev;
    ev.swap(q_events);
    pthread_mutex_unlock(&q_lock);
    for (const QEvent &q : ev) {
        switch (q.kind) {
        case QEvent::KEY: io.AddKeyEvent(q.key, q.down); break;
        case QEvent::ANALOG: io.AddKeyAnalogEvent(q.key, q.value > 0.1f, q.value); break;
        case QEvent::MOUSE_POS: io.AddMousePosEvent(q.x, q.y); break;
        case QEvent::MOUSE_BUTTON: io.AddMouseButtonEvent(q.button, q.down); break;
        case QEvent::WHEEL: io.AddMouseWheelEvent(q.x, q.y); break;
        case QEvent::TEXT: io.AddInputCharactersUTF8(q.text); break;
        }
    }
}

// ------------------------------------------------------------------ pages
// Controls: the layout (runtime/hle/input.c), as rows - nothing to change here yet.
static void tab_controls(float scale) {
    opt_begin("##controls", scale);
    opt_section("Keyboard");
    static const struct { const char *what, *keys; } kb[] = {
        {"Move", "W A S D"},          {"Camera", "Numpad 8 4 5 6"},  {"A (confirm)", "K / Space"},
        {"B (back)", "J"},            {"X", "I"},                    {"Y", "L"},
        {"L / R", "Q / E"},           {"ZL / ZR", "1 / 3"},          {"+ (Plus)", "Enter"},
        {"- (Minus)", "Backspace"},   {"D-pad", "Arrow keys"},       {"Stick clicks", "F / R"},
    };
    for (auto &k : kb) opt_action(k.what, k.keys, "The keyboard layout (LAS Recomp's, plus Space for A).");
    opt_section("Controller");
    static const struct { const char *what, *keys; } pad[] = {
        {"A / B / X / Y", "By position, Switch layout"}, {"L / R", "Shoulders"}, {"ZL / ZR", "Triggers"},
        {"+ / -", "Start / Back"},
    };
    for (auto &k : pad)
        opt_action(k.what, k.keys, "Any controller works, buttons by position as on a Switch: right = A, bottom = B, "
                                   "top = X, left = Y.");
    opt_section("This menu");
    opt_action("Open / close", "F1, Esc", "Or the controller's Home / Xbox / PlayStation button, or Back + Start.");
    opt_action("Switch tabs", "L / R  (Q / E)", "");
    opt_action("Back", "B  (Esc, J)", "");
    opt_action("Fullscreen", "F11 / Alt+Enter", "");
    opt_end();
}

static void tab_video(float scale) {
    opt_begin("##video", scale);
    opt_section("Display");
    bool fs = g_settings.fullscreen;
    if (opt_toggle("Fullscreen", &fs, false, "Fills the screen. Also: F11 or Alt+Enter.")) {
        g_settings.fullscreen = fs;
        g_want_fullscreen_apply.store(true);
    }
    {
        int nd = g_ndisplays.load();
        const char *names[MAX_DISPLAYS + 1];
        names[0] = "Default";
        for (int i = 0; i < nd; i++) names[i + 1] = g_display_names[i];
        int v = g_settings.display >= 0 && g_settings.display <= nd ? g_settings.display : 0;
        if (opt_choice("Monitor", &v, names, nd + 1, 0,
                       "Which monitor the game opens on. Default: where Windows puts it. Moves the window now.", false)) {
            g_settings.display = v;
            if (v) g_want_display_apply.store(true);
        }
    }
    if (opt_toggle("VSync", &g_settings.vsync, false,
                   "On: waits for the monitor's refresh before showing each frame (classic vsync). Off: shows the newest "
                   "frame at the next refresh without waiting (no tearing either). The game runs at 30 fps both ways; Off "
                   "keeps it smoother when the desktop is busy."))
        ui_request_swapchain();
    opt_toggle("Show FPS", &g_settings.show_fps, false, "Shows the frame rate in the top right corner.");

    opt_section("Rendering");
    static const char *res[] = {"25%", "50%", "75%", "Match display", "Dynamic", "1x", "2x", "3x", "4x"};
    static const int res_mode[] = {RES_Q25, RES_Q50, RES_Q75, RES_MATCH, RES_DYNAMIC, 1, 2, 3, 4};
    enum { RES_MATCH_AT = 3, NRES = sizeof res_mode / sizeof res_mode[0] };
    {
        int ri = RES_MATCH_AT;
        for (int i = 0; i < NRES; i++) if (res_mode[i] == g_settings.res_mode) ri = i;
        float sx, sy;
        renderer_get_scale(&sx, &sy);
        char d[400];
        int n = snprintf(d, sizeof d, "How sharp the 3D image is. Match display: your screen's own resolution. Dynamic: "
                                      "as sharp as your GPU keeps at full speed. 1x-4x: the Switch's 1080p times that. "
                                      "75%% / 50%% / 25%%: a share of the display, for slower machines.\n\nRendering at "
                                      "%.0f x %.0f.", 1920.0 * sx, 1080.0 * sy);
        if (g_settings.res_mode == RES_DYNAMIC)
            snprintf(d + n, sizeof d - n, " Dynamic: %.0f%% of the display right now.", output_scale_dynamic_factor() * 100);
        if (opt_choice("Internal resolution", &ri, res, NRES, RES_MATCH_AT, d, false)) g_settings.res_mode = res_mode[ri];
    }
    {
        static const char *ups[] = {"Bilinear", "AMD FSR 1"};
        const char *ud = "How the image is scaled up to the window when it renders at a lower resolution. AMD FSR 1: "
                         "edge-aware upscaling and sharpening, sharper. Bilinear: plain and soft.";
        int ui = g_settings.upscaler == UPSCALE_BILINEAR ? 0 : 1;
        char udm[512];
        if (g_settings.res_mode == RES_MATCH) {
            snprintf(udm, sizeof udm, "%s\n\nNot used at Match display: the game already renders at your display's resolution.", ud);
            ud = udm;
            opt_disable_next();
        }
        if (opt_choice("Upscaler", &ui, ups, 2, 1, ud)) g_settings.upscaler = ui ? UPSCALE_SHARP : UPSCALE_BILINEAR;
    }
    static const char *aa[] = {"Off", "SMAA"};
    opt_choice("Anti-aliasing", &g_settings.antialias, aa, 2, AA_OFF,
               "Smooths jagged edges of the game image before it is scaled to the window. SMAA: finds the edges and "
               "blends only along them, so textures stay sharp. Most useful at a lower internal resolution.");
    opt_end();
}

static void tab_audio(float scale) {
    opt_begin("##audio", scale);
    opt_section("Sound");
    float pct = roundf(g_settings.volume * 100);
    if (opt_slider("Volume", &pct, 0, 200, 5, 100, "%g%%", "The game's volume. 100% is the game's own level; above it, louder."))
        g_settings.volume = pct / 100.0f;
    opt_end();
}

// Quit: out to the desktop, after asking (progress since the last save is lost). B / Esc or Cancel backs out.
static void tab_quit(float scale) {
    static bool ask;
    if (ask && (ImGui::IsKeyPressed(ImGuiKey_GamepadFaceRight, false) || ImGui::IsKeyPressed(ImGuiKey_Escape, false)))
        ask = false;
    const char *d = "Closes PSV Recomp.\n\nProgress since your last save is lost: save in the game first.";
    opt_begin("##quit", scale);
    opt_section("Quit");
    if (!ask) {
        if (opt_action("Quit to Desktop", "", d)) ask = true;
    } else {
        if (opt_action("Yes, quit to Desktop", "", d)) {
            settings_save();
            SDL_Event q = {};
            q.type = SDL_EVENT_QUIT;
            SDL_PushEvent(&q);
            ask = false;
        }
        if (opt_action("Cancel", "", "Stays in the game.")) ask = false;
    }
    opt_end();
}

static void tabs_body(float scale) {
    static const char *names[NTABS] = {"Controls", "Video", "Audio", "Quit"};
    int cur = g_tab;
    if (g_tab_request_ext >= 0) { g_tab_request = g_tab_request_ext; g_tab_request_ext = -1; }
    bool any_popup = ImGui::IsPopupOpen("", ImGuiPopupFlags_AnyPopupId), typing = ui_text_busy();
    static int focused_tab = -99;  // the tab the controller's cursor is on (from the frame before; -99: none)
    if (!any_popup && !typing) {
        int step = ImGui::IsKeyPressed(ImGuiKey_GamepadR1, false) || ImGui::IsKeyPressed(ImGuiKey_E, false) ? 1
                 : ImGui::IsKeyPressed(ImGuiKey_GamepadL1, false) || ImGui::IsKeyPressed(ImGuiKey_Q, false) ? -1 : 0;
        if (step) {
            g_tab_request = (cur + step + NTABS) % NTABS;
            if (focused_tab != -99) g_focus_tab = g_tab_request, g_focus_frames = 0;  // (the cursor on the tab bar goes along)
        }
    }
    // Down with the cursor on the tab bar: the page's first row
    bool down_from_tab = focused_tab != -99 && ImGui::GetCurrentContext()->NavCursorVisible && !any_popup &&
                         (ImGui::IsKeyPressed(ImGuiKey_GamepadDpadDown) || ImGui::IsKeyPressed(ImGuiKey_GamepadLStickDown) ||
                          ImGui::IsKeyPressed(ImGuiKey_DownArrow));
    opt_focus_first(down_from_tab);
    if (ImGui::BeginTabBar("##tabs", ImGuiTabBarFlags_NoTabListScrollingButtons)) {
        for (int t = 0; t < NTABS; t++) {
            ImGuiTabItemFlags f = g_tab_request == t ? ImGuiTabItemFlags_SetSelected : 0;
            char lbl[64];
            snprintf(lbl, sizeof lbl, "  %s  ", names[t]);
            // focus: the tab lights up with a gold bar along its bottom instead of ImGui's outline (LAS)
            bool lit = focused_tab == t && ImGui::GetCurrentContext()->NavCursorVisible;
            ImGui::PushStyleColor(ImGuiCol_NavCursor, ImVec4(0, 0, 0, 0));
            if (lit) {
                ImGui::PushStyleColor(ImGuiCol_Tab, ImVec4(0.19f, 0.27f, 0.22f, 1));
                ImGui::PushStyleColor(ImGuiCol_TabHovered, ImVec4(0.19f, 0.27f, 0.22f, 1));
            }
            bool focus_here = g_focus_tab == t || (g_focus_tab == -100 && t == g_tab);
            bool open = ImGui::BeginTabItem(lbl, NULL, f);
            ImGui::PopStyleColor(lit ? 3 : 1);
            if (focus_here) {  // the controller's cursor starts on this tab (a few frames: the page lays out first)
                ImGui::SetFocusID(ImGui::GetItemID(), ImGui::GetCurrentWindow());
                ImGui::SetNavCursorVisible(true);
                if (++g_focus_frames >= 4) g_focus_tab = -99, g_focus_frames = 0;
                else g_focus_tab = t;
            }
            if (lit) {
                ImVec2 a = ImGui::GetItemRectMin(), b = ImGui::GetItemRectMax();
                float h = 4 * scale > 2 ? 4 * scale : 2;
                ImGui::GetWindowDrawList()->AddRectFilled(ImVec2(a.x + 2, b.y - h), ImVec2(b.x - 2, b.y), IM_COL32(236, 194, 84, 255));
            }
            if (ImGui::IsItemFocused()) focused_tab = t;
            else if (focused_tab == t) focused_tab = -99;
            if (open) {
                g_tab = t;
                ImGui::Spacing();
                ImGui::BeginChild("##page", ImVec2(0, 0), ImGuiChildFlags_None, ImGuiWindowFlags_NavFlattened);
                switch (t) {
                case TAB_CONTROLS: tab_controls(scale); break;
                case TAB_VIDEO: tab_video(scale); break;
                case TAB_AUDIO: tab_audio(scale); break;
                case TAB_QUIT: tab_quit(scale); break;
                }
                ImGui::EndChild();
                ImGui::EndTabItem();
            }
        }
        g_tab_request = -2;
        opt_focus_first(false);
        ImGui::EndTabBar();
    }
}

void menu_render(void *cmd, uint32_t target_w, uint32_t target_h) {
    const double tw = target_w, th = target_h;
    bool open = g_open.load();
    if (!open && !g_settings.show_fps) {
        if (g_inited) { pthread_mutex_lock(&q_lock); q_events.clear(); pthread_mutex_unlock(&q_lock); }
        return;
    }
    if (!g_inited) init();
    ImGui::SetCurrentContext(g_ctx);
    ImGuiIO &io = ImGui::GetIO();
    io.DisplaySize = ImVec2((float)tw, (float)th);
    io.DisplayFramebufferScale = ImVec2(1, 1);
    static double last;
    double now = SDL_GetTicks() / 1000.0;
    io.DeltaTime = last > 0 && now > last ? (float)(now - last) : 1.0f / 60;
    last = now;
    drain_events(io);
    // fonts are built for a ~1080 px tall output; scale to the window
    float scale = (float)(th / 1080.0);
    if (scale < 0.45f) scale = 0.45f;
    io.FontGlobalScale = scale;
    static ImGuiStyle base;
    static float style_scale = -1;
    if (style_scale < 0) base = ImGui::GetStyle();
    if (fabsf(style_scale - scale) > 0.01f) {
        ImGui::GetStyle() = base;
        ImGui::GetStyle().ScaleAllSizes(scale);
        style_scale = scale;
    }
    ImGui_ImplVulkan_NewFrame();
    ImGui::NewFrame();

    if (g_settings.show_fps) {
        ImGui::SetNextWindowPos(ImVec2(io.DisplaySize.x - 16 * scale, 16 * scale), 0, ImVec2(1, 0));
        ImGui::SetNextWindowBgAlpha(0.5f);
        ImGui::Begin("##fps", NULL, ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_AlwaysAutoResize |
                                        ImGuiWindowFlags_NoInputs | ImGuiWindowFlags_NoNav | ImGuiWindowFlags_NoFocusOnAppearing);
        int f10 = g_title_fps10_get();  // (the game's frames, not the menu's redraws)
        if (f10 >= 0) ImGui::Text("%d fps", (f10 + 5) / 10);
        else ImGui::Text("%.0f fps", io.Framerate);
        ImGui::End();
    }

    if (open) {
        ImGui::GetBackgroundDrawList()->AddRectFilled(ImVec2(0, 0), io.DisplaySize, IM_COL32(0, 0, 0, 110));  // dim the game
        float w = fminf(io.DisplaySize.x * 0.9f, 1500 * scale), h = io.DisplaySize.y - 2 * 18 * scale;
        ImGui::SetNextWindowPos(ImVec2(io.DisplaySize.x * 0.5f, io.DisplaySize.y * 0.5f), ImGuiCond_Always, ImVec2(0.5f, 0.5f));
        ImGui::SetNextWindowSize(ImVec2(w, h), ImGuiCond_Always);
        ImGui::Begin("##menu", NULL, ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_NoMove | ImGuiWindowFlags_NoSavedSettings);
        ImGui::PushFont(g_menu_font);
        ImGui::PushFont(g_menu_font_big);
        ImGui::TextColored(ImVec4(0.93f, 0.76f, 0.33f, 1), "Settings");
        ImGui::PopFont();
        {  // a close X in the corner (B / Esc too)
            float bx = 44 * scale;
            ImGui::SameLine(ImGui::GetWindowWidth() - ImGui::GetStyle().WindowPadding.x - bx);
            ImVec2 p = ImGui::GetCursorScreenPos();
            ImGui::PushStyleColor(ImGuiCol_NavCursor, ImVec4(0, 0, 0, 0));
            bool close = ImGui::InvisibleButton("##close", ImVec2(bx, bx), ImGuiButtonFlags_EnableNav);
            ImGui::PopStyleColor();
            bool hot = ImGui::IsItemHovered() || ImGui::IsItemFocused();
            ImU32 col = hot ? IM_COL32(236, 194, 84, 255) : IM_COL32(220, 216, 205, 255);
            float m = bx * 0.3f, t = (hot ? 3.0f : 2.4f) * scale * 1.5f;
            ImDrawList *dl = ImGui::GetWindowDrawList();
            if (hot) dl->AddRectFilled(p, ImVec2(p.x + bx, p.y + bx), IM_COL32(255, 255, 255, 20), 8 * scale);
            dl->AddLine(ImVec2(p.x + m, p.y + m), ImVec2(p.x + bx - m, p.y + bx - m), col, t);
            dl->AddLine(ImVec2(p.x + bx - m, p.y + m), ImVec2(p.x + m, p.y + bx - m), col, t);
            if (close) set_open(false);
        }
        bool any_popup = ImGui::IsPopupOpen("", ImGuiPopupFlags_AnyPopupId), typing = ui_text_busy();
        tabs_body(scale);
        // B with nothing deeper focused closes the menu
        if (!any_popup && !typing && !ui_text_busy() && ImGui::IsWindowFocused(ImGuiFocusedFlags_RootAndChildWindows) &&
            (ImGui::IsKeyPressed(ImGuiKey_GamepadFaceRight, false) || ImGui::IsKeyPressed(ImGuiKey_Escape, false)))
            set_open(false);
        ImGui::PopFont();
        ImGui::End();
        osk_draw(g_font_big, scale);
    }
    ImGui::Render();
    ImGui_ImplVulkan_RenderDrawData(ImGui::GetDrawData(), (VkCommandBuffer)cmd);  // inside the window image's rendering
}
