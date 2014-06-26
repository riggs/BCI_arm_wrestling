
from __future__ import print_function, absolute_import, division

import numpy


def running_average_coro():
    """
    A coroutine to compute a running average.

    Because of the peculiarities of python generator functions, this function acts more like a class. Call it to
    instantiate a new coroutine and initialize the coroutine using 'next'. Once it's operational, sending it a value
    (via it's .send method) will return the running average of everything it's been sent.
    """
    sum = 0.0
    count = 0
    value = yield (float('nan'))
    while True:
        sum += value
        count += 1
        value = yield (sum / count)


def fft(data, sample_frequency):
    """
    Compute a Fast Fourier Transform (FFT) of a given data set.

    :param data:
    :param sample_frequency:
    :return:
    """
    amplitudes = numpy.fft.fft(data)
    frequencies = numpy.fft.fftfreq(len(data), 1/sample_frequency)
    return frequencies, amplitudes

def fft_power(data, sample_frequency):
    frequencies, amplitudes = fft(data, sample_frequency)
    power = numpy.square(numpy.abs(amplitudes))
    return zip(frequencies, power)
