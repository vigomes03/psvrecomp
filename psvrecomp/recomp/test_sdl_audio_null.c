// Acceptance test for card W04 (runtime/platform/sdl_audio_null.h).
#include <stdio.h>

#include "sdl_audio_null.h"
#include "sdl_audio_null.h"  // twice: #pragma once

int main(void) {
    int fails = 0;
#define CHECK(c) do { if (!(c)) { printf("FAIL %s\n", #c); fails++; } } while (0)
    CHECK(!SDL_InitSubSystem(SDL_INIT_AUDIO));
    CHECK(SDL_GetCurrentAudioDriver() == NULL);
    SDL_AudioSpec spec = {SDL_AUDIO_F32, 2, 48000};
    CHECK(sizeof(SDL_AudioSpec) == 12);
    CHECK(spec.format == SDL_AUDIO_F32 && spec.channels == 2 && spec.freq == 48000);
    SDL_AudioStream *s = SDL_OpenAudioDeviceStream(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK, &spec, NULL, NULL);
    CHECK(s == NULL);
    CHECK(SDL_GetAudioStreamQueued(NULL) == 0);
    CHECK(SDL_GetError() != NULL);
    SDL_AudioSpec dev;
    int frames = 0;
    CHECK(!SDL_GetAudioDeviceFormat(SDL_GetAudioStreamDevice(s), &dev, &frames));
    CHECK(SDL_GetAudioStreamGain(s) == 1.0f);
    SDL_DestroyAudioStream(s);
    printf(fails ? "W04 FAIL (%d)\n" : "W04 PASS\n", fails);
    return fails != 0;
}
