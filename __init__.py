
from __future__ import print_function, absolute_import, division

from .api import DSI_Streamer_Session, LOG
from .analysis import running_average_coro, fft_power
#from .output import output, display
from .output import output

from operator import itemgetter
from random import choice
#from time import sleep


IP_ADDRESS = '10.1.10.25'  # IP of host running DSI-Streamer, 'localhost' if on the same machine
PORT = 8844  # Port as specified in DSI-Streamer. Multiple ports allow multi-cap analysis

EXPONENT = 1


def main(data_file=None, debug=False):

    print("\n     {0}\n".format(choice(("Right", "Left"))))

    if debug:  # Log to stdout
        import logging, sys
        LOG.setLevel(logging.DEBUG)
        stdout = logging.StreamHandler(sys.stdout)
        stdout.setLevel(logging.DEBUG)
        LOG.addHandler(stdout)

    # Connect to DSI-Streamer
    cap = DSI_Streamer_Session(log_file=data_file, ip_address=IP_ADDRESS, port=PORT, data_age=0.5)

    P4_running_average = running_average_coro()
    next(P4_running_average)  # Required boilerplate, returns NaN
    C4_running_average = running_average_coro()
    next(C4_running_average)  # Required boilerplate, returns NaN

    P4_displacement = 0
    C4_displacement = 0

    P4_velocity = 1
    C4_velocity = 1

    total_displacement = 0

    cap.acquire_data(0.5)  # Make sure there's enough data for first analysis

    while True:

        #output(total_displacement)
        print(total_displacement)

        cap.acquire_data()

        # Because of 'data_age=0.5', only last 1/2 second of signal is analyzed
        Fz_power = fft_power(cap.sensor_data['Fz'], sample_frequency=cap.sample_frequency)
        C4_power = fft_power(cap.sensor_data['C3'], sample_frequency=cap.sample_frequency)

        # Get the max signal between 10 & 14 Hz
        Fz_signal = max(filter(lambda x: 11 < x[0] < 13, Fz_power), key=itemgetter(1))[1]
        C4_signal = max(filter(lambda x: 11 < x[0] < 13, C4_power), key=itemgetter(1))[1]

        """
        total_displacement = Fz_signal - C4_signal
        """

        P4_average = P4_running_average.send(Fz_signal)
        C4_average = C4_running_average.send(C4_signal)

        if Fz_signal >= P4_average:
            P4_displacement += P4_velocity
            P4_velocity *= EXPONENT

        if C4_signal >= C4_average:
            C4_displacement += C4_velocity
            C4_velocity *= EXPONENT

        total_displacement = P4_displacement - C4_displacement

    output(total_displacement)
    print('Winner!')
    #sleep(1)
    # display(total_displacement)
    #output(0)


if __name__ == '__main__':
    import sys

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
