"""
Batch runner: runs scripts/launcher.py once per research question, back to
back, so a full RQ1-RQ4 sweep can be kicked off before going to bed and
checked on in the morning.

Progress and subprocess output are logged (with timestamps) to both the
console and experiments/logs/<timestamp>.log. If a run fails, it's recorded
and the batch moves on to the next research question rather than aborting
the whole night.

Run with: python scripts/run_batch.py                simulations only
          python scripts/run_batch.py --analyze       simulations + analysis
"""

import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.paths import BASE_DIR

# Jobs to run tonight: (research_question, design_yaml)
# RQ4 is left out until experiments/rq4/design.yaml exists.
JOBS = [
    ("RQ1", BASE_DIR / "experiments" / "rq1" / "design.yaml"),
    ("RQ2", BASE_DIR / "experiments" / "rq2" / "design.yaml"),
    ("RQ3", BASE_DIR / "experiments" / "rq3" / "design.yaml"),
]

# 1. One timestamped log file per batch run
logs_dir = BASE_DIR / "experiments" / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
log_path = logs_dir / f"{datetime.now():%Y%m%d_%H%M%S}.log"

# 2. Log to console and file simultaneously, timestamped per line
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
)
log = logging.getLogger("run_batch")


def main():
    # 3. Track outcome of each research question to print a summary at the end
    results = []

    for research_question, design_path in JOBS:
        log.info("=== %s ===", research_question)

        # 4. Skip research questions whose design YAML hasn't been written yet
        if not design_path.exists():
            log.info("SKIPPED: %s not found", design_path)
            results.append((research_question, "SKIPPED"))
            continue

        # 5. Run launcher.py for this research question. Passing the research
        # question to launcher.py also makes it run the analysis afterwards
        # (see launcher.py's own usage docstring), so only pass it when
        # --analyze was given.
        cmd = [
            sys.executable,
            str(BASE_DIR / "scripts" / "launcher.py"),
            str(design_path),
        ]
        if "--analyze" in sys.argv:
            cmd.append(research_question)

        # 6. Start another program, and give me an object that lets me interact with it
        # while it's running
        # Normally when a program prints something it goes to the terminal, 
        # with stdout=subprocess.PIPE we are asking it to dont print it but give it to us
        process = subprocess.Popen(
            cmd, cwd=BASE_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        # 6. Stream launcher.py's output through the logger (console + file)
        for line in process.stdout:
            log.info(line.rstrip())
            
        # Pause this Python program until the subprocess has finished running
        process.wait()

        # 7. Record outcome and move on to the next research question,
        # even on failure, so one bad run doesn't block the rest of the batch
        status = "OK" if process.returncode == 0 else f"FAILED (exit {process.returncode})"
        log.info("%s: %s", research_question, status)
        results.append((research_question, status))

    # 8. Final summary of the whole batch
    log.info("=== Batch summary ===")
    for research_question, status in results:
        log.info("%s: %s", research_question, status)


if __name__ == "__main__":
    main()