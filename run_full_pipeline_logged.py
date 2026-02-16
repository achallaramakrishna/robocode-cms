import subprocess
import logging
import sys
from datetime import datetime
from pathlib import Path

# -----------------------------------------
# CONFIG
# -----------------------------------------

JSON = "db_bootstrap/courses/physics_grade10_cbse.json"
PROMPT = "prompts/physics/ocr_physics_cbse.txt"

commands = [
    f"python db_bootstrap/run_phase_a.py {JSON}",
    f"python db_bootstrap/run_phase_b.py {JSON}",
    f"python run_ocr.py {JSON} {PROMPT} --force",
    f"python run_merge_all_chapters.py {JSON}",
    f"python run_clean_all_chapters.py {JSON}",
    f"python run_flashcards_all_chapters.py {JSON}",
    f"python run_matching_games_all_chapters.py {JSON}",
    f"python run_quizzes_all_chapters.py {JSON}",
    f"python run_practice_tests_all_chapters.py {JSON}",
    f"python run_textbook_practice_tests.py {JSON}",
    f"python db_bootstrap/run_phase_c_all_chapters.py {JSON}",
    f"python -m db_bootstrap.run_phase_d_flashcards {JSON}",
    f"python -m db_bootstrap.run_phase_e_quizzes {JSON}",
    f"python -m db_bootstrap.run_phase_f_matching_game_all_chapters {JSON}",
    f"python -m db_bootstrap.run_phase_f_matching_pair_all_chapters {JSON}",
    f"python -m db_bootstrap.run_phase_f_generate_practice_versions_all_chapters {JSON}",
    f"python -m db_bootstrap.phase_g_textbook_practice_to_db {JSON}",
]

# -----------------------------------------
# SETUP LOG FILE
# -----------------------------------------

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = log_dir / f"pipeline_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

# -----------------------------------------
# EXECUTION
# -----------------------------------------

logging.info("==========================================")
logging.info("ROBO DYNAMICS FULL PIPELINE STARTED")
logging.info("==========================================")

for cmd in commands:
    logging.info(f"Running: {cmd}")

    start = datetime.now()

    try:
        result = subprocess.run(cmd, shell=True,
                                capture_output=True,
                                text=True)

        logging.info(result.stdout)

        if result.returncode != 0:
            logging.error(result.stderr)
            logging.error("Pipeline stopped due to error.")
            break

    except Exception as e:
        logging.exception("Unexpected error occurred")
        break

    end = datetime.now()
    duration = (end - start).total_seconds()

    logging.info(f"Completed in {duration:.2f} seconds")
    logging.info("------------------------------------------")

logging.info("PIPELINE FINISHED")
logging.info(f"Log saved to: {log_file}")
