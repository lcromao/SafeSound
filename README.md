# Welcome to SafeSound

_A Secure Application for Audio Transcription with Artificial Intelligence_

This project is part of the prerequisite for the completion of the MBA in Data Science & Analytics at USP/ESALQ. This app aims to allow the transcription of audio files into text. The project was built in Python using the Streamlit library for the graphical interface and the Whisper model for speech recognition. The Whisper model was trained with the LibriSpeech dataset, which contains 1000 hours of audiobook readings. The model was trained for 10 epochs and achieved an accuracy of 0.9.

## Whisper Prerequisites

The base code is expected to run on Python versions 3.8-3.11. Make sure you have the correct Python version installed. To check the Python version, run the following command:

### Python

```bash
python --version
```

### ffmpeg

To run Whisper, you need to install the `ffmpeg` package and its dependencies. To do this, run the following command:

#### on Ubuntu or Debian

```bash
sudo apt update && sudo apt install ffmpeg
```

#### on Arch Linux

```bash
sudo pacman -S ffmpeg
```

#### on MacOS using Homebrew (https://brew.sh/)

```bash
brew install ffmpeg
```

#### on Windows using Chocolatey (https://chocolatey.org/)

```bash
choco install ffmpeg
```

#### on Windows using Scoop (https://scoop.sh/)

```bash
scoop install ffmpeg
```

### Command Line Tools for MacOS

To avoid potential incompatibilities on MacOS, install the Xcode command line tools:

```bash
xcode-select --install
```

After installing the prerequisites, install the required packages listed in the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

## To Run

To run the project, execute the following command:

```bash
streamlit run app.py
```

Then, access the link `http://localhost:8501` in your browser.

```bash
pyinstaller --name=SafeSoundPlus --windowed --noconsole run_app.py
```
