// (PVRecomp) Present pacing: the game's clock follows its frames, so it must not present faster than the Switch.
// On the Switch, nvnQueuePresentTexture with present interval N shows each image for N vsyncs (60 Hz) and the
// next window-texture acquire blocks until one is free, which caps the game at 60/N fps. Our present returned at
// once (mailbox swapchain), so light scenes (menus, loading) ran at 200-300 fps and the game sped up with them.
// framepace_present() waits until N x 16.67 ms have passed since the previous present.
//   PVR_FRAMEPACE=0       off (the old behaviour)
//   PVR_FPS_CAP=<fps>     use this rate instead of 60/interval (experiments: goal 3, 60 fps)
// A frame that comes in late is not "caught up" with shorter later frames: the schedule restarts from it, as the
// hardware does (a late present lands on the next vsync).
#include <stdint.h>
#include <stdlib.h>

#include "platform.h"
#include "rt.h"

void framepace_present(int interval) {
    static int on = -1;
    static uint64_t fixed_period;
    if (on < 0) {
        const char *e = getenv("PVR_FRAMEPACE");
        on = !e || atoi(e) != 0;
        e = getenv("PVR_FPS_CAP");
        if (e && atof(e) > 0) fixed_period = (uint64_t)(1e9 / atof(e));
    }
    static int last_interval = -1;
    if (interval != last_interval) {
        LOG("[framepace] present interval %d (%s)\n", interval, on ? "paced" : "PVR_FRAMEPACE=0: not paced");
        last_interval = interval;
    }
    if (!on || (interval <= 0 && !fixed_period)) return;
    uint64_t period = fixed_period ? fixed_period : (uint64_t)interval * 16666667ull;
    static uint64_t next;  // earliest time for this present
    uint64_t now = plat_now_ns();
    if (next && now < next) {
        plat_sleep_until_ns(next);
        now = plat_now_ns();
    }
    // on time: keep the grid (no drift); more than half a period late: restart the grid from now
    next = (next && now < next + period / 2 ? next : now) + period;
}
