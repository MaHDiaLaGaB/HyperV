import time
import re
import subprocess
import os
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from threading import Timer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("watcher.log")
    ]
)
logger = logging.getLogger("watcher")

# Updated regex to include all relevant directories
WATCHER_REGEX_PATTERN = re.compile(
    r"(main\.py|"
    r"schemas/.*\.py|"
    r"models/.*\.py|"
    r"services/.*\.py|"
    r"repositories/.*\.py|"
    r"routes/.*\.py|"
    r"db/.*\.py)$"
)
APP_PATH = "app"
DEBOUNCE_TIME = 1.5  # seconds

class MyHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.debounce_timer = None
        self.last_modified = 0

    def on_modified(self, event):
        if not event.is_directory:
            try:
                rel_path = os.path.relpath(event.src_path, APP_PATH)
                if WATCHER_REGEX_PATTERN.search(rel_path):
                    current_time = time.time()
                    # Debounce to prevent multiple triggers
                    if current_time - self.last_modified > DEBOUNCE_TIME:
                        self.last_modified = current_time
                        if self.debounce_timer:
                            self.debounce_timer.cancel()
                        self.debounce_timer = Timer(
                            DEBOUNCE_TIME, 
                            self.execute_command, 
                            [event.src_path]
                        )
                        self.debounce_timer.start()
                        logger.info(f"Detected modification in {rel_path}")
            except Exception as e:
                logger.error(f"Error handling modification: {e}")

    def execute_command(self, file_path):
        try:
            rel_path = os.path.relpath(file_path, APP_PATH)
            logger.info(f"Processing changes in {rel_path}")
            self.run_mypy_checks()
            self.run_openapi_schema_generation()
        except Exception as e:
            logger.error(f"Error in execute_command: {e}")

    def run_mypy_checks(self):
        """Run mypy type checks and print output."""
        logger.info("Running mypy type checks...")
        try:
            result = subprocess.run(
                ["uv", "run", "mypy", "app"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.stdout:
                logger.info("Mypy output:\n" + result.stdout)
            if result.stderr:
                logger.error("Mypy errors:\n" + result.stderr)
            
            if result.returncode:
                logger.warning(
                    "Type errors detected! Check the mypy output for details."
                )
            else:
                logger.info("No type errors detected.")
        except Exception as e:
            logger.error(f"Error running mypy: {e}")

    def run_openapi_schema_generation(self):
        """Run the OpenAPI schema generation command."""
        logger.info("Generating OpenAPI schema...")
        try:
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "python",
                    "-m",
                    "commands.generate_openapi_schema",
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            if result.stdout:
                logger.info("OpenAPI generation output:\n" + result.stdout)
            logger.info("OpenAPI schema generation completed successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(
                f"OpenAPI generation failed with error {e.returncode}:\n"
                f"STDOUT: {e.stdout}\nSTDERR: {e.stderr}"
            )
        except Exception as e:
            logger.error(f"Error generating OpenAPI schema: {e}")


if __name__ == "__main__":
    logger.info("Starting watchdog service...")
    logger.info(f"Watching directory: {APP_PATH}")
    logger.info(f"Watching patterns: {WATCHER_REGEX_PATTERN.pattern}")
    
    observer = Observer()
    observer.schedule(MyHandler(), APP_PATH, recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping watchdog service...")
        observer.stop()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        observer.join()
        logger.info("Watchdog service stopped.")