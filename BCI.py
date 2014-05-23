
from __future__ import print_function, absolute_import, unicode_literals, division

from .buffer import PacketBuffer

from numpy.fft import fft
import socket

class BCI_Session(object):

    def __init__(self, channel_list, ip_address='localhost', port=8844):

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((ip_address, port))
        self._packet_stream = PacketBuffer(self._socket)

        self._sensor_map = []
        self._sample_frequency = float('nan')

        packet = self._packet_stream.next()
        while packet.type == 'EVENT':
            if packet.code == 'VERSION':
                packet = self._packet_stream.next()
                continue
            if packet.code == 'SENSOR_MAP':
                self._sensor_map = packet.message.strip().split(',')
            elif packet.code == 'DATA_RATE':
                self._sample_frequency = int(packet.message.strip().split(',')[1])

            packet = self._packet_stream.next()

        self._channel_map = dict()
        for channel in channel_list:
            index = self._sensor_map.index(channel)
            self._channel_map[channel] = index

        self._data_buffers = dict((channel, []) for channel in channel_list)

        self._process_packet(packet)

    def _process_packet(self, packet):
        if not packet.type == 'EEG_DATA':
            raise ValueError('Wrong packet type')
        for channel, index in self._channel_map.iteritems():
            self._data_buffers[channel].append(packet.data[index])

    def acquire_data(self, count=1):
        while count:
            self._process_packet(self._packet_stream.next())
            count -= 1

    def transform(self, data, sample_size=150):
        transform = fft(data[-int(sample_size):])
        power = abs(transform[1:int(sample_size/2)])**2
        frequencies = [i/(sample_size/2)*(self._sample_frequency/2) for i in range(1, int(sample_size/2))]
        return zip(frequencies, power)

    def channel(self, channel):
        return self._data_buffers[channel]
