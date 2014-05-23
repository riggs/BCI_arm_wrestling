
from .parser import DSI_streamer_packet

class PacketBuffer(object):

    HEADER = '@ABCD'
    LENGTH = 1024

    def __init__(self, socket):
        self.socket = socket
        self._stream = ''

    def fill(self):
        if self.socket:
            try:
                self._stream += self.socket.recv(self.LENGTH)
            except:
                pass
        else:
            raise IOError

    def next(self):
        '''
        Yields next packet from the socket.
        '''
        while self._stream.count(self.HEADER) < 2:
            try:
                self.fill()
            except IOError:
                start = self._stream.find(self.HEADER)
                if start == -1:
                    raise StopIteration
                try:
                    return DSI_streamer_packet.parse(self._stream)
                except ValueError:
                    return

        start = self._stream.find(self.HEADER)
        end = self._stream.find(self.HEADER, start + 1)
        packet = DSI_streamer_packet.parse(self._stream[start:end])
        self._stream = self._stream[end:]
        if packet.type != 'NULL':
            return packet
        else:
            return self.next()

    def __iter__(self):
        while True:
            yield self.next()
