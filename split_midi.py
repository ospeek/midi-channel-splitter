#!/usr/bin/env python3

import sys
import os
import subprocess
import csv
from pathlib import Path

class MidiSplitter:
    def __init__(self, remove_csv=None):
        """Initialize the MidiSplitter with configuration options."""
        self.remove_csv = remove_csv
        self.input_file = None
        self.csv_file = None
        self.output_dir = None

    def is_midi_file(self, file_path):
        """Check if the file is a MIDI file based on extension."""
        return file_path.lower().endswith(('.mid', '.midi'))

    def convert_midi_to_csv(self, midi_file):
        """Convert MIDI file to CSV using midicsv."""
        csv_file = midi_file.rsplit('.', 1)[0] + '.csv'
        try:
            subprocess.run(['midicsv', midi_file, csv_file], check=True)
            return csv_file
        except subprocess.CalledProcessError as e:
            print(f"Error converting MIDI to CSV: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print("Error: midicsv command not found. Please install midicsv.")
            sys.exit(1)

    def convert_csv_to_midi(self, csv_file):
        """Convert CSV file to MIDI using csvmidi."""
        midi_file = csv_file.rsplit('.', 1)[0] + '.mid'
        try:
            subprocess.run(['csvmidi', csv_file, midi_file], check=True)
            return midi_file
        except subprocess.CalledProcessError as e:
            print(f"Error converting CSV to MIDI: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print("Error: csvmidi command not found. Please install midicsv.")
            sys.exit(1)

    @staticmethod
    def is_midi_event(event_type):
        """Check if the event type is a MIDI event that should be split by channel."""
        return event_type in ['Note_on_c', 'Note_off_c', 'Control_c', 'Program_c', 'Pitch_bend_c']

    def process_csv_file(self, csv_file):
        """Process the CSV file and split it into separate channel files."""
        # Read all rows from the CSV file
        rows = []
        with open(csv_file, 'r') as f:
            csv_reader = csv.reader(f, skipinitialspace=True)
            rows = list(csv_reader)

        # Create output directory
        self.output_dir = Path(csv_file).parent / 'split_channels'
        self.output_dir.mkdir(exist_ok=True)

        # Separate meta events and MIDI events
        channels = []
        midi_events = []

        for row in rows:
            if len(row) < 3:
                midi_events.append((-1, row))
            else:
                event_type = row[2]
                if self.is_midi_event(event_type) and len(row) > 3:
                    channel = row[3]
                    if channel not in channels:
                        channels.append(channel)
                    midi_events.append((channel, row))
                else:
                    midi_events.append((-1, row))

        # Process each channel
        for channel in channels:
            # Save to CSV
            output_file = self.output_dir / f'channel_{channel}.csv'
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                for event in midi_events:
                    if event[0] == channel or event[0] == -1:
                        writer.writerow(event[1])

            # Convert to MIDI
            midi_file = self.convert_csv_to_midi(str(output_file))
            print(f"Created {midi_file}")
            if self.remove_csv:
                os.remove(output_file)

    def process_file(self, input_file):
        """Main method to process a file."""
        self.input_file = input_file

        if not os.path.exists(input_file):
            print(f"Error: File {input_file} does not exist")
            sys.exit(1)

        # Check if input is MIDI file
        if self.is_midi_file(input_file):
            print(f"Converting MIDI file {input_file} to CSV...")
            self.csv_file = self.convert_midi_to_csv(input_file)
            if self.remove_csv is None:
                self.remove_csv = True
        else:
            self.csv_file = input_file
            if self.remove_csv is None:
                self.remove_csv = False

        print(f"Processing {self.csv_file}...")
        self.process_csv_file(self.csv_file)

        # Clean up temporary CSV file if it was converted from MIDI
        if self.remove_csv:
            os.remove(self.csv_file)

def main():
    if len(sys.argv) != 2:
        print("Usage: python split_midi.py <input_file>")
        sys.exit(1)

    splitter = MidiSplitter()
    splitter.process_file(sys.argv[1])

if __name__ == "__main__":
    main()