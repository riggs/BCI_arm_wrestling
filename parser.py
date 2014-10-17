
from __future__ import print_function, absolute_import, division

import json
from construct import Container

from .api import DSI_Streamer_Session


class DSI_Streamer_Replay(DSI_Streamer_Session):

    def __init__(self, replay_file, data_age=None):

        self.replay_file = replay_file

        self.sample_frequency = None
        self.mains_frequency = None
        self.timestamps = list()
        self.sensor_data = dict()
        self.sensor_map = dict()
        self.data_age = data_age

        self._streaming_start()

    def _next_packet(self):
        return Container(**json.loads(self.replay_file.readline()))

    @staticmethod
    def packet_encoder(packet):
        return repr(packet)
