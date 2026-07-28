"""
Batch runner: runs scripts/launcher.py once per research question, back to
back, so a full RQ1-RQ4 sweep can be kicked off before going to bed and
checked on in the morning.

The research questions to run are given as CLI arguments; the design YAML
for each is assumed to live at experiments/<rq, lowercased>/design.yaml.

Progress and subprocess output are logged (with timestamps) to both the
console and experiments/logs/<timestamp>.log. If a run fails, it's recorded
and the batch moves on to the next research question rather than aborting
the whole night.

Run with: python scripts/run_batch.py RQ1 RQ2 RQ3            simulations only
          python scripts/run_batch.py RQ1 RQ2 RQ3 --analyze  simulations + analysis
"""

import logging
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from config.paths import BASE_DIR

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
    # 3. Research questions to run tonight are passed as CLI args, e.g.
    # `python scripts/run_batch.py RQ1 RQ2 RQ3`
    research_questions = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    if not research_questions:
        sys.exit("Usage: python scripts/run_batch.py RQ1 RQ2 ... [--analyze]")
    for research_question in research_questions:
        if not re.match(r"^RQ\d+$", research_question):
            sys.exit(f"Invalid research question '{research_question}'. Expected format: RQ1, RQ2, ...")

    # 4. Track outcome of each research question to print a summary at the end
    results = []

    for research_question in research_questions:
        design_path = BASE_DIR / "experiments" / research_question.lower() / "design.yaml"
        log.info("=== %s ===", research_question)

        # 5. Skip research questions whose design YAML hasn't been written yet
        if not design_path.exists():
            log.info("SKIPPED: %s not found", design_path)
            results.append((research_question, "SKIPPED"))
            continue

        # 6. Run launcher.py for this research question. Passing the research
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

        # 7. Start another program, and give me an object that lets me interact with it
        # while it's running
        # Normally when a program prints something it goes to the terminal,
        # with stdout=subprocess.PIPE we are asking it to dont print it but give it to us
        process = subprocess.Popen(
            cmd, cwd=BASE_DIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )

        # 8. Stream launcher.py's output through the logger (console + file)
        for line in process.stdout:
            log.info(line.rstrip())

        # Pause this Python program until the subprocess has finished running
        process.wait()

        # 9. Record outcome and move on to the next research question,
        # even on failure, so one bad run doesn't block the rest of the batch
        status = "OK" if process.returncode == 0 else f"FAILED (exit {process.returncode})"
        log.info("%s: %s", research_question, status)
        results.append((research_question, status))

    # 10. Final summary of the whole batch
    log.info("=== Batch summary ===")
    for research_question, status in results:
        log.info("%s: %s", research_question, status)


if __name__ == "__main__":
    main()