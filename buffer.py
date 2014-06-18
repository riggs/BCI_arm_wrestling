
from .parser import DSI_streamer_packet

# FIXME: Class is likely obsolete due to update to DSI_streamer_packet.
# TODO: Need to test using the actual DSI-Streamer software to determine what this class needs to do.
class DSI_Packet_Buffer(object):
    """
    An iterator that produces parsed packets from a given socket connected to the DSI-Streamer application.

    Initialize with a socket.socket that is already connected.
    """

    DEFAULT_HEADER = '@ABCD'
    DEFAULT_LENGTH = 1024

    def __init__(self, socket, recv_length=None, header=None, drop_null_packets=True):
        self.socket = socket
        self.length = recv_length if recv_length is not None else self.DEFAULT_LENGTH
        self.header = header if header is not None else self.DEFAULT_HEADER
        self.drop_null = drop_null_packets
        self._stream = ''

    def fill(self):
        """
        Attempt to fill self._stream with data.
        """
        if self.socket:
            try:
                data = self.socket.recv(self.length)
            except:  # Sockets throw generic exceptions with more detail in the error message.
                pass  # Ignore errors since method isn't
            else:
                self._stream += data
        else:
            raise IOError

    def _next_packet(self):
        '''
        Yields next packet from the socket.
        '''
        while self._stream.count(self.header) < 2:
            try:
                self.fill()
            except IOError:
                start = self._stream.find(self.header)
                if start == -1:
                    raise StopIteration
                try:
                    return DSI_streamer_packet.parse(self._stream)
                except ValueError:
                    return

        start = self._stream.find(self.header)
        end = self._stream.find(self.header, start + 1)
        packet = DSI_streamer_packet.parse(self._stream[start:end])
        self._stream = self._stream[end:]
        return packet

    def next(self):
        """
        A wrapper function to ignore NULL packets.

        Implemented as a while loop to avoid potential recursion limits.
        """
        packet = self._next_packet()
        if self.drop_null:
            while packet.type == 'NULL':
                packet = self._next_packet()
        return packet

    def __iter__(self):
        while True:
            yield self.next()
