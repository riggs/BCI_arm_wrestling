
from __future__ import print_function, absolute_import, division

from .protocol import DSI_streamer_packet, packet_versions

from uuid import uuid4
from warnings import warn
from bisect import bisect
import socket
import json

import logging

# Module-wide logger
LOG = logging.getLogger(__name__)

packet_logger = logging.getLogger("DSI_packets")
packet_logger.setLevel(logging.INFO)
packet_logger.addHandler(logging.NullHandler())


class DSI_Streamer_Session(object):
    """
    This class connects to DSI-Streamer software and collects data from it for convenient use.

    :param log_file: A file name to log all packets received from DSI-Streamer. By default, packets are JSON-encoded
     (see `packet_encoder` attribute).
    :type log_file: str
    :param ip_address: The IP address of the machine running DSI-Streamer.
    :type ip_address: str
    :param port: The 'Client Port' as specified in DSI-Streamer.
    :type port: int
    :param timeout: The value passed to the :meth:`~socket.socket.settimeout` method of the :class:socket.socket
     connection to DSI-Streamer.
    :type timeout: int or float
    :param data_age: The time, in seconds, of the oldest data to keep in memory. Data older than this value is purged
     after every data-acquisition cycle. This is probably only relevant if you plan to run a single session for
     extended periods. By default, all data is saved for the life of the instance.
    :type data_age: int or float

    Upon initialization, this class connects to the given IP & port combination. It then expects to receive packets as
    dictated by the TCP/IP Socket protocol documentation `available here
    <http://wearablesensing.com/support_downloads.php>`.


    """

    @staticmethod
    def packet_encoder(packet):
        return json.dumps(dict(packet))

    def __init__(self, log_file=None, ip_address='localhost', port=8844, timeout=None, data_age=None):

        self._id = uuid4().hex
        self.sample_frequency = None
        self.mains_frequency = None
        self.timestamps = list()
        self.sensor_data = dict()
        self.sensor_map = dict()
        self.data_age = data_age

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
        if packet.type != 'EVENT' or packet.event_code != 'VERSION':
            LOG.warn("Expected VERSION packet, got: %s", self.packet_encoder(packet))
        else:
            if packet.message.strip() not in packet_versions:
                warn("Unknown program version, verify parsed data", RuntimeWarning)
                LOG.warn("Unknown program version %s", packet.message)
            else:
                LOG.info("Connected to version %s", packet.message)

        # Second packet should be SENSOR_MAP.
        packet = self._next_packet()
        if packet.type != 'EVENT' or packet.event_code != 'SENSOR_MAP':
            LOG.warn("Expected SENSOR_MAP packet, got: %s", self.packet_encoder(packet))
            warn("Didn't receive SENSOR_MAP packet, unable to process data")
        else:
            array = packet.message.strip().split(',')
            for index, name in enumerate(array):
                if name == '-':
                    continue
                self.sensor_map[name] = index
            for name in self.sensor_map:
                self.sensor_data[name] = list()
            LOG.info('Initialized sensor_data')

        # Third packet should be DATA_RATE.
        packet = self._next_packet()
        if packet.type != 'EVENT' or packet.event_code != 'DATA_RATE':
            LOG.warn("Expected DATA_RATE packet, got: %s", self.packet_encoder(packet))
        else:
            self.mains_frequency, self.sample_frequency = map(int, packet.message.split(','))
            LOG.info("Sample frequency set to %s", self.sample_frequency)

        # Fourth packet should be DATA_START.
        packet = self._next_packet()
        if packet.type != 'EVENT' or packet.event_code != 'DATA_START':
            LOG.warn("Expected DATA_START packet, got: %s", self.packet_encoder(packet))
        else:
            LOG.info("Received DATA_START")

    def _log_packet(self, packet):
        self._logger.info(self.packet_encoder(packet))

    def _next_packet(self):
        packet = DSI_streamer_packet.parse_stream(self._socket_file)
        while packet.type == "NULL":  # Drop NULL packets
            packet = DSI_streamer_packet.parse_stream(self._socket_file)
        self._log_packet(packet)
        return packet

    def _record_data(self, packet):
        if packet.type != "EEG_DATA":
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
            insert_func(self.sensor_data[channel_name], packet.sensor_data[index])

    def _trim_data(self):
        if self.data_age is None:
            return
        max_count = int(self.data_age * (self.sample_frequency or 900))  # Assume worst case if missing value
        LOG.info("Trimming data to %s points", max_count)
        for name, data in self.sensor_data.items():
            self.sensor_data[name] = data[-max_count:]
        self.timestamps = self.timestamps[-max_count:]

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
            if packet.type == 'EVENT':
                if packet.event_code == 'DATA_STOP':
                    return
                else:
                    self._streaming_start(packet)
                    packet = self._next_packet()
            self._record_data(packet)
            packet_count -= 1

        if self.data_age is not None:
            self._trim_data()

