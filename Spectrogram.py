import math
import statistics
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
from Hash import build_and_add_signature, TracePoint as tp, \
    DirectionVector, FrequencyMap as fm, find_in_hash, FrequencyDirectionHash

'''
This file's job is to:
1. Create a spectrogram for a recording it finds
2. Find the peaks in the spectrogram
'''

SDB = []
DatabaseList = ["PressStart"]
FRAME_SIZE = 2048
HOP_SIZE = 1000


class Measures:
    def __init__(self, peaks_spec_list):
        self.AVERAGES_UP = []
        self.AVERAGES_DOWN = []
        self.index = []
        self.peaks_spec_list = peaks_spec_list
        self.old_range = None
        self.new_range = None

    def generateNormalizeTransformParams(self, s_db_list):
        max_max, min_min = 0, 0
        for s_db in s_db_list:
            Max, Min = np.amax(s_db), np.amin(s_db)
            if Max > max_max:
                max_max = Max
            if Min < min_min:
                min_min = Min
        self.old_range = [min_min, max_max]
        self.new_range = [0, 1]

    def save_averages(self):
        """
        note - This function is dividing the list into windows and works with each separately
        :param lst: The list of values in the spectrogram
        :saves: saves The average between average of the window to max num min num to AVERAGES_UP and DOWN
        """

        # arr = np.array(self.peaks_spec)
        # max_value, min_value = np.max(arr), np.min(arr)
        # length = len(arr[0])
        # windows = int(length / 256)
        # average_list_up = []
        # average_list_down = []
        # if length % 256 != 0:
        #     windows = windows + 1
        # jump = 0
        # next_jump = 0
        # for i in range(windows):
        #     next_jump += 256
        #     average = np.mean(arr[jump:(length if (windows - 1) else next_jump)])
        #     average_up = statistics.mean([average, max_value])
        #     average_down = statistics.mean([average, min_value])
        #     jump = next_jump
        #     average_list_up.append(average_up)
        #     average_list_down.append(average_down)
        # self.AVERAGES_UP = average_list_up
        # self.AVERAGES_DOWN = average_list_down
        #for peaks_spec in self.peaks_spec_list:
        for lst in self.peaks_spec_list:
            arr = np.array(lst)
            max_value, min_value = np.max(arr), np.min(arr)
            average = np.average(arr)
            self.AVERAGES_UP.append(statistics.mean([average, max_value]))
            self.AVERAGES_DOWN.append(statistics.mean([average, min_value]))
        # return average_list_up, average_list_down

    # def peaks(self):
    #     """ In this function all the peaks are presented on top of the spectrogram"""
    #
    #     rows, cols = len(self.peaks_spec), len(self.peaks_spec[0])
    #     for row in range(rows):
    #         for col in range(cols):
    #             if self.peaks_spec[row][col] > self.AVERAGES_UP[1]: #or 0.1 < self.peaks_spec[row][col] < AVERAGES_DOWN[int(col/256)]
    #                 self.peaks_spec[row][col] = 0.5
    #                 if row > 200:
    #                     self.index.append((col, row))
    #             else:
    #                 self.peaks_spec[row][col] = 0.0


