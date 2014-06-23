
import numpy

def transform(data, sample_frequency):
    """
    Compute a Fast Fourier Transform (FFT) of a given data set.

    :param data:
    :param sample_frequency:
    :return:
    """
    transformed = numpy.fft.fft(data)
    frequencies = numpy.fft.fftfreq(len(data), 1/sample_frequency)
    return frequencies, transformed

