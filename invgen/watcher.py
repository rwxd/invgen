from pathlib import Path
from time import sleep, time
import os

import typer
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from invgen.hosts import generate_hosts
from invgen.logging import logger


class RegenerateHandler(FileSystemEventHandler):
    def __init__(self, source: Path):
        self.source = source
        self.pending_regeneration = False
        self.last_processed_time = 0
        self.debounce_time = 0.5  # seconds
    
    def _should_process(self, event):
        # Skip events in the generated directory
        if "generated" in event.src_path:
            return False
            
        # Only process yaml files
        if not event.src_path.endswith(".yaml") and not event.is_directory:
            return False
            
        return True
        
    def _schedule_regeneration(self, event):
        if not self._should_process(event):
            return
            
        current_time = time()
        if current_time - self.last_processed_time < self.debounce_time:
            # If we're within the debounce period, just mark that we need to regenerate
            self.pending_regeneration = True
            return
            
        # Otherwise, regenerate now
        self._regenerate(event)
        self.pending_regeneration = False
        self.last_processed_time = current_time
        
    def _regenerate(self, event):
        print(f"=> File {event.event_type}: {event.src_path}")
        try:
            generate_hosts(self.source)
            print(f"=> Done! Regenerated hosts in {self.source}/generated/")
        except Exception as e:
            print(f"=> Error regenerating hosts: {e}")
            logger.error(f"Error regenerating hosts: {e}")

    def on_created(self, event):
        self._schedule_regeneration(event)

    def on_modified(self, event):
        self._schedule_regeneration(event)

    def on_deleted(self, event):
        self._schedule_regeneration(event)
        
    def check_pending(self):
        """Check if there's a pending regeneration and process it if needed"""
        current_time = time()
        if self.pending_regeneration and current_time - self.last_processed_time >= self.debounce_time:
            print("=> Processing pending changes...")
            try:
                generate_hosts(self.source)
                print(f"=> Done! Regenerated hosts in {self.source}/generated/")
            except Exception as e:
                print(f"=> Error regenerating hosts: {e}")
                logger.error(f"Error regenerating hosts: {e}")
            self.pending_regeneration = False
            self.last_processed_time = current_time


def watch_for_changes(source: Path):
    # Ensure the directories exist
    os.makedirs(source.joinpath("hosts/"), exist_ok=True)
    os.makedirs(source.joinpath("metadata/"), exist_ok=True)

    event_handler = RegenerateHandler(source)
    observer = Observer()
    observer.schedule(event_handler, str(source.joinpath("hosts/")), recursive=True)
    observer.schedule(event_handler, str(source.joinpath("metadata/")), recursive=True)
    observer.start()

    typer.echo("=> Watching for changes... Press Ctrl+C to stop.")
    try:
        while True:
            event_handler.check_pending()
            sleep(0.5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
