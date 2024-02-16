from collections import defaultdict
'''
This file's job is to:
1. Creat a hash of all the trace points in the database
2. Allow to search for similar trace points in the hash
'''


class DirectionVector:
    def __init__(self, length, angle):
        """
        :param length: The length/size of the vector to the next trace point
        :param angle: The direction/angle of the vector to the next trace point
        """
        self.length = length
        self.angle = angle


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
        print(f"freq: {self.frequency}, vector: {self.direction_vector}")


class FrequencyDirectionHash:
    def __init__(self):
        """
        :self.h: The hash that consists of all the trace points info
        """
        self.h = defaultdict(dict)

    def add(self, trace_point: TracePoint):
        """
        :param trace_point: A given trace point
        :The function adds the trace point that was given to the has (self.h):
        """
        if trace_point.frequency not in self.h or not trace_point.direction_vector or trace_point.direction_vector.angle not in self.h[trace_point.frequency]:
            if trace_point.direction_vector is None:
                self.h[trace_point.frequency][None] = [trace_point]
            else:
                self.h[trace_point.frequency][trace_point.direction_vector.angle] = [trace_point]
        else:

            if trace_point.direction_vector is None:
                self.h[trace_point.frequency][None].append(trace_point)
            else:
                self.h[trace_point.frequency][trace_point.direction_vector.angle].append(trace_point)


class FrequencyMap:
    def __init__(self, fdhash: FrequencyDirectionHash):
        '''
        :param fdhash: The whole hash
        :frequencies ends as a sorted list of all the frequencies in fdhash:
        '''
        self.frequencies = []
        for freq in fdhash.h:
            self.frequencies.append(freq)
        self.frequencies.sort()


class AngleMap:
    def __init__(self, fdhash: dict):
        """
        :param fdhash: The whole hash
        :frequencies ends as a sorted list of all the frequencies in fdhash:
        """
        self.angles = []
        for angle in fdhash:
            self.angles.append(angle)
        self.angles.sort()


def build_and_add_signature(tp_list):
    """
    :builds an object of FrequencyDirectionHash:
    :return the object:
    """
    fdhash = FrequencyDirectionHash()
    for tp in tp_list:
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


def find_in_hash(fdhash: FrequencyDirectionHash, fmap_frequencies: list, tp: TracePoint) -> tuple:
    """
    :searches through the fmap (sorted frequencies):
    :if the position is bigger then the frequency it returns the closest frequency (the last or next position):
    :note - fdhash is here in case I want to return the value of the angle and not the angle itself:
    :param fdhash: The hash of the original song
    :param fmap_frequencies: list of sorted frequencies
    :param tp: The trace point from the sample we are comparing to
    :return: A tuple of the closest frequencyand angle
    """
    freq = tp.frequency
    for i in range(len(fmap_frequencies)):
        if fmap_frequencies[i] == freq:
            freq = fmap_frequencies[i]
            break
        elif fmap_frequencies[i] > freq:
            if abs(fmap_frequencies[i] - freq) < abs(freq - fmap_frequencies[i-1]):  # if difference from the next is smaller than from the prev
                freq = fmap_frequencies[i]
                break
            else:  # if difference from the prev is smaller than from the next
                freq = fmap_frequencies[i-1]
                break
    if tp.direction_vector is None:
        return freq, 0
    angle = tp.direction_vector.angle
    amap = AngleMap(fdhash.h[freq]).angles
    for i in range(len(amap)):
        if amap[i] == angle:
            return freq, amap[i]
        elif amap[i] > angle:
            if abs(amap[i] - angle) < abs(angle - amap[i-1]):  # if difference from the next is smaller than from the prev
                return freq, amap[i]
            else:  # if difference from the prev is smaller than from the next
                return freq, amap[i-1]
    return -1000, -180


def main():
    fdhash = build_and_add_signature_tmp()
    fmap = FrequencyMap(fdhash)
    t3 = TracePoint(10)
    t4 = TracePoint(7.9, DirectionVector(4, -10.1), t3)
    print(find_in_hash(fdhash, fmap.frequencies, t4))


if __name__ == "__main__":
    main()