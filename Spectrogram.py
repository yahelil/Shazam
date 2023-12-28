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
        self.BinarySpec = []

    def scale(self):
        scale, sr = librosa.load(self.file)  # returns audio time series, sampling rate of scale
        S_scale = librosa.stft(scale, n_fft=FRAME_SIZE, hop_length=HOP_SIZE)

        # Creating a spectrogram out of the audio
        Y_scale = np.abs(S_scale) ** 2
        self.S_db = librosa.amplitude_to_db(Y_scale, ref=np.max)
        Max, Min = self.max_spec(self.S_db)
        for line in self.S_db:
            old_range = [Min, Max]
            new_range = [0, 1]
            self.BinarySpec.append([self.translate(x, old_range, new_range)for x in line])
        plt.imshow(self.BinarySpec, cmap=plt.get_cmap('gray'))
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
    def max_spec(lst):
        mymax = -80
        mymin = 0
        rows = len(lst)
        col = len(lst[0])
        for i in range(rows):
            for j in range(col):
                mymax = max(mymax, lst[i][j])
                mymin = min(mymin, lst[i][j])
        print(mymax, mymin)
        return mymax, mymin

    @staticmethod
    def translate(value, src, dest):
        srcSpan = src[1] - src[0]
        destSpan = dest[1] - dest[0]
        valueScaled = float(value - src[0]) / float(srcSpan)
        return dest[0] + (valueScaled * destSpan)


if __name__ == "__main__":
    Spec().scale()
