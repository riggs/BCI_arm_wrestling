
from __future__ import print_function, absolute_import, unicode_literals, division
from data import DSI_streamer_packet


def main():
    import argparse, socket
    parser = argparse.ArgumentParser(description='Analyze data from DSI-Streamer and emit controls for robotic arms.')
    parser.add_argument('--ip-address', default='localhost')
    parser.add_argument('--port', default=8844, type=int)

    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(args.ip_address, args.port)
    file_ = sock.makefile()

    try:
        while True:
            print(DSI_streamer_packet.parse_stream(file_))
    finally:
        sock.close()

if __name__ == '__main__':
    import sys

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)