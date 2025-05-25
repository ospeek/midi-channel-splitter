# MIDI Channel Splitter

A Python tool for splitting MIDI files into separate files by channel. This tool is useful for separating different instruments or tracks in a MIDI file into individual files.

## Author

Onno Speekenbrink

## Description

This tool takes a MIDI file and splits it into separate MIDI files, one for each channel. It uses the `midicsv` and `csvmidi` tools to convert between MIDI and CSV formats.

## Features

- Split MIDI files by channel
- Preserve meta events in each channel file
- Support for both MIDI and CSV input files
- Option to keep or remove intermediate CSV files
- Creates a separate directory for split files

## Requirements

- Python 3.6 or higher
- midicsv (command-line tool)

### Installing midicsv

#### On macOS:
```bash
brew install midicsv
```

#### On Ubuntu/Debian:
```bash
sudo apt-get install midicsv
```

#### On Windows:
Download from [midicsv website](http://www.fourmilab.ch/webtools/midicsv/)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/ospeek/midi-channel-splitter.git
cd midi-channel-splitter
```

2. Install the required Python packages:
```bash
pip install -r requirements.txt
```

## Usage

### Command Line

```bash
python split_midi.py input_file.mid
```

The script will:
1. Convert the MIDI file to CSV (if input is MIDI)
2. Process the CSV file and split it by channel
3. Convert each channel's CSV back to MIDI
4. Save the results in a `split_channels` directory

### As a Python Module

```python
from split_midi import MidiSplitter

# Create a splitter instance
splitter = MidiSplitter(remove_csv=False)  # Set to True to remove intermediate CSV files

# Process a MIDI file
splitter.process_file("path/to/your/file.mid")
```

## Output

The script creates a `split_channels` directory containing:
- `channel_0.mid` - MIDI file for channel 0
- `channel_1.mid` - MIDI file for channel 1
- etc.

Each file contains the MIDI events for that specific channel, including relevant meta events.

## Testing

Run the test suite with:

```bash
python -m unittest test_split_midi.py
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- The `midicsv` and `csvmidi` tools for MIDI/CSV conversion
- The Python community for excellent testing tools