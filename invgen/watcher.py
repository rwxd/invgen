from pathlib import Path
from time import sleep

import typer
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from invgen.hosts import generate_hosts


def watch_for_changes(source: Path):
    class RegenerateHandler(FileSystemEventHandler):
        def _run(self, event):
            if (
                "generated" not in event.src_path
                and event.src_path.endswith(".yaml")
                and event.is_directory is False
            ):
                print(f"=> File {event.event_type}: {event.src_path}")
                generate_hosts(source)
                print(f"=> Done! Regenerated hosts in {source}/generated/")

        def on_created(self, event):
            self._run(event)

        def on_modified(self, event):
            self._run(event)

        def on_deleted(self, event):
            self._run(event)

    event_handler = RegenerateHandler()
    observer = Observer()
    observer.schedule(event_handler, str(source.joinpath("hosts/")), recursive=True)
    observer.schedule(event_handler, str(source.joinpath("metadata/")), recursive=True)
    observer.start()

    typer.echo("=> Watching for changes... Press Ctrl+C to stop.")
    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
