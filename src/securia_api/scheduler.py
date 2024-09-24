import sys
import os
import threading
import schedule
import time
from envyaml import EnvYAML
from logger import setup_custom_logger

logger = setup_custom_logger(__name__)

logger.info("Scheduler loading config")
config = EnvYAML('config.yml')

def run_continuously(interval=1):
    cease_continuous_run = threading.Event()

    class ScheduleThread(threading.Thread):
        def run(self):
            while not cease_continuous_run.is_set():
                schedule.run_pending()
                time.sleep(interval)

    continuous_thread = ScheduleThread()
    continuous_thread.start()
    return continuous_thread, cease_continuous_run

def health_check():
    logger.debug("Scheduler active")

def start_schedules():
    if config["scheduler"]["enabled"]:
        logger.info("Starting scheduled tasks")
        schedule.every(30).seconds.do(health_check)

        # Run the schedule on a separate thread
        continuous_thread, stop_run_continuously = run_continuously()

        logger.info("Scheduler started")
        # Now return control back to the main program
        return continuous_thread, stop_run_continuously
    else:
        logger.info("Scheduler not enabled")
        return None, None

if __name__ == "__main__":
    start_schedules()