import math
import statistics
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
from Hash import build_and_add_signature as baas, TracePoint as tp, \
    DirectionVector as dv, FrequencyMap as fm, find_in_hash as fih

'''
This file's job is to:
1. Create a spectrogram for a recording it finds
2. Find the peaks in the spectrogram
'''

AVERAGES_UP = []
AVERAGES_DOWN = []
INDEXSONG = []
DatabaseList = ["PressStart"]
FRAME_SIZE = 2048
HOP_SIZE = 1000


class Spec:
    def __init__(self, song: str):
        self.name = song
        self.fmap = None
        self.tp_list = []
        self.fdhash = None
        self.file = f"database/{song}.wav"
        self.S_db = None
        self.PeaksSpec = []
        self.index = []
        self.indices_list = []
        self.best_match = 0

    def run(self):
        self.spec()
        self.peaks()
        self.hash()
        song_hash = self.search()
        #self.__init__("sample2")
        self.__init__("PressStartCut2")
        self.spec()
        self.peaks()
        self.hash()
        sample_hash = self.search()
        print(f"song_hash: {song_hash}\n sample_hash: {sample_hash}")
        self.match(song_hash, sample_hash)

    def spec(self):
        """This function presents the spectrogram of the file after the transformation(fft)"""

        # generate spectrogram
        scale, sr = librosa.load(self.file)  # returns audio time series, sampling rate of scale
        S_scale = librosa.stft(scale, n_fft=FRAME_SIZE, hop_length=HOP_SIZE)

        # Creating a spectrogram out of the audio
        Y_scale = np.abs(S_scale) ** 2
        self.S_db = librosa.amplitude_to_db(Y_scale, ref=np.max)
        Max, Min = np.amax(self.S_db), np.amin(self.S_db)
        old_range = [Min, Max]
        new_range = [0, 1]
        for line in self.S_db:   # loop to create self.PeaksSpec
            self.PeaksSpec.append([self.translate(x, old_range, new_range)for x in line])
        rows, cols = len(self.PeaksSpec), len(self.PeaksSpec[0])
        for row in range(rows):
            for col in range(cols):
                if row < 200:
                    self.PeaksSpec[row][col] = 0.0
        # # Just the spectrogram
        # plt.imshow(self.PeaksSpec, cmap=plt.get_cmap('gray'))
        # plt.savefig('original_spectrogram.png', bbox_inches='tight', pad_inches=0)
        # plt.show()

    def peaks(self):
        """ In this function all the peaks are presented on top of the spectrogram"""
        global INDEXSONG
        # seeking peaks
        rows, cols = len(self.PeaksSpec), len(self.PeaksSpec[0])
        x = []
        y = []
        if self.name in DatabaseList:
            self.save_averages(self.PeaksSpec)
        for row in range(rows):
            for col in range(cols):
                if self.PeaksSpec[row][col] > AVERAGES_UP[int(col/256)]: #or 0.1 < self.PeaksSpec[row][col] < AVERAGES_DOWN[int(col/256)]
                    self.PeaksSpec[row][col] = 0.5
                    if row > 200:
                        x.append(col)
                        y.append(row)
                        self.index.append((col, row))
                else:
                    self.PeaksSpec[row][col] = 0.0
        '''if self.name == "PressStart":
            print("gg")
            INDEXSONG = self.index'''
        # # The spectrogram with peaks
        #plt.imshow(self.PeaksSpec, cmap=plt.get_cmap('gray'))
        #plt.savefig('original_spectrogram.png', bbox_inches='tight', pad_inches=0)
        #plt.show()

    def hash(self):
        """ builds self.tp_list, self.fdhash and self.fmap """
        #self.index = INDEXSONG
        for i in range(len(self.index)):
            freq = self.index[i][0]
            prev_freq = self.index[i-1][0]
            #print(f"freq: {freq}, next: {next_freq}")
            if abs(freq - prev_freq) >= 1:
                #print(f"after:\nfreq: {freq}, next: {prev_freq}")
                length = math.dist(self.index[i], self.index[i-1])
                TracePoint = tp(freq) if i == 0 else tp(freq, dv(length, math.degrees(math.asin(abs(prev_freq-freq)/length))))
                self.tp_list.append(TracePoint)
        '''for tpt in self.tp_list:
            print(tpt.__str__())'''
        self.fdhash = baas(self.tp_list)
        self.fmap = fm(self.fdhash)
        # plt.scatter(x, y, color="gray", s=5)
        # plt.show()
        # print(f"tp_list: {self.tp_list}, fdhash: {self.fdhash}, fmap: {self.fmap}")

    def search(self):
        """
        :return: the hash of the song/sample
        """
        hash = []
        for tp in self.tp_list:
            hash.append(fih(self.fdhash, self.fmap.frequencies, tp))
        return hash

    def indices(self, list1, list2):
        index = 1

        for t in list1[1:]:
            if math.isclose(t[0], list2[1][0], abs_tol=2) and math.isclose(t[1], list2[1][1], abs_tol=2):
                self.indices_list.append(index)
            index += 1

    def match(self, list1, list2):
        #list2 = list1[100:200]
        self.indices(list1, list2)
        print(self.indices_list)
        total = 0
        for index in self.indices_list:
            success = 0
            total = 0
            for tuples in zip(list1[index:], list2[1:]):
                #print(f"freq diff = {tuples[0][0], tuples[1][0]}, andle diff = {tuples[0][0], tuples[1][0]}")
                if math.isclose(tuples[0][0], tuples[1][0], abs_tol=10) and math.isclose(tuples[0][1], tuples[1][1], abs_tol=5):
                    success += 1

                total += 1
                #print(f"total - success = {total} - {success}")

            match = success/total * 100
            if self.best_match < match:
                self.best_match = match
            self.best_match = max(self.best_match, match)
            #print("___________________________________________________")
        if total == 0:
            print(f"The match percentage is 0%")
        else:
            print(f"The match percentage is {self.best_match}%")

    @staticmethod
    def translate(value, src, dest):
        """
        :param value: an element in S_db
        :param src: The range to list used to be
        :param dest: The range we want the list to be
        :return: The value in the same ratio but in the new range
        """
        srcSpan = src[1] - src[0]
        destSpan = dest[1] - dest[0]
        valueScaled = float(value - src[0]) / float(srcSpan)
        return dest[0] + (valueScaled * destSpan)

    @staticmethod
    def save_averages(lst):
        """
        note - This function is dividing the list into windows and works with each separately
        :param lst: The list of values in the spectrogram
        :saves: saves The average between average of the window to max num min num to AVERAGES_UP and DOWN
        """

        global AVERAGES_UP, AVERAGES_DOWN

        arr = np.array(lst)
        max_value, min_value = np.max(arr), np.min(arr)
        length = len(arr[0])
        windows = int(length / 256)
        average_list_up = []
        average_list_down = []
        if length % 256 != 0:
            windows = windows + 1
        jump = 0
        next_jump = 0
        for i in range(windows):
            next_jump += 256
            average = np.mean(arr[jump:(length if (windows - 1) else next_jump)])
            average_up = statistics.mean([average, max_value])
            average_down = statistics.mean([average, min_value])
            jump = next_jump
            average_list_up.append(average_up)
            average_list_down.append(average_down)
        AVERAGES_UP = average_list_up
        AVERAGES_DOWN = average_list_down
        #return average_list_up, average_list_down


if __name__ == "__main__":
    p = Spec("PressStart")
    p.run()
    # g = Spec("Symbolism")
    # g.run()


