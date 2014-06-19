
from __future__ import print_function, absolute_import, unicode_literals, division

from .parser import DSI_streamer_packet

import numpy
from uuid import uuid4
import socket

import logging

packet_logger = logging.getLogger('DSI_packets')
packet_logger.setLevel(logging.INFO)
packet_logger.addHandler(logging.NullHandler())

LOG = logging.getLogger(__name__)


class BCI_Session(object):

    def __init__(self, log_file=None, ip_address='localhost', port=8844, timeout=5):

        self.id = uuid4()

        # Setup logging
        if log_file is not None:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.INFO)
            self._logger = packet_logger.getChild(self.id)
            self._logger.addHandler(fh)
        else:
            self._logger = packet_logger

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(timeout)
        LOG.debug('Connecting to %s:%s', ip_address, port)
        self._socket.connect((ip_address, port))
        self._socket_file = self._socket.makefile()

        self.sample_frequency = float('nan')

    def acquire_data(self, duration=0.5):
        packet_count = int(self.sample_frequency * duration)
        while packet_count > 0:
            packet_count -= 1
            packet = self.next_packet()
            # TODO: Stuff with packet


    def next_packet(self):
        packet = DSI_streamer_packet.parse_stream(self._socket_file)
        while packet.type is "NULL":  # Silently drop NULL packets
            packet = DSI_streamer_packet.parse_stream(self._socket_file)
        self.log(repr(packet))
        return packet

    def log(self, packet):
        self._logger.info(packet)


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

