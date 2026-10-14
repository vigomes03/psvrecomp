"""Run a command and report wall time + peak RSS of the process tree (Windows/Linux). Usage: measure.py <cmd...>"""
import json, subprocess, sys, time
import psutil

t0 = time.time()
p = subprocess.Popen(sys.argv[1:])
proc = psutil.Process(p.pid)
peak = 0
while p.poll() is None:
    try:
        rss = proc.memory_info().rss + sum(c.memory_info().rss for c in proc.children(recursive=True))
        peak = max(peak, rss)
    except psutil.Error:
        pass
    time.sleep(0.5)
print(json.dumps({"exit": p.returncode, "seconds": round(time.time() - t0, 1), "peak_rss_mb": round(peak / 2**20)}),
      file=sys.stderr)
sys.exit(p.returncode)
