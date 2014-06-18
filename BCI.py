
from __future__ import print_function, absolute_import, unicode_literals, division

from .buffer import DSI_Packet_Buffer

from numpy.fft import fft
from uuid import uuid4
import socket

import logging

packet_logger = logging.getLogger('DSI_packets')
packet_logger.setLevel(logging.INFO)
packet_logger.addHandler(logging.NullHandler())

logger = logging.getLogger(__name__)


class BCI_Session(object):

    def __init__(self, channel_list, ip_address='localhost', port=8844, data_file=None):

        self.id = uuid4()

        if data_file is not None:
            fh = logging.FileHandler(data_file)
            fh.setLevel(logging.INFO)
            self._logger = packet_logger.getChild(self.id)
            self._logger.addHandler(fh)
        else:
            self._logger = packet_logger

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(2)
        logger.debug('Connecting to %s:%s', ip_address, port)
        self._socket.connect((ip_address, port))
        self._packet_stream = DSI_Packet_Buffer(self._socket)

        self._sensor_map = []
        self.sample_frequency = float('nan')

        packet = self._packet_stream.next()
        while packet.type == 'EVENT':
            self.log(packet)
            if packet.code == 'VERSION':
                packet = self._packet_stream.next()
                continue
            if packet.code == 'SENSOR_MAP':
                self._sensor_map = packet.message.strip().split(',')
            elif packet.code == 'DATA_RATE':
                self.sample_frequency = int(packet.message.strip().split(',')[1])

            packet = self._packet_stream.next()

        self._channel_map = dict()
        for channel in channel_list:
            index = self._sensor_map.index(channel)
            self._channel_map[channel] = index

        self._data_buffers = dict((channel, []) for channel in channel_list)

        self._process_packet(packet)

    def _process_packet(self, packet):
        #print('{0}: {1!r}\n'.format(self.id, packet))
        self.log(packet)
        if not packet.type == 'EEG_DATA':
            raise ValueError('Wrong packet type')
        for channel, index in self._channel_map.iteritems():
            self._data_buffers[channel].append(packet.data[index])

    def acquire_data(self, count=1):
        while count:
            self._process_packet(self._packet_stream.next())
            count -= 1

    def channel(self, channel):
        return self._data_buffers[channel]

    def log(self, packet):
        self._logger.info(packet)


def transform(data, sample_size, sample_frequency):
    transform = fft(data[-int(sample_size):])
    power = abs(transform[1:int(sample_size/2)])**2
    frequencies = [i/(sample_size/2)*(sample_frequency/2) for i in range(1, int(sample_size/2))]
    return zip(frequencies, power)

