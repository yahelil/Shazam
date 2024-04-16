import math


class Constants:
    common_delta = 1


class TracePoint:
    def __init__(self, frequency, time=None, amplitude=None, distances=None):
        """
        :param frequency: The freq in which the trace point was found
        :param time: The time in which the trace point was found
        :param amplitude: The amplitude in which the trace point was found
        :param distances: The distances from the current trace point to the next 3 trace points
        """
        self.frequency = frequency
        self.time = time
        self.amplitude = amplitude
        if distances is None:
            distances = []
        self.distances = distances

    def __str__(self):
        return f"freq: {self.frequency}, time: {self.time if self.time is not None else 'None'}, amplitude: {self.amplitude if self.amplitude is not None else 'None'}, distances: {self.distances if self.distances is not None else 'None'}"

    def __repr__(self):
        return f"freq: {self.frequency}, time: {self.time if self.time is not None else 'None'}, amplitude: {self.amplitude if self.amplitude is not None else 'None'}, distances: {self.distances if self.distances is not None else 'None'}"

    def __eq__(self, other):
        return math.isclose(self.frequency, other.frequency, abs_tol=Constants.common_delta) and math.isclose(
            self.time, other.time,
            abs_tol=Constants.common_delta / 2) and math.isclose(self.amplitude,
                                                                 other.amplitude,
                                                                 abs_tol=Constants.common_delta / 2)


