import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt

FRAME_SIZE = 2048
HOP_SIZE = 512


def plot_spectrogram(tmp, Y, sr, hop_length, y_axis="linear"):
    plt.figure(figsize=(25, 10))
    librosa.display.specshow(tmp)
    plt.colorbar()


scale_file = "audio/scale.wav"

scale, sr = librosa.load(scale_file)  # returns audio time series, sampling rate of scale
S_scale = librosa.stft(scale, n_fft=FRAME_SIZE, hop_length=HOP_SIZE)

# Creating a spectrogram out of the audio
Y_scale = np.abs(S_scale) ** 2
S_db = librosa.amplitude_to_db(Y_scale, ref=np.max)
plot_spectrogram(S_db, Y_scale, sr, HOP_SIZE)

Y_log_scale = librosa.power_to_db(Y_scale)
plot_spectrogram(Y_log_scale, sr, HOP_SIZE)

plot_spectrogram(Y_log_scale, sr, HOP_SIZE, y_axis="log")
