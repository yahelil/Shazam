import math
from collections import defaultdict
import numpy as np
'''
This file's job is to:
1. Creat a hash of all the trace points in the database
    2. Allow to search for similar trace points in the hash
'''


class Constants:
    common_delta = 2


class DirectionVector:
    def __init__(self, length, angle):
        """
        :param length: The length/size of the vector to the next trace point
        :param angle: The direction/angle of the vector to the next trace point
        """
        self.length = length
        self.angle = angle

    def __str__(self):
        print(f"length: {self.length}, angle: {self.angle}")


class TracePoint:
    def __init__(self, frequency, direction_vector=None, follow=None, song=None):
        """
        :param frequency: The freq in which the trace point was found
        :param direction_vector: The vector to the next trace point; see class DirectionVector
        :param follow: The next trace point
        :param song: The name of the song in which the trace point was found
        """
        self.frequency = frequency
        self.direction_vector = direction_vector
        self.follow = follow
        self.song = song

    def set_dir(self, direction_vector):
        self.direction_vector = direction_vector

    def __str__(self):
        return f"freq: {self.frequency}, vector: {self.direction_vector.angle if self.direction_vector is not None else 'None'}"

    def __repr__(self):
        return f"freq: {self.frequency}, vector: {self.direction_vector.angle if self.direction_vector is not None else 'None'}"

    def __eq__(self, other):
        return math.isclose(self.frequency, other.frequency, abs_tol=Constants.common_delta) and math.isclose(self.direction_vector.angle, other.direction_vector.angle, abs_tol=Constants.common_delta)


class FrequencyDirectionHash:
    def __init__(self):
        """
        :self.h: The hash that consists of all the trace points info
        """
        self.h = defaultdict(dict)

    def __str__(self):
        return self.h

    def add(self, trace_point: TracePoint):
        """
        :param trace_point: A given trace point
        :The function adds the trace point that was given to the has (self.h):
        """
        freq = round(trace_point.frequency)
        if trace_point.direction_vector is not None:
            angle = round(trace_point.direction_vector.angle)
        else:
            angle = None

        if freq not in self.h:
            self.h[freq] = {}

        if angle not in self.h[freq]:
            # if angle is None:
            #     self.h[freq][None] = [trace_point]
            # else:
            self.h[freq][angle] = [trace_point]
        else:
            self.h[freq][angle].append(trace_point)

    def get_closest_freq(self, freq, delta, dirvec, angle=None):
        #(f"closest -------------------- freq = {freq}")
        freq = round(freq)
        lst = []
        angle = round(angle)
        for i in range(freq-delta, freq+delta+1):
            if i in self.h:
                for j in range(angle-delta, angle+delta+1):
                    if j in self.h[i]:
                        for tp in self.h[i][j]:
                            if math.fabs(dirvec.length-tp.direction_vector.length) < Constants.common_delta:
                                lst.append(tp)
        return lst


class FrequencyMap:
    def __init__(self, fdhash: FrequencyDirectionHash):
        '''
        :param fdhash: The whole hash
        :frequencies ends as a list of all the frequencies in fdhash:
        '''
        self.frequencies = []
        for freq in list(fdhash.h.keys()):
            self.frequencies.append(freq)


class AngleMap:
    def __init__(self, fdhash: dict):
        """
        :param fdhash: The whole hash
        :frequencies ends as a list of all the frequencies in fdhash:
        """
        self.angles = []
        for angle in fdhash:
            if angle is not None:
                self.angles.append(angle)


def build_and_add_signature(fdhash: FrequencyDirectionHash, tp_list):
    """
    :builds an object of FrequencyDirectionHash:
    :return the object:
    """
    for tp in tp_list:
        if tp.direction_vector is None:
            continue

        fdhash.add(tp)

    return fdhash


def build_and_add_signature_tmp():
    """
    :builds an object of FrequencyDirectionHash:
    :return the object:
    """
    fdhash = FrequencyDirectionHash()
    t1 = TracePoint(7)
    t2 = TracePoint(7.6, DirectionVector(4, 30), t1)
    t3 = TracePoint(10, DirectionVector(4, 10), t2)
    t4 = TracePoint(8, DirectionVector(4, 20), t3)
    fdhash.add(t1)
    fdhash.add(t2)
    fdhash.add(t3)
    fdhash.add(t4)

    return fdhash


def find_in_hash(fdhash: FrequencyDirectionHash, fmap_frequencies: list, tp: TracePoint) -> list:
    """
    :searches through the fmap (sorted frequencies):
    :if the position is bigger then the frequency it returns the closest frequency (the last or next position):
    :note - fdhash is here in case I want to return the value of the angle and not the angle itself:
    :param fdhash: The hash of the original song
    :param fmap_frequencies: list of frequencies
    :param tp: The trace point from the sample we are comparing to
    :return: list of all the tp that can be the start
    """
    freq = tp.frequency
    minfreq = fmap_frequencies[np.absolute(np.asarray(fmap_frequencies) - freq).argmin()]

    angle = tp.direction_vector.angle
    amap = list(fdhash.h[minfreq].keys())
    if not amap:
        return amap
    minangle = amap[np.absolute(np.asarray(amap) - angle).argmin()]
    lst = fdhash.get_closest_freq(minfreq, Constants.common_delta, tp.direction_vector, minangle)

    if round(angle) != minangle and (2*angle - minangle) in fdhash.h[minfreq]:
        lst += fdhash.get_closest_freq(minfreq, Constants.common_delta, tp.direction_vector, (2*angle - minangle))

    if round(freq) != minfreq and 2*freq-minfreq in fmap_frequencies:
        minfreq_opposite = 2*freq-minfreq

        amap = list(fdhash.h[minfreq_opposite].keys())
        minangle = amap[np.absolute(np.asarray(amap) - angle).argmin()]
        lst += fdhash.get_closest_freq(minfreq_opposite, Constants.common_delta, tp.direction_vector, minangle)

        if round(angle) != minangle and (2 * angle - minangle) in fdhash.h[minfreq]:
            lst += fdhash.get_closest_freq(minfreq_opposite, Constants.common_delta, tp.direction_vector, (2 * angle - minangle))
    return lst


def main():
    fdhash = build_and_add_signature_tmp()
    fmap = FrequencyMap(fdhash)
    t3 = TracePoint(10)
    t4 = TracePoint(7.9, DirectionVector(4, -10.1), t3)
    print(find_in_hash(fdhash, fmap.frequencies, t4))


if __name__ == "__main__":
    main()