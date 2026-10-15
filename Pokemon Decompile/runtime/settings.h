// PVRecomp headless settings: the subset of LAS Recomp's settings.h the ported services read (audio.c).
// LAS keeps these in a settings file edited from its start screen; headless uses fixed defaults.
#pragma once
#include <stdbool.h>

typedef struct {
    float volume;  // master volume, 1 = 100%
    bool reverb;   // room reverb effect
} Settings;

extern Settings g_settings;
