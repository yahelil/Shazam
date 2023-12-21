import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
from PIL import  Image

FRAME_SIZE = 2048
HOP_SIZE = 100


class Spec:
    def __init__(self):
        self.file = "audio/scale.wav"
        self.S_db = None
        self.BinerySpec = []

    def scale(self):
        scale, sr = librosa.load(self.file)  # returns audio time series, sampling rate of scale
        S_scale = librosa.stft(scale, n_fft=FRAME_SIZE, hop_length=HOP_SIZE)

        # Creating a spectrogram out of the audio
        Y_scale = np.abs(S_scale) ** 2
        self.S_db = librosa.amplitude_to_db(Y_scale, ref=np.max)
        for line in self.S_db:
            self.BinerySpec.append([0 if x == -80.0 else 1 for x in line])

        plt.imshow(self.BinerySpec, cmap=plt.get_cmap('gray'))
        plt.show()

        # self.plot_spectrogram()

    def plot_spectrogram(self):
        fig, ax = plt.subplots()
        img = librosa.display.specshow(self.S_db, x_axis='time', y_axis='linear', ax=ax)
        ax.set(title='A Spectrogram of Hz on time')
        fig.colorbar(img, ax=ax, format="%+2.f dB")
        plt.show()


if __name__ == "__main__":
     g = Spec()
     g.scale()