class Spec:
    def __init__(self, song: str):
        self.name = song
        self.fmap = None
        self.tp_list = []
        self.FrequencyDirectionHash = None
        self.file = f"{song}.wav"
        self.S_db_list = []
        self.peaks_spec_list = []
        self.index = []
        self.indices_list = []
        self.best_match = 0
        self.measures = None

    def run(self, fname, measures=None):
        if measures:
            self.SpecBeforeNormilizing("sample_DB.csv")
        else:
            self.SpecBeforeNormilizing()

        require_normalization = False
        if measures is None:
            require_normalization = True
            measures = Measures(self.peaks_spec_list)
            measures.generateNormalizeTransformParams(self.S_db_list)

        self.normalizingSpec(measures.old_range, measures.new_range)
        if require_normalization:
            measures.save_averages()

        self.peaks(measures)
        self.hash(fname)

        return measures

    def compare(self, other):
        sample_hash = self.search()
        song_hash = other.search()
        print(f"song_hash: {song_hash.__str__()}\n sample_hash: {sample_hash.__str__()}")
        self.match(sample_hash, song_hash, other.fmap)

    def normalizingSpec(self, old_range, new_range):
        for S_db in self.S_db_list:
            peaks_spec = []
            for line in S_db:  # loop to create self.peaks_spec
                peaks_spec.append([self.translate(x, old_range, new_range) for x in line])
            rows, cols = len(peaks_spec), len(peaks_spec[0])
            for row in range(rows):
                for col in range(cols):
                    if row < 200:
                        peaks_spec[row][col] = 0.0
            self.peaks_spec_list.append(peaks_spec)


    def SpecBeforeNormilizing(self, fname="S_DB.csv"):
        """This function presents the spectrogram of the file after the transformation(fft)"""
        # global SDB
        # generate spectrogram
        scale, sr = librosa.load(self.file)  # returns audio time series, sampling rate of scale
        sample_length = sr*2
        sample_div_2 = int(sample_length/2)
        if fname != "S_DB.csv":
            #scale_list = [scale[:int(sample_length/2)], scale[int(sample_length/2):2*sample_length]]
            scale_list = []
            sample_length = math.floor(len(scale) / (sample_div_2))
            for x in range(sample_length):
                scale_list.append(scale[sample_div_2*x:sample_div_2*(x+1)])
        else:
            song_length = math.floor(len(scale)/(sample_div_2))  # The length in the number of times the length if the sample
            scale_list = []
            for x in range(song_length):
                scale_list.append(scale[sample_div_2*x:sample_div_2*(x+1)])
        for scale in scale_list:
            S_scale = librosa.stft(scale, n_fft=FRAME_SIZE, hop_length=HOP_SIZE)

            # Creating a spectrogram out of the audio
            Y_scale = np.power(np.abs(S_scale), 2)

            self.S_db_list.append(librosa.amplitude_to_db(Y_scale, ref=np.max))
        # file = open(fname, "w")
        # for x in self.S_db:
        #     comma = ""
        #     for y in x:
        #         if comma == "":
        #             file.write("\n")
        #         file.write(f"{comma} {y}")
        #         comma = ","
        # file.close()
        # if self.name in DatabaseList:
        #     SDB = self.S_db
        # else:
        #     self.S_db = SDB
        # # Just the spectrogram
        # plt.imshow(self.peaks_spec, cmap=plt.get_cmap('gray'))
        # plt.savefig('original_spectrogram.png', bbox_inches='tight', pad_inches=0)
        # plt.show()

    def peaks(self, measures):
        """ In this function all the peaks are presented on top of the spectrogram"""
        for peaks_spec in self.peaks_spec_list:
            rows, cols = len(peaks_spec), len(peaks_spec[0])
            for col in range(cols):
                for row in range(rows):
                    if peaks_spec[row][col] > measures.AVERAGES_UP[
                        0]:  # or 0.1 < self.peaks_spec[row][col] < AVERAGES_DOWN[int(col/256)]
                        peaks_spec[row][col] = 0.5
                        self.index.append((col, row))
                    else:
                        peaks_spec[row][col] = 0.0
        '''if self.name == "PressStart":
            print("gg")
            INDEXSONG = self.index'''
        # # The spectrogram with peaks
        # plt.imshow(self.peaks_spec, cmap=plt.get_cmap('gray'))
        # plt.savefig('original_spectrogram.png', bbox_inches='tight', pad_inches=0)
        # plt.show()

    def hash(self, fname):
        """ builds self.tp_list, self.FrequencyDirectionHashash and self.fmap """
        last_tp = None
        dirvec = None

        f = open(fname, "w")
        for i in range(len(self.index)):
            freq = self.index[i][1]
            time = self.index[i][0]
            if i == 0:
                last_tp = tp(freq)
                self.tp_list.append(last_tp)
            else:
                prev_time = self.index[i - 1][0]
                prev_freq = self.index[i - 1][1]
                #if abs(time - prev_time) >= 1:
                length = math.dist(self.index[i], self.index[i - 1])
                dirvec = DirectionVector(length, math.degrees(math.asin((freq - prev_freq) / length)))
                TracePoint = tp(freq)
                last_tp.follow = TracePoint
                last_tp.direction_vector = dirvec
                self.tp_list.append(TracePoint)
                if last_tp.direction_vector is not None:
                    f.write(f"{last_tp.frequency},{last_tp.direction_vector.angle}, {last_tp.direction_vector.length}\n")
                last_tp = TracePoint

        f.close()
        last_tp.direction_vector = dirvec
        '''for tpt in self.tp_list:
            print(tpt.__str__())'''
        if self.name in DatabaseList:
            self.FrequencyDirectionHash = build_and_add_signature(self.tp_list)
            self.fmap = fm(self.FrequencyDirectionHash).frequencies
        # plt.scatter(x, y, color="gray", s=5)
        # plt.show()
        # print(f"tp_list: {self.tp_list}, FrequencyDirectionHashash: {self.FrequencyDirectionHashash}, fmap: {self.fmap}")

    def search(self):
        """
        :return: the hash of the song/sample
        """
        if self.name not in DatabaseList:
            return self.tp_list
        song_hash = FrequencyDirectionHash()
        for tp in self.tp_list:
            song_hash.add(tp)
        return song_hash

    def indices(self, list1, list2):
        index = 1
        for t in list1[1:]:
            if math.isclose(t[0], list2[1][0], abs_tol=10) and math.isclose(t[1], list2[1][1], abs_tol=5):
                self.indices_list.append(index)
            index += 1

    def match(self, tp_sample, hash_song, song_fmap):
        # list2 = list1[100:200]
        # self.indices(list1, list2)

        current_tp = tp_sample[0]  # The starting tp
        tp_list = find_in_hash(hash_song, song_fmap, current_tp)
        # tp_sample = []
        # p = tp_list[0]
        # for i in range(200):
        #     tp_sample.append(p)
        #     p = p.follow
        self.best_match = 0
        winner_tp_song = None
        for tp_song in tp_list:
            matches = 0
            total = 0
            current_tp = tp_sample[0]
            starter = tp_song
            while current_tp is not None and tp_song is not None:  # not the last tp
                total += 1
                if current_tp == tp_song:
                    matches += 1
                current_tp = current_tp.follow
                tp_song = tp_song.follow
                # if total == 20:
                #     break
            if total > 0 and self.best_match < (matches/total) * 100:
                self.best_match = (matches/total) * 100
                winner_tp_song = starter
            print(f"total = {total}, matchws = {matches}")
            print(f"The match percentage is { (matches/total) * 100 }%")

        print(f"The best match percentage is { self.best_match }%")
        file = open("tp_sample.csv", "w")
        file_song = open("tp_song.csv", "w")
        tp = tp_sample[0]
        tp_song = winner_tp_song
        while tp is not None and tp_song is not None:
            file.write(f"{tp.frequency},{tp.direction_vector.angle}, {tp.direction_vector.length}\n")
            tp = tp.follow
            file_song.write(f"{tp_song.frequency},{tp_song.direction_vector.angle}, {tp_song.direction_vector.length}\n")
            tp_song = tp_song.follow
        # print(f"indices: {self.indices_list}")
        # total = 0
        # for index in self.indices_list:
        #     success = 0
        #     total = 0
        #     tp_src = list1[index]
        #     tp_dst = list2[1]
        #     for tuples in zip(list1[index:], list2[1:]):
        #         if math.isclose(tuples[0][0], tuples[1][0], abs_tol=10) and math.isclose(tuples[0][1], tuples[1][1],
        #                                                                                  abs_tol=5):
        #             success += 1
        #         total += 1
        #     match = success / total * 100
        #     if self.best_match < match:
        #         self.best_match = match
        #         print(f"index = {index}\nsuccess = {success}\ntotal = {total}\n")
        #     self.best_match = max(self.best_match, match)
        # if total == 0:
        #     print(f"The match percentage is 0%")
        # else:
        #     print(f"The match percentage is {self.best_match}%")

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

    # @staticmethod
    # def save_averages(lst):
    #     """
    #     note - This function is dividing the list into windows and works with each separately
    #     :param lst: The list of values in the spectrogram
    #     :saves: saves The average between average of the window to max num min num to AVERAGES_UP and DOWN
    #     """
    #
    #
    #     arr = np.array(lst)
    #     max_value, min_value = np.max(arr), np.min(arr)
    #     length = len(arr[0])
    #     windows = int(length / 256)
    #     average_list_up = []
    #     average_list_down = []
    #     if length % 256 != 0:
    #         windows = windows + 1
    #     jump = 0
    #     next_jump = 0
    #     for i in range(windows):
    #         next_jump += 256
    #         average = np.mean(arr[jump:(length if (windows - 1) else next_jump)])
    #         average_up = statistics.mean([average, max_value])
    #         average_down = statistics.mean([average, min_value])
    #         jump = next_jump
    #         average_list_up.append(average_up)
    #         average_list_down.append(average_down)
    #     AVERAGES_UP = average_list_up
    #     AVERAGES_DOWN = average_list_down
    #     # return average_list_up, average_list_down


if __name__ == "__main__":
    p1 = Spec("PressStart")
    measures = p1.run("song.csv")

    p2 = Spec("sample28")
    p2.run("sample.csv", measures)

    p2.compare(p1)
    # g = Spec("Symbolism")
    # g.run()