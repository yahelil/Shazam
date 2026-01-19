import os
from tkinter import filedialog
import json
import librosa
from pydub import AudioSegment
import numpy as np


def extract_mfcc(file_path, n_mfcc=13):
    """
    Extracts MFCC features from an audio file.
    """
    try:
        # Load the audio file
        y, sr = librosa.load(file_path, sr=None)

        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)

        mfccs_var = np.var(mfccs.T, axis=0)

        return json.dumps(mfccs_var.tolist())

    except Exception as e:
        # Handle any exceptions that occur during file loading or feature extraction
        print(f"Error loading file {file_path}: {e}")
        return None


def split_wav(selected_file, mode):
    # Load the audio file
    audio = AudioSegment.from_wav(selected_file)
    # Duration of each split in milliseconds
    split_duration_ms = 5 * 1000  # 5 seconds

    # Calculate the number of splits
    num_splits = len(audio) // split_duration_ms
    splits = []
    base_dir = os.path.dirname(selected_file)
    base_name = os.path.splitext(os.path.basename(selected_file))[0]

    for i in range(num_splits):
        start_time = i * split_duration_ms
        end_time = start_time + split_duration_ms
        split_audio = audio[start_time:end_time]

        # Create a clean filename: e.g., "SongName_0_5.wav"
        split_filename = f"{base_name}_{i * 5}_{(i + 1) * 5}.wav"
        split_filepath = os.path.join(base_dir, split_filename)

        split_audio.export(split_filepath, format="wav")

        if mode == "Export":
            pass
        else:
            # In database mode, we extract data from the newly saved file
            mfcc_data = extract_mfcc(split_filepath)

            # Append the data if extraction was successful
            if mfcc_data is not None:
                splits.append((split_filename, mfcc_data))
    return splits


def export():
    selected_destination = filedialog.askopenfilename(title="Select a prerecorded audio file",
                                                      filetypes=(("WAV Files", "*.wav"), ("All Files", "*.*")))
    split_wav(selected_destination, "Export")

