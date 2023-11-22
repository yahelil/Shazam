import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt

FRAME_SIZE = 2048
HOP_SIZE = 512


def plot_spectrogram(S_db):
    plt.figure()
    librosa.display.specshow(S_db)
    plt.colorbar()
    plt.show()


scale_file = "audio/mysinewave.wav"

scale, sr = librosa.load(scale_file)  # returns audio time series, sampling rate of scale
S_scale = librosa.stft(scale, n_fft=FRAME_SIZE, hop_length=HOP_SIZE)

# Creating a spectrogram out of the audio
Y_scale = np.abs(S_scale) ** 2
S_db = librosa.amplitude_to_db(Y_scale, ref=np.max)
plot_spectrogram(S_db)


