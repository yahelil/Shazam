import cv2 as cv
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt

FRAME_SIZE = 2048
HOP_SIZE = 100


class Spec:
    def __init__(self):
        self.file = "audio/elior.wav"
        self.S_db = None
        self.BinerySpec = []

    def scale(self):
        scale, sr = librosa.load(self.file)  # returns audio time series, sampling rate of scale
        S_scale = librosa.stft(scale, n_fft=FRAME_SIZE, hop_length=HOP_SIZE)

        # Creating a spectrogram out of the audio
        Y_scale = np.abs(S_scale) ** 2
        self.S_db = librosa.amplitude_to_db(Y_scale, ref=np.max)
        for line in self.S_db:
            new_line = []
            for x in line:
                if -80.0 <= x <= -70.0:
                    new_line.append(0)
                elif -70.0 < x <= -60.0:
                    new_line.append(0.15)
                elif -60.0 < x <= -50.0:
                    new_line.append(0.3)
                elif -50.0 < x <= -40.0:
                    new_line.append(0.45)
                elif -40.0 < x <= -30.0:
                    new_line.append(0.6)
                elif -30.0 < x <= -20.0:
                    new_line.append(0.75)
                elif -20.0 < x <= -10.0:
                    new_line.append(0.9)
                else:
                    new_line.append(1)
            self.BinerySpec.append(new_line)
        plt.imshow(self.BinerySpec, cmap=plt.get_cmap('gray'))
        plt.axis('off')
        plt.savefig('original_spectrogram.png', bbox_inches='tight', pad_inches=0)
        plt.show()
        img = cv.imread('original_spectrogram.png')
        blur = cv.blur(img, (5, 5))
        plt.subplot(121), plt.imshow(img), plt.title('Original')
        plt.xticks([]), plt.yticks([])
        plt.subplot(122), plt.imshow(blur), plt.title('Blurred')
        plt.xticks([]), plt.yticks([])
        plt.show()

    @staticmethod
    def translate(value, src, dest):
        srcSpan = src[1] - src[0]
        destSpan = dest[1] - dest[0]
        valueScaled = float(value - src[0]) / float(srcSpan)
        return dest[0] + (valueScaled * destSpan)


if __name__ == "__main__":
    Spec().scale()
