#!/usr/bin/env python3

import unittest
import os
import tempfile
import shutil
import subprocess
from pathlib import Path
from split_midi import MidiSplitter, MidiSplitterError

class TestMidiSplitter(unittest.TestCase):
    """Test cases for the MidiSplitter class."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests."""
        # Check if required commands are available
        try:
            subprocess.run(['midicsv', '-u'], capture_output=True, check=True)
            subprocess.run(['csvmidi', '-u'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise unittest.SkipTest("Required commands (midicsv, csvmidi) not found")

    def setUp(self):
        """Set up test environment before each test."""
        self.test_dir = tempfile.mkdtemp()
        self.splitter = MidiSplitter(remove_csv=False)
        self._create_test_files()

    def tearDown(self):
        """Clean up after each test."""
        shutil.rmtree(self.test_dir)

    def _create_test_files(self):
        """Create test MIDI and CSV files."""
        # Create a CSV file for testing
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

    def test_is_midi_file(self):
        """Test MIDI file detection."""
        self.assertTrue(self.splitter.is_midi_file(f"{self.test_dir}/test.mid"))
        self.assertTrue(self.splitter.is_midi_file(f"{self.test_dir}/test.MIDI"))
        self.assertFalse(self.splitter.is_midi_file(f"{self.test_dir}/test.txt"))
        self.assertFalse(self.splitter.is_midi_file(f"{self.test_dir}/test"))

    def test_is_midi_event(self):
        """Test MIDI event detection."""
        self.assertTrue(MidiSplitter.is_midi_event("Note_on_c"))
        self.assertTrue(MidiSplitter.is_midi_event("Note_off_c"))
        self.assertTrue(MidiSplitter.is_midi_event("Control_c"))
        self.assertTrue(MidiSplitter.is_midi_event("Program_c"))
        self.assertTrue(MidiSplitter.is_midi_event("Pitch_bend_c"))
        self.assertFalse(MidiSplitter.is_midi_event("Meta"))
        self.assertFalse(MidiSplitter.is_midi_event(""))
        self.assertFalse(MidiSplitter.is_midi_event("Note_on"))

    def test_process_file_midi(self):
        """Test processing a MIDI file."""
        self.splitter.process_file(f"{self.test_dir}/test.mid")
        self.assertTrue(os.path.exists(f"{self.test_dir}/split_channels/channel_1.mid"))
        self.assertTrue(os.path.exists(f"{self.test_dir}/split_channels/channel_2.mid"))

    def test_process_file_csv(self):
        """Test processing a CSV file."""
        csv_file = os.path.join(self.test_dir, "test.csv")
        self.splitter.process_file(csv_file)
        self.assertTrue(os.path.exists(f"{self.test_dir}/split_channels/channel_1.mid"))
        self.assertTrue(os.path.exists(f"{self.test_dir}/split_channels/channel_2.mid"))

    def test_nonexistent_file(self):
        """Test handling of nonexistent file."""
        with self.assertRaises(MidiSplitterError):
            self.splitter.process_file(f"{self.test_dir}/nonexistent.mid")

    def test_wellformed_channel_files(self):
        """Test that each channel CSV file is well-formed with header and end markers."""
        self.splitter.process_file(f"{self.test_dir}/test.mid")

        for channel in [1, 2]:
            csv_file = f"{self.test_dir}/split_channels/channel_{channel}.csv"
            with open(csv_file, 'r') as f:
                lines = f.readlines()
                # Check first line for header
                self.assertTrue(any('Header' in line for line in lines[:3]),
                              f"Channel {channel} CSV missing header")
                # Check last line for End_of_file
                self.assertTrue('End_of_file' in lines[-1],
                              f"Channel {channel} CSV missing End_of_file marker")

    def test_channel_content(self):
        """Test that channel files contain correct events."""
        self.splitter.process_file(f"{self.test_dir}/test.mid")

        # Test channel 1 content
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

        # Test channel 2 content
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

    def test_csv_removal(self):
        """Test that CSV files are removed when remove_csv is True."""
        splitter = MidiSplitter(remove_csv=True)
        splitter.process_file(f"{self.test_dir}/test.mid")

        # Check that MIDI files exist but CSV files don't
        self.assertTrue(os.path.exists(f"{self.test_dir}/split_channels/channel_1.mid"))
        self.assertTrue(os.path.exists(f"{self.test_dir}/split_channels/channel_2.mid"))
        self.assertFalse(os.path.exists(f"{self.test_dir}/split_channels/channel_1.csv"))
        self.assertFalse(os.path.exists(f"{self.test_dir}/split_channels/channel_2.csv"))

if __name__ == '__main__':
    unittest.main()