"""A Python module for splitting MIDI files into separate files by channel.

This module provides functionality to split MIDI files into separate files based on
MIDI channels while preserving meta events. It uses midicsv and csvmidi tools for
conversion between MIDI and CSV formats.
"""

#!/usr/bin/env python3

import sys
import os
import subprocess
import csv
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIDI_EXTENSIONS = ('.mid', '.midi')
MIDI_EVENTS: Set[str] = {
    'Note_on_c',
    'Note_off_c',
    'Control_c',
    'Program_c',
    'Pitch_bend_c'
}
OUTPUT_DIR_NAME = 'split_channels'
META_EVENT_CHANNEL = -1

class MidiSplitterError(Exception):
    """Base exception class for MidiSplitter errors."""
    pass

class MidiSplitter:
    """A class to split MIDI files into separate files by channel.

    This class handles the conversion between MIDI and CSV formats, and splits
    MIDI events by channel while preserving meta events in each output file.

    Attributes:
        remove_csv (Optional[bool]): Whether to remove CSV files after processing
        input_file (Optional[str]): Path to the input file
        csv_file (Optional[str]): Path to the intermediate CSV file
        output_dir (Optional[Path]): Directory for output files
    """

    def __init__(self, remove_csv: Optional[bool] = None) -> None:
        """Initialize the MidiSplitter with configuration options.

        Args:
            remove_csv: Whether to remove CSV files after processing. If None,
                       will be determined based on input file type.
        """
        self.remove_csv = remove_csv
        self.input_file: Optional[str] = None
        self.csv_file: Optional[str] = None
        self.output_dir: Optional[Path] = None

    def is_midi_file(self, file_path: str) -> bool:
        """Check if the file is a MIDI file based on extension.

        Args:
            file_path: Path to the file to check

        Returns:
            bool: True if the file has a MIDI extension, False otherwise
        """
        return file_path.lower().endswith(MIDI_EXTENSIONS)

    def convert_midi_to_csv(self, midi_file: str) -> str:
        """Convert MIDI file to CSV using midicsv.

        Args:
            midi_file: Path to the MIDI file to convert

        Returns:
            str: Path to the created CSV file

        Raises:
            MidiSplitterError: If midicsv command fails or is not found
        """
        csv_file = midi_file.rsplit('.', 1)[0] + '.csv'
        try:
            subprocess.run(
                ['midicsv', midi_file, csv_file],
                check=True,
                capture_output=True,
                text=True
            )
            return csv_file
        except subprocess.CalledProcessError as e:
            raise MidiSplitterError(f"Error converting MIDI to CSV: {e.stderr}") from e
        except FileNotFoundError as exc:
            raise MidiSplitterError(
                "Error: midicsv command not found. Please install midicsv."
            ) from exc

    def convert_csv_to_midi(self, csv_file: str) -> str:
        """Convert CSV file to MIDI using csvmidi.

        Args:
            csv_file: Path to the CSV file to convert

        Returns:
            str: Path to the created MIDI file

        Raises:
            MidiSplitterError: If csvmidi command fails or is not found
        """
        midi_file = csv_file.rsplit('.', 1)[0] + '.mid'
        try:
            subprocess.run(
                ['csvmidi', csv_file, midi_file],
                check=True,
                capture_output=True,
                text=True
            )
            return midi_file
        except subprocess.CalledProcessError as e:
            raise MidiSplitterError(f"Error converting CSV to MIDI: {e.stderr}") from e
        except FileNotFoundError as exc:
            raise MidiSplitterError(
                "Error: csvmidi command not found. Please install midicsv."
            ) from exc

    @staticmethod
    def is_midi_event(event_type: str) -> bool:
        """Check if the event type is a MIDI event that should be split by channel.

        Args:
            event_type: The event type to check

        Returns:
            bool: True if the event type is a channel-specific MIDI event
        """
        return event_type in MIDI_EVENTS

    def _create_output_directory(self, base_path: Path) -> None:
        """Create the output directory for split files.

        Args:
            base_path: Base path where the output directory should be created
        """
        self.output_dir = base_path / OUTPUT_DIR_NAME
        self.output_dir.mkdir(exist_ok=True)
        logger.debug(f"Created output directory: {self.output_dir}")

    def _process_midi_events(self, rows: List[List[str]]) -> Tuple[List[int], List[Tuple[int, List[str]]]]:
        """Process MIDI events and separate them by channel.

        Args:
            rows: List of CSV rows from the input file

        Returns:
            Tuple containing:
            - List of unique channel numbers
            - List of tuples (channel, row) for each event
        """
        channels: List[int] = []
        midi_events: List[Tuple[int, List[str]]] = []

        for row in rows:
            if len(row) < 3:
                midi_events.append((META_EVENT_CHANNEL, row))
            else:
                event_type = row[2]
                if self.is_midi_event(event_type) and len(row) > 3:
                    channel = int(row[3])
                    if channel not in channels:
                        channels.append(channel)
                    midi_events.append((channel, row))
                else:
                    midi_events.append((META_EVENT_CHANNEL, row))

        return channels, midi_events

    def _write_channel_file(self, channel: int, midi_events: List[Tuple[int, List[str]]]) -> str:
        """Write events for a specific channel to a CSV file.

        Args:
            channel: Channel number to write
            midi_events: List of all MIDI events

        Returns:
            str: Path to the created CSV file
        """
        output_file = self.output_dir / f'channel_{channel}.csv'
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            for event in midi_events:
                if event[0] == channel or event[0] == META_EVENT_CHANNEL:
                    writer.writerow(event[1])
        return str(output_file)

    def process_csv_file(self, csv_file: str) -> None:
        """Process the CSV file and split it into separate channel files.

        This method reads the CSV file, separates meta events and MIDI events,
        and creates separate files for each MIDI channel while preserving
        meta events in each file.

        Args:
            csv_file: Path to the CSV file to process
        """
        # Read all rows from the CSV file
        with open(csv_file, 'r', encoding='utf-8') as f:
            csv_reader = csv.reader(f, skipinitialspace=True)
            rows = list(csv_reader)

        # Create output directory
        self._create_output_directory(Path(csv_file).parent)

        # Process MIDI events
        channels, midi_events = self._process_midi_events(rows)

        # Process each channel
        for channel in channels:
            # Save to CSV
            output_file = self._write_channel_file(channel, midi_events)

            # Convert to MIDI
            midi_file = self.convert_csv_to_midi(output_file)
            logger.info(f"Created {midi_file}")

            if self.remove_csv:
                os.remove(output_file)
                logger.debug(f"Removed temporary CSV file: {output_file}")

    def process_file(self, input_file: str) -> None:
        """Main method to process a file.

        This method handles the complete workflow of processing a MIDI or CSV file,
        including conversion between formats and splitting by channel.

        Args:
            input_file: Path to the input file (MIDI or CSV)

        Raises:
            MidiSplitterError: If the input file doesn't exist or processing fails
        """
        self.input_file = input_file

        if not os.path.exists(input_file):
            raise MidiSplitterError(f"Error: File {input_file} does not exist")

        try:
            # Check if input is MIDI file
            if self.is_midi_file(input_file):
                logger.info(f"Converting MIDI file {input_file} to CSV...")
                self.csv_file = self.convert_midi_to_csv(input_file)
                if self.remove_csv is None:
                    self.remove_csv = True
            else:
                self.csv_file = input_file
                if self.remove_csv is None:
                    self.remove_csv = False

            logger.info(f"Processing {self.csv_file}...")
            self.process_csv_file(self.csv_file)

            # Clean up temporary CSV file if it was converted from MIDI
            if self.remove_csv:
                os.remove(self.csv_file)
                logger.debug(f"Removed temporary CSV file: {self.csv_file}")

        except Exception as e:
            raise MidiSplitterError(f"Error processing file {input_file}: {str(e)}") from e

def main():
    """Main entry point for the script.

    Processes command line arguments and runs the MIDI splitter.
    """
    if len(sys.argv) != 2:
        logger.error("Usage: python split_midi.py <input_file>")
        sys.exit(1)

    try:
        splitter = MidiSplitter()
        splitter.process_file(sys.argv[1])
    except MidiSplitterError as e:
        logger.error(str(e))
        sys.exit(1)

if __name__ == "__main__":
    main()
