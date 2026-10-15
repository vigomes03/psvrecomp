# W04 — null SDL3 audio shim for the headless host (`runtime/platform/sdl_audio_null.h`)

## Goal
`runtime/services/audio.c` (ported from LAS Recomp) implements the Switch audio services and plays sound through SDL3.
The PVRecomp host is headless and does not link SDL. Write ONE header that replaces `#include <SDL3/SDL.h>` and
provides exactly the SDL3 audio subset audio.c uses, as a **null device**: initialization fails cleanly, so audio.c
takes its existing no-device paths (it already handles `stream == NULL`: it paces itself with the clock).

Output: ONE C header, `sdl_audio_null.h`. C11, must compile with clang `-Wall -Werror` (unused static functions must
not warn: declare every function `static inline`).

## What audio.c uses (complete list, with the exact SDL3 shapes)
Types:
- `SDL_AudioStream` — opaque: `typedef struct SDL_AudioStream SDL_AudioStream;` (never defined).
- `SDL_AudioDeviceID` — `typedef uint32_t SDL_AudioDeviceID;`
- `SDL_AudioFormat` — `typedef enum { SDL_AUDIO_UNKNOWN = 0, SDL_AUDIO_S16 = 0x8010, SDL_AUDIO_F32 = 0x8120 } SDL_AudioFormat;`
- `SDL_AudioSpec` — `typedef struct { SDL_AudioFormat format; int channels; int freq; } SDL_AudioSpec;`
  (field order matters: audio.c writes `SDL_AudioSpec spec = {SDL_AUDIO_F32, 2, rate};`)
Macros:
- `SDL_INIT_AUDIO` = `0x00000010u`
- `SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK` = `((SDL_AudioDeviceID)0xFFFFFFFFu)`
Functions (all `static inline`, behaviour = null device):
- `bool SDL_InitSubSystem(uint32_t flags)` → returns `false`
- `const char *SDL_GetError(void)` → returns `"headless build: no audio device"`
- `SDL_AudioStream *SDL_OpenAudioDeviceStream(SDL_AudioDeviceID devid, const SDL_AudioSpec *spec, void *callback, void *userdata)` → returns `NULL`
- `bool SDL_ResumeAudioStreamDevice(SDL_AudioStream *stream)` → `false`
- `void SDL_DestroyAudioStream(SDL_AudioStream *stream)` → nothing
- `SDL_AudioDeviceID SDL_GetAudioStreamDevice(SDL_AudioStream *stream)` → `0`
- `bool SDL_GetAudioDeviceFormat(SDL_AudioDeviceID devid, SDL_AudioSpec *spec, int *sample_frames)` → `false`
- `int SDL_GetAudioStreamQueued(SDL_AudioStream *stream)` → `0`
- `bool SDL_PutAudioStreamData(SDL_AudioStream *stream, const void *buf, int len)` → `false`
- `float SDL_GetAudioStreamGain(SDL_AudioStream *stream)` → `1.0f`
- `bool SDL_SetAudioStreamGain(SDL_AudioStream *stream, float gain)` → `false`
Every unused parameter: `(void)name;`. Include `<stdbool.h>` and `<stdint.h>`. Use `#pragma once`.
Nothing else: no other SDL names, no globals, no includes of SDL.

## Acceptance (checked by script)
A test includes the header twice (pragma once), compiles with `-Wall -Werror`, and checks: `SDL_InitSubSystem` is
false, `SDL_OpenAudioDeviceStream` is NULL, `sizeof(SDL_AudioSpec) == 12`, `{SDL_AUDIO_F32, 2, 48000}` puts 2 in
`.channels` and 48000 in `.freq`, `SDL_GetAudioStreamQueued(NULL) == 0`. Then `runtime/services/audio.c` compiles
with it.
