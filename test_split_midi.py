#!/usr/bin/env python3

import unittest
import os
import tempfile
import shutil
import subprocess
from pathlib import Path
from split_midi import MidiSplitter

class TestMidiSplitter(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        self.test_dir = tempfile.mkdtemp()
        self.splitter = MidiSplitter(remove_csv=False)

        # Create a simple test MIDI file (this is just a placeholder)
        # Create a CSV file for testing first
        test_csv = os.path.join(self.test_dir, "test.csv")
        with open(test_csv, "w") as f:
            f.write("0, 0, Header, 0, 1, 96\n")
            f.write("1, 0, Start_track\n")
            f.write("1, 0, MIDI_port, 0\n")
            f.write("1, 0, System_exclusive, 5, 126, 127, 9, 1, 247\n")
            f.write("1, 0, MIDI_port, 0\n")
            f.write("1, 0, Time_signature, 4, 2, 24, 8\n")
            f.write("1, 0, Key_signature, 0, \"major\"\n")
            f.write("1, 0, Tempo, 400000\n")
            f.write("1, 0, Program_c, 1, 32\n")
            f.write("1, 0, Control_c, 1, 7, 100\n")
            f.write("1, 0, Control_c, 1, 10, 64\n")
            f.write("1, 0, Control_c, 1, 11, 127\n")
            f.write("1, 0, Control_c, 1, 91, 0\n")
            f.write("1, 0, Control_c, 1, 93, 0\n")
            f.write("1, 0, Program_c, 2, 27\n")
            f.write("1, 0, Control_c, 2, 7, 100\n")
            f.write("1, 0, Control_c, 2, 10, 50\n")
            f.write("1, 0, Control_c, 2, 11, 127\n")
            f.write("1, 0, Control_c, 2, 91, 40\n")
            f.write("1, 0, Control_c, 2, 93, 40\n")
            f.write("1, 100, Note_on_c, 1, 40, 75\n")
            f.write("1, 200, Note_on_c, 1, 40, 0\n")
            f.write("1, 300, Note_on_c, 2, 40, 80\n")
            f.write("1, 400, Note_on_c, 2, 40, 0\n")
            f.write("1, 500, End_track\n")
            f.write("0, 0, End_of_file\n")

        # Convert the CSV to MIDI for the test
        self.test_midi = os.path.join(self.test_dir, "test.mid")
        subprocess.run(['csvmidi', test_csv, self.test_midi], check=True)

    def tearDown(self):
        """Clean up after each test."""
        shutil.rmtree(self.test_dir)

    def test_is_midi_file(self):
        """Test MIDI file detection."""
        self.assertTrue(self.splitter.is_midi_file(f"{self.test_dir}/test.mid"))
        self.assertFalse(self.splitter.is_midi_file(f"{self.test_dir}/test.txt"))

    def test_is_midi_event(self):
        """Test MIDI event detection."""
        self.assertTrue(MidiSplitter.is_midi_event("Note_on_c"))
        self.assertTrue(MidiSplitter.is_midi_event("Note_off_c"))
        self.assertTrue(MidiSplitter.is_midi_event("Control_c"))
        self.assertFalse(MidiSplitter.is_midi_event("Meta"))
        self.assertFalse(MidiSplitter.is_midi_event(""))

    def test_process_file(self):
        """Test the process_file method."""
        self.splitter.process_file(f"{self.test_dir}/test.mid")
        self.assertTrue(os.path.exists(f"{self.test_dir}/split_channels/channel_1.mid"))
        self.assertTrue(os.path.exists(f"{self.test_dir}/split_channels/channel_2.mid"))

    def test_wellformed_channel_files(self):
        """Test that each channel CSV file is well-formed with header and end markers."""
        # Process the test MIDI file
        self.splitter.process_file(f"{self.test_dir}/test.mid")

        # Get the paths of the generated CSV files
        channel1_csv = f"{self.test_dir}/split_channels/channel_1.csv"
        channel2_csv = f"{self.test_dir}/split_channels/channel_2.csv"

        # Check channel 1 CSV
        with open(channel1_csv, 'r') as f:
            lines = f.readlines()
            # Check first line for header
            self.assertTrue(any('Header' in line for line in lines[:3]), "Channel 1 CSV missing header")
            # Check last line for End_of_file
            self.assertTrue('End_of_file' in lines[-1], "Channel 1 CSV missing End_of_file marker")

        # Check channel 2 CSV
        with open(channel2_csv, 'r') as f:
            lines = f.readlines()
            # Check first line for header
            self.assertTrue(any('Header' in line for line in lines[:3]), "Channel 2 CSV missing header")
            # Check last line for End_of_file
            self.assertTrue('End_of_file' in lines[-1], "Channel 2 CSV missing End_of_file marker")

    def test_channel1_content(self):
        """Test that channel 1 file contains all meta events and channel 1 events, but no channel 2 events."""
        self.splitter.process_file(f"{self.test_dir}/test.mid")
        channel1_csv = f"{self.test_dir}/split_channels/channel_1.csv"

        with open(channel1_csv, 'r') as f:
            content = f.read()

            # Should contain meta events
            self.assertIn("Header", content)
            self.assertIn("Time_signature", content)
            self.assertIn("Key_signature", content)
            self.assertIn("Tempo", content)

            # Should contain channel 1 events
            self.assertIn("Program_c,1,32", content)
            self.assertIn("Control_c,1,7,100", content)
            self.assertIn("Note_on_c,1,40,75", content)

            # Should not contain channel 2 events
            self.assertNotIn("Program_c,2,27", content)
            self.assertNotIn("Control_c,2,7,100", content)
            self.assertNotIn("Note_on_c,2,40,80", content)

    def test_channel2_content(self):
        """Test that channel 2 file contains all meta events and channel 2 events, but no channel 1 events."""
        self.splitter.process_file(f"{self.test_dir}/test.mid")
        channel2_csv = f"{self.test_dir}/split_channels/channel_2.csv"

        with open(channel2_csv, 'r') as f:
            content = f.read()

            # Should contain meta events
            self.assertIn("Header", content)
            self.assertIn("Time_signature", content)
            self.assertIn("Key_signature", content)
            self.assertIn("Tempo", content)

            # Should contain channel 2 events
            self.assertIn("Program_c,2,27", content)
            self.assertIn("Control_c,2,7,100", content)
            self.assertIn("Note_on_c,2,40,80", content)

            # Should not contain channel 1 events
            self.assertNotIn("Program_c,1,32", content)
            self.assertNotIn("Control_c,1,7,100", content)
            self.assertNotIn("Note_on_c,1,40,75", content)

if __name__ == '__main__':
    unittest.main()