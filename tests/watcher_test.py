import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest
from watchdog.events import FileCreatedEvent

from invgen.watcher import watch_for_changes


@pytest.fixture
def temp_inventory_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create basic directory structure
        os.makedirs(os.path.join(tmpdir, "hosts"))
        os.makedirs(os.path.join(tmpdir, "metadata"))
        os.makedirs(os.path.join(tmpdir, "generated"))

        yield Path(tmpdir)


@patch("invgen.watcher.Observer")
@patch("invgen.watcher.generate_hosts")
@patch("invgen.watcher.sleep", side_effect=KeyboardInterrupt)  # Stop the watch loop
def test_watch_for_changes(
    mock_sleep, mock_generate_hosts, mock_observer, temp_inventory_dir
):
    # Setup mock observer
    mock_observer_instance = MagicMock()
    mock_observer.return_value = mock_observer_instance

    # Call the function
    watch_for_changes(temp_inventory_dir)

    # Check that the observer was started and stopped
    mock_observer_instance.start.assert_called_once()
    mock_observer_instance.stop.assert_called_once()
    mock_observer_instance.join.assert_called_once()

    # Check that the observer was scheduled for both directories
    assert mock_observer_instance.schedule.call_count == 2
    mock_observer_instance.schedule.assert_has_calls(
        [
            call(
                mock_observer_instance.schedule.call_args_list[0][0][0],
                str(temp_inventory_dir / "hosts/"),
                recursive=True,
            ),
            call(
                mock_observer_instance.schedule.call_args_list[1][0][0],
                str(temp_inventory_dir / "metadata/"),
                recursive=True,
            ),
        ],
        any_order=True,
    )


@patch("invgen.watcher.generate_hosts")
@patch("invgen.watcher.Observer")
def test_file_event_handling(mock_observer, mock_generate_hosts, temp_inventory_dir):
    # Setup mock observer
    mock_observer_instance = MagicMock()
    mock_observer.return_value = mock_observer_instance

    # Create a handler directly
    from invgen.watcher import RegenerateHandler

    handler = RegenerateHandler(temp_inventory_dir)

    # Test file created event
    yaml_event = FileCreatedEvent(str(temp_inventory_dir / "hosts" / "test.yaml"))
    handler._regenerate(yaml_event)
    mock_generate_hosts.assert_called_with(temp_inventory_dir)
    mock_generate_hosts.reset_mock()

    # Test _should_process method
    # File in generated directory (should be ignored)
    generated_event = FileCreatedEvent(
        str(temp_inventory_dir / "generated" / "test.yaml")
    )
    assert not handler._should_process(generated_event)

    # Non-yaml file (should be ignored)
    non_yaml_event = FileCreatedEvent(str(temp_inventory_dir / "hosts" / "test.txt"))
    assert not handler._should_process(non_yaml_event)

    # Valid yaml file (should be processed)
    valid_event = FileCreatedEvent(str(temp_inventory_dir / "hosts" / "test.yaml"))
    assert handler._should_process(valid_event)


@patch("invgen.watcher.generate_hosts")
@patch("invgen.watcher.time")
def test_debounce_mechanism(mock_time, mock_generate_hosts, temp_inventory_dir):
    # Create a handler directly
    from invgen.watcher import RegenerateHandler

    handler = RegenerateHandler(temp_inventory_dir)

    # Set initial time
    mock_time.return_value = 100.0

    # First event should trigger regeneration
    yaml_event1 = FileCreatedEvent(str(temp_inventory_dir / "hosts" / "test1.yaml"))
    handler._schedule_regeneration(yaml_event1)
    assert mock_generate_hosts.call_count == 1
    mock_generate_hosts.reset_mock()

    # Second event within debounce time should not trigger immediate regeneration
    mock_time.return_value = 100.2  # Less than debounce time (0.5s)
    yaml_event2 = FileCreatedEvent(str(temp_inventory_dir / "hosts" / "test2.yaml"))
    handler._schedule_regeneration(yaml_event2)
    assert mock_generate_hosts.call_count == 0
    assert handler.pending_regeneration == True

    # Check pending should process the pending regeneration after debounce time
    mock_time.return_value = 100.7  # More than debounce time
    handler.check_pending()
    assert mock_generate_hosts.call_count == 1
    assert handler.pending_regeneration == False
