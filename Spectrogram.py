import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt

FRAME_SIZE = 2048
HOP_SIZE = 100


class Spec:
    def __init__(self):
        self.file = "audio/eyal4.wav"
        self.S_db = None
        self.PeaksSpec = []

    def scale(self):
        scale, sr = librosa.load(self.file)  # returns audio time series, sampling rate of scale
        S_scale = librosa.stft(scale, n_fft=FRAME_SIZE, hop_length=HOP_SIZE)

        # Creating a spectrogram out of the audio
        Y_scale = np.abs(S_scale) ** 2
        self.S_db = librosa.amplitude_to_db(Y_scale, ref=np.max)
        Max, Min = self.max_spec(self.S_db)
        old_range = [Min, Max]
        new_range = [0, 1]
        for line in self.S_db:
            self.PeaksSpec.append([self.translate(x, old_range, new_range)for x in line])
        peaks = self.peaks(self.PeaksSpec)
        rows, cols = len(self.PeaksSpec), len(self.PeaksSpec[0])
        x = []
        y = []
        for row in range(rows):
            if all(num == 0 for num in self.PeaksSpec[row]):
                stop = -1 * (len(self.PeaksSpec) - row)
                self.PeaksSpec = self.PeaksSpec[:stop]
                break
            for col in range(cols):
                if self.PeaksSpec[row][col] > peaks[-1]:
                    self.PeaksSpec[row][col] = 0.5
                    if row > 3:
                        x.append(col)
                        y.append(row)
                else:
                    self.PeaksSpec[row][col] = 0.0
        # Just the spectrogram
        plt.imshow(self.PeaksSpec, cmap=plt.get_cmap('gray'))
        plt.savefig('original_spectrogram.png', bbox_inches='tight', pad_inches=0)
        plt.show()
        # The spectrogram with peaks
        plt.imshow(self.PeaksSpec, cmap=plt.get_cmap('gray'))
        plt.savefig('original_spectrogram.png', bbox_inches='tight', pad_inches=0)
        plt.scatter(x, y, color="red", s=3)
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
        return mymax, mymin

    @staticmethod
    def translate(value, src, dest):
        srcSpan = src[1] - src[0]
        destSpan = dest[1] - dest[0]
        valueScaled = float(value - src[0]) / float(srcSpan)
        return dest[0] + (valueScaled * destSpan)

    @staticmethod
    def peaks(lst):
        arr = np.array(lst)
        origin = arr
        partition = np.argpartition(origin.ravel(), -3500)[-3500:]
        max_ten = origin[partition // 1025, partition % 1103]
        return max_ten


if __name__ == "__main__":
    Spec().scale()
