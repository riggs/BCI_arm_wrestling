
from __future__ import print_function, absolute_import, unicode_literals, division

from .parser import DSI_streamer_packet, packet_versions

from uuid import uuid4
from warnings import warn
from bisect import bisect
import socket
import json

import logging

packet_logger = logging.getLogger("DSI_packets")
packet_logger.setLevel(logging.INFO)
packet_logger.addHandler(logging.NullHandler())
# Module-wide logger
LOG = logging.getLogger(__name__)


class DSI_Streamer_Session(object):

    packet_encoder = json.dumps

    def __init__(self, log_file=None, ip_address='localhost', port=8844, timeout=None, analysis_window=None):

        self._id = uuid4()
        self.sample_frequency = None
        self.mains_frequency = None
        self.timestamps = list()
        self.channel_data = dict()
        self.sensor_map = dict()
        self.analysis_window = analysis_window

        self._logger = packet_logger.getChild(self._id)
        if log_file is not None:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.INFO)
            self._logger.addHandler(fh)

        LOG.info("Connecting to %s:%s", ip_address, port)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(timeout)
        self._socket.connect((ip_address, port))
        self._socket_file = self._socket.makefile()

        self._streaming_start()

    def _streaming_start(self, packet=None):
        if packet is None:
            packet = self._next_packet()

        # First packet sent on connection should be VERSION packet.
        if packet.type is not 'EVENT' or packet.event_code is not 'VERSION':
            LOG.warn("Expected VERSION packet, got: %s", self.packet_encoder(packet))
        else:
            if packet.message.strip() not in packet_versions:
                warn("Unknown program version, verify parsed data", RuntimeWarning)
                LOG.warn("Unknown program version %s", packet.message)
            else:
                LOG.info("Connected to version %s", packet.message)

        # Second packet should be SENSOR_MAP.
        packet = self._next_packet()
        if packet.type is not 'EVENT' or packet.event_code is not 'SENSOR_MAP':
            LOG.warn("Expected SENSOR_MAP packet, got: %s", self.packet_encoder(packet))
            warn("Didn't receive SENSOR_MAP packet, unable to process data")
        else:
            array = packet.message.strip().split(',')
            for index, name in enumerate(array):
                if name is '-':
                    continue
                self.sensor_map[name] = index
            for name in self.sensor_map:
                self.channel_data[name] = list()
            LOG.info('Initialized channel_data')

        # Third packet should be DATA_RATE.
        packet = self._next_packet()
        if packet.type is not 'EVENT' or packet.event_code is not 'DATA_RATE':
            LOG.warn("Expected DATA_RATE packet, got: %s", self.packet_encoder(packet))
        else:
            self.mains_frequency, self.sample_frequency = map(int, packet.message.split(','))
            LOG.info("Sample frequency set to %s", self.sample_frequency)

        # Fourth packet should be DATA_START.
        packet = self._next_packet()
        if packet.type is not 'EVENT' or packet.event_code is not 'DATA_START':
            LOG.warn("Expected DATA_START packet, got: %s", self.packet_encoder(packet))
        else:
            LOG.info("Received DATA_START")

    def _log_packet(self, packet):
        self._logger.info(self.packet_encoder(packet))

    def _next_packet(self):
        packet = DSI_streamer_packet.parse_stream(self._socket_file)
        while packet.type is "NULL":  # Drop NULL packets
            packet = DSI_streamer_packet.parse_stream(self._socket_file)
        self._log_packet(packet)
        return packet

    def _record_data(self, packet):
        if packet.type is not "EEG_DATA":
            raise ValueError("Wrong packet type")

        # Ensure data is time-sorted
        timestamp = packet.timestamp
        if not self.timestamps or timestamp > self.timestamps[-1]:  # Simplest and most likely case
            insert_func = list.append
        else:  # Insert each data value at appropriate index so series remains time-sorted
            index = bisect(self.timestamps, timestamp)
            insert_func = lambda list_, value: list_.insert(index, value)

        insert_func(self.timestamps, timestamp)

        for channel_name, index in self.sensor_map.items():
            insert_func(self.channel_data[channel_name], packet.data[index])

    def acquire_data(self, duration=0.2):
        """
        Acquire data for a duration of time.

        :param duration: Length of time to acquire data, in seconds
        :type duration: int or float
        :return:
        """
        if self.sample_frequency is None:
            LOG.warn("sample_frequency not set, assuming 300")
            packet_count = int(300 * duration)
        else:
            packet_count = int(self.sample_frequency * duration)

        while packet_count > 0:
            packet = self._next_packet()
            if packet.type is 'EVENT':
                if packet.event_code is 'DATA_STOP':
                    return
                else:
                    self._streaming_start(packet)
                    packet = self._next_packet()
            self._record_data(packet)
            packet_count -= 1

        if self.analysis_window is not None:
            max_count = self.analysis_window * (self.sample_frequency or 900)
            LOG.info("Trimming data to %s points", max_count)
            for name, data in self.channel_data.items():
                self.channel_data[name] = data[max_count:]
