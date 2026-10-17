// (PVRecomp) Frame-time recorder: how regular the frames are, and what each spike was spent on.
// Fed once per presented frame by framepace_present (after its pacing sleep). Per frame it keeps the present-to-present
// time, the pacing sleep, and the backend's counters for that frame (renderer_frame_counters: command-list execution,
// GPU waits, texture/buffer upload bytes, shader compiles started, draws skipped because a shader was still compiling).
// Log lines:
//   [frametime] 10 s: ...   every 10 s of play (PVR_FRAMETIME_EVERY=<s> to change, 0 = off)
//   [frametime] RUN: ...    the whole run, at exit (time limit or window closed)
// A spike is a frame longer than 1.5x the paced period (50 ms at 30 fps). Its cause is the first that applies:
//   shader  a compile started or a draw waited for one in that frame
//   upload  >= 16 MB uploaded in that frame
//   gpu     the backend waited on the GPU for >= half of the frame's work time
//   game    the rest (the game's own CPU work / its threads)
// PVR_FRAMETIME_CSV=<path>: one row per frame (frame, dt, sleep, exec, wait, upload_mb, compiles, pending).
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "platform.h"
#include "rt.h"

void renderer_frame_counters(uint64_t out[5]);  // backend: cumulative exec ns, wait ns, upload bytes, compiles, pending skips

typedef struct { float dt, sleep, exec, wait, upload_mb; uint16_t compiles, pending; } FtRec;
static FtRec *rec;
static size_t nrec, caprec, win_start;
static uint64_t last_ns, last_c[5], period_ns = 33333333ull, win_t0;
static int every_s = -1;

static int cmpf(const void *a, const void *b) {
    float x = *(const float *)a, y = *(const float *)b;
    return x < y ? -1 : x > y;
}

static void summary(const char *label, size_t from, size_t to) {
    size_t n = to - from;
    if (n < 2) return;
    float *d = malloc(n * sizeof *d);
    double sum = 0, work = 0;
    int sp[4] = {0}, nsp = 0;
    float thr = (float)(period_ns * 1.5 / 1e6);
    for (size_t i = 0; i < n; i++) {
        const FtRec *r = &rec[from + i];
        d[i] = r->dt;
        sum += r->dt;
        work += r->dt - r->sleep;
        if (r->dt <= thr) continue;
        nsp++;
        float w = r->dt - r->sleep;
        if (r->compiles || r->pending) sp[0]++;
        else if (r->upload_mb >= 16) sp[1]++;
        else if (r->wait >= 0.5f * w) sp[2]++;
        else sp[3]++;
    }
    qsort(d, n, sizeof *d, cmpf);
    size_t k = n / 100 ? n / 100 : 1;  // worst 1%
    double worst = 0;
    for (size_t i = n - k; i < n; i++) worst += d[i];
    worst /= (double)k;
    LOG("[frametime] %s: %zu frames, avg %.1f ms (%.1f fps), p50 %.1f p95 %.1f p99 %.1f max %.1f ms, 1%% low %.1f fps, "
        "work avg %.1f ms | spikes >%.0f ms: %d (shader %d, upload %d, gpu %d, game %d)\n",
        label, n, sum / n, 1000.0 * n / sum, d[n / 2], d[n * 95 / 100], d[n * 99 / 100], d[n - 1], 1000.0 / worst, work / n,
        thr, nsp, sp[0], sp[1], sp[2], sp[3]);
    free(d);
}

static void write_csv(void) {
    const char *path = getenv("PVR_FRAMETIME_CSV");
    if (!path || !nrec) return;
    FILE *f = fopen(path, "w");
    if (!f) return;
    fprintf(f, "frame,dt_ms,sleep_ms,exec_ms,gpu_wait_ms,upload_mb,compiles,pending\n");
    for (size_t i = 0; i < nrec; i++)
        fprintf(f, "%zu,%.3f,%.3f,%.3f,%.3f,%.2f,%u,%u\n", i, rec[i].dt, rec[i].sleep, rec[i].exec, rec[i].wait, rec[i].upload_mb,
                rec[i].compiles, rec[i].pending);
    fclose(f);
}

static int final_done;
void frametime_final(void) {  // time limit (main.c) or window closed (atexit)
    if (final_done++ || !nrec) return;
    summary("RUN", 0, nrec);
    write_csv();
    fflush(stderr);
}

void frametime_frame(uint64_t sleep_ns, uint64_t period) {
    uint64_t now = plat_now_ns(), c[5];
    renderer_frame_counters(c);
    if (period) period_ns = period;
    if (every_s < 0) {
        every_s = getenv("PVR_FRAMETIME_EVERY") ? atoi(getenv("PVR_FRAMETIME_EVERY")) : 10;
        atexit(frametime_final);
    }
    if (last_ns) {
        if (nrec == caprec) {
            caprec = caprec ? caprec * 2 : 1 << 14;
            rec = realloc(rec, caprec * sizeof *rec);
        }
        FtRec *r = &rec[nrec++];
        r->dt = (float)((now - last_ns) / 1e6);
        r->sleep = (float)(sleep_ns / 1e6);
        r->exec = (float)((c[0] - last_c[0]) / 1e6);
        r->wait = (float)((c[1] - last_c[1]) / 1e6);
        r->upload_mb = (float)((c[2] - last_c[2]) / 1048576.0);
        r->compiles = (uint16_t)(c[3] - last_c[3] > 65535 ? 65535 : c[3] - last_c[3]);
        r->pending = (uint16_t)(c[4] - last_c[4] > 65535 ? 65535 : c[4] - last_c[4]);
    } else {
        win_t0 = now;
    }
    last_ns = now;
    memcpy(last_c, c, sizeof c);
    if (every_s > 0 && now - win_t0 >= (uint64_t)every_s * 1000000000ull) {
        char label[32];
        snprintf(label, sizeof label, "%d s", every_s);
        summary(label, win_start, nrec);
        win_start = nrec;
        win_t0 = now;
    }
}
