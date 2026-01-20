import librosa
import numpy as np
import json


def extract_mfcc(file_path, n_mfcc=13):
    """
    Extracts MFCC features from an audio file.
    """
    try:
        y, sr = librosa.load(file_path, sr=None)

        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)

        mfccs_mean = np.mean(mfccs.T, axis=0)

        mfccs_var = np.var(mfccs.T, axis=0)

        return json.dumps(mfccs_var.tolist())

    except Exception as e:
        # Handle any exceptions that occur during file loading or feature extraction
        print(f"Error loading file {file_path}: {e}")
        return None
