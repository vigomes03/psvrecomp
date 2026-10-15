#pragma once

#include <stdbool.h>
#include <stdint.h>

typedef struct SDL_AudioStream SDL_AudioStream;
typedef uint32_t SDL_AudioDeviceID;
typedef enum {
    SDL_AUDIO_UNKNOWN = 0,
    SDL_AUDIO_S16 = 0x8010,
    SDL_AUDIO_F32 = 0x8120
} SDL_AudioFormat;

typedef struct {
    SDL_AudioFormat format;
    int channels;
    int freq;
} SDL_AudioSpec;

#define SDL_INIT_AUDIO 0x00000010u
#define SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK ((SDL_AudioDeviceID)0xFFFFFFFFu)

static inline bool SDL_InitSubSystem(uint32_t flags) {
    (void)flags;
    return false;
}

static inline const char *SDL_GetError(void) {
    return "headless build: no audio device";
}

static inline SDL_AudioStream *SDL_OpenAudioDeviceStream(SDL_AudioDeviceID devid, const SDL_AudioSpec *spec, void *callback, void *userdata) {
    (void)devid;
    (void)spec;
    (void)callback;
    (void)userdata;
    return NULL;
}

static inline bool SDL_ResumeAudioStreamDevice(SDL_AudioStream *stream) {
    (void)stream;
    return false;
}

static inline void SDL_DestroyAudioStream(SDL_AudioStream *stream) {
    (void)stream;
}

static inline SDL_AudioDeviceID SDL_GetAudioStreamDevice(SDL_AudioStream *stream) {
    (void)stream;
    return 0;
}

static inline bool SDL_GetAudioDeviceFormat(SDL_AudioDeviceID devid, SDL_AudioSpec *spec, int *sample_frames) {
    (void)devid;
    (void)spec;
    (void)sample_frames;
    return false;
}

static inline int SDL_GetAudioStreamQueued(SDL_AudioStream *stream) {
    (void)stream;
    return 0;
}

static inline bool SDL_PutAudioStreamData(SDL_AudioStream *stream, const void *buf, int len) {
    (void)stream;
    (void)buf;
    (void)len;
    return false;
}

static inline float SDL_GetAudioStreamGain(SDL_AudioStream *stream) {
    (void)stream;
    return 1.0f;
}

static inline bool SDL_SetAudioStreamGain(SDL_AudioStream *stream, float gain) {
    (void)stream;
    (void)gain;
    return false;
}
