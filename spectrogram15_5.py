import csv
import math
import statistics
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
import scipy.io.wavfile

from Hash import build_and_add_signature, TracePoint as tracepoint, \
    DirectionVector, FrequencyMap as fm, find_in_hash, FrequencyDirectionHash

'''
This file's job is to:
1. Create a spectrogram for a recording it finds
2. Find the peaks in the spectrogram
'''

SDB = []
DatabaseList = ["PressStart", "FireToTheRain", "HereComesTheSun", "Yesterday", "LetItBe", "LAMinorChord"]
FRAME_SIZE = 2048
HOP_SIZE = 50
LOWFREQTHRESHOLD = 50
MINIMUM_TOTAL = 3


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
    j = 0
    def __init__(self, song: str):
        self.name = song
        self.fmap = None
        self.tp_lists_list = []
        self.FrequencyDirectionHash = FrequencyDirectionHash()
        self.file = f"database/{song}.wav"
        self.S_db_list = []
        self.peaks_spec_list = []
        self.index_list = []
        self.indices_list = []
        self.best_match = 0
        self.measures = None
        self.matches_list = []

    def run(self, measures=None):
        if measures:
            self.spec_before_normalizing("sample_DB.csv")
        else:
            self.spec_before_normalizing()

        require_normalization = False
        if measures is None:
            require_normalization = True
            measures = Measures(self.peaks_spec_list)
            measures.generateNormalizeTransformParams(self.S_db_list)

        self.normalizing_spec(measures.old_range, measures.new_range, self.file)
        if require_normalization:
            measures.save_averages()

        self.peaks(measures)
        self.dominante()
        self.hash()

        return measures

    def compare(self, other):
        sample_hash = self.search()
        song_hash = other.search()
        #print(f"song_hash: {song_hash.__str__()}\n sample_hash: {sample_hash.__str__()}")
        self.match_matches(sample_hash, song_hash, other.fmap)

    def normalizing_spec(self, old_range, new_range, fname):
        for S_db in self.S_db_list:
            peaks_spec = []
            for line in S_db:  # loop to create self.peaks_spec
                peaks_spec.append([self.translate(x, old_range, new_range) for x in line])
            rows, cols = len(peaks_spec), len(peaks_spec[0])
            for row in range(rows):
                for col in range(cols):
                    if row < LOWFREQTHRESHOLD:
                        peaks_spec[row][col] = 0.0
            self.peaks_spec_list.append(peaks_spec)
            a=37

            # # Just the spectrogram

            #j = 0
            # for peaks_spec in self.peaks_spec_list:
            #     doubeld_peak_list = []
            #     doubled_peaks_spec = []
            #     for peak_list in peaks_spec:
            #         for peak in peak_list:
            #             for i in range(30):
            #                 doubeld_peak_list.append(peak)
            #         doubled_peaks_spec.append(doubeld_peak_list)
            #         doubeld_peak_list = []
            #
            #     if fname != "database/PressStart.wav":
            #         plt.figure(figsize=(7, 7))
            #         plt.imshow(doubled_peaks_spec, cmap=plt.get_cmap('gray'))
            #         plt.savefig(f'RecordSpecPictures/pic{Spec.j}.png', bbox_inches='tight', pad_inches=0)
            #         plt.show()
            #         Spec.j += 1


    def spec_before_normalizing(self, fname="S_DB.csv"):
        """This function presents the spectrogram of the file after the transformation(fft)"""
        # global SDB
        # generate spectrogram
        scale, sr = librosa.load(self.file)  # returns audio time series, sampling rate of scale
        sample_length = sr*2
        sample_div_2 = int((sample_length+1)/2)
        if fname != "S_DB.csv":
            scale_list = []

            sample_div_parts = math.floor(scale.size / sample_div_2)
            for x in range(sample_div_parts):
                for y in range(sample_div_2*x, sample_div_2*(x+1), int((sample_div_2+1)/2)):
                    #print(f"sample range {y} - {y+sample_div_2}")
                    if y+sample_div_2 <= scale.size:
                        scale_list.append(scale[y:y+sample_div_2])
        else:
            song_length = math.floor(scale.size/sample_div_2)  # The length in the number of times the length if the sample
            scale_list = []
            for x in range(song_length):
                #print(f"song range {sample_div_2*x} - {sample_div_2*(x+1)}")
                scale_list.append(scale[sample_div_2*x:sample_div_2*(x+1)])
        for scale in scale_list:
            S_scale = librosa.stft(scale, n_fft=FRAME_SIZE, hop_length=HOP_SIZE)

            # Creating a spectrogram out of the audio
            Y_scale = np.power(np.abs(S_scale), 2)

            self.S_db_list.append(librosa.amplitude_to_db(Y_scale, ref=np.max))
        # # Just the spectrogram
        # plt.imshow(self.peaks_spec, cmap=plt.get_cmap('gray'))
        # plt.savefig('original_spectrogram.png', bbox_inches='tight', pad_inches=0)
        # plt.show()

    def peaks(self, measures):
        """ In this function all the peaks are presented on top of the spectrogram"""

        for peaks_spec in self.peaks_spec_list:
            index = []
            rows, cols = len(peaks_spec), len(peaks_spec[0])
            for col in range(100, cols):
                for row in range(rows):
                    if peaks_spec[row][col] > measures.AVERAGES_UP[
                        0]:  # or 0.1 < self.peaks_spec[row][col] < AVERAGES_DOWN[int(col/256)]
                        index.append((row, col, peaks_spec[row][col]))
                    else:
                        peaks_spec[row][col] = 0.0
            self.index_list.append(index)
        # # The spectrogram with peaks
        # plt.imshow(self.peaks_spec, cmap=plt.get_cmap('gray'))
        # plt.savefig('original_spectrogram.png', bbox_inches='tight', pad_inches=0)
        # plt.show()

    def dominante(self):
        """removes all the non-dominant trace points from self.index_list"""
        position_counter = -1
        new_index_list = []
        for index in self.index_list:
            position_counter += 1
            tp_last_dominant = None
            remove_list = []
            for i in range(len(index)):
                time = index[i][1]
                freq = index[i][0]
                amplitude = self.peaks_spec_list[position_counter][freq][time]
                TracePoint = tracepoint(freq, time, amplitude)
                if tp_last_dominant is None:
                    tp_last_dominant = TracePoint
                elif tp_last_dominant.time == TracePoint.time:
                    if amplitude > tp_last_dominant.amplitude:
                        remove_list.append(tp_last_dominant)
                        tp_last_dominant = TracePoint
                    else:
                        remove_list.append(TracePoint)
                else:
                    tp_last_dominant = TracePoint
            for tp in remove_list:
                tuple_to_remove = (tp.frequency, tp.time, tp.amplitude)
                if tuple_to_remove in index:
                    index.remove(tuple_to_remove)
            new_index_list.append(index)
        self.index_list = new_index_list
        a=3

    def hash(self):
        """ builds self.tp_list, self.FrequencyDirectionHashash and self.fmap """
        tp_list = []
        for index in self.index_list:
            last_tp = None
            dirvec = None
            tp_list = []
            for i in range(len(index)):
                freq = index[i][1]
                if i == 0:
                    last_tp = tracepoint(freq)
                    tp_list.append(last_tp)
                else:
                    prev_freq = index[i - 1][1]
                    length = math.dist(index[i], index[i - 1])
                    dirvec = DirectionVector(length, math.degrees(math.asin((freq - prev_freq) / length)))
                    TracePoint = tracepoint(freq)
                    last_tp.follow = TracePoint
                    last_tp.direction_vector = dirvec
                    tp_list.append(TracePoint)
                    last_tp = TracePoint
            if last_tp is not None:
                last_tp.direction_vector = dirvec
            self.tp_lists_list.append(tp_list)
        if self.name in DatabaseList:
            for tp_list in self.tp_lists_list:
                build_and_add_signature(self.FrequencyDirectionHash, tp_list)
            self.fmap = fm(self.FrequencyDirectionHash).frequencies

        # plt.scatter(x, y, color="gray", s=5)
        # plt.show()

    def search(self):
        """
        :return: the hash of the song/sample
        """
        file = open('mydata.csv', 'w')
        files = csv.writer(file)
        if self.name not in DatabaseList:
            files.writerow(['Name', 'Age', 'Enrollment Number'])
            files.writerow(self.tp_lists_list)
            return self.tp_lists_list
        song_hash = FrequencyDirectionHash()
        for tp_list in self.tp_lists_list:
            for tp in tp_list:  # The last added value
                song_hash.add(tp)
        file.close()
        return song_hash

    def match(self, tp_sample, hash_song, song_fmap):
        current_tp = tp_sample[0]  # The starting tp
        tp_list = find_in_hash(hash_song, song_fmap, current_tp)
        best_match = 0
        for tp_song in tp_list:
            matches = 0
            total = 0
            current_tp = tp_sample[0]
            while current_tp is not None and tp_song is not None:  # not the last tp
                total += 1
                if current_tp == tp_song:
                    matches += 1
                current_tp = current_tp.follow
                tp_song = tp_song.follow
            if total > MINIMUM_TOTAL and best_match < (matches/total) * 100:
                best_match = (matches/total) * 100
                self.matches_list.append((matches/total) * 100)
                print(f"match: {matches}, total: {total}")
        return best_match

    def match_matches(self, tp_samples, hash_song, song_fmap):
        for tp_sample in tp_samples:
            if tp_sample:
                new_match = self.match(tp_sample, hash_song, song_fmap)
                if new_match > self.best_match:
                    self.best_match = new_match
        #standard_dev = statistics.stdev(self.matches_list)
        print(f"The best match percentage is {self.best_match}%")
        #print(f"The Standard Deviation is {standard_dev}")

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


if __name__ == "__main__":
    p1 = Spec(DatabaseList[-2])
    measures = p1.run()

    p2 = Spec("LetItBe1")
    #p2 = Spec("realsamplesymbolism")
    #p2 = Spec("sample1.5-6.5")
    p2.run(measures)

    p2.compare(p1)
    # g = Spec("Symbolism")
    # g.run()