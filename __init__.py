from __future__ import print_function, absolute_import, unicode_literals, division

from .BCI import DSI_Streamer_Session
from .analysis import transform, running_average_coro
from .output import output, display

from operator import itemgetter
from time import sleep


IP_ADDRESS = 'localhost'

OLD_CAP_PORT = 8844
NEW_CAP_PORT = 8888

EXPONENT = 1.2


def main(data_file=None):
    old_cap = DSI_Streamer_Session(log_file=data_file, ip_address=IP_ADDRESS, port=OLD_CAP_PORT)
    new_cap = DSI_Streamer_Session(log_file=data_file, ip_address=IP_ADDRESS, port=NEW_CAP_PORT)

    old_cap_running_average = running_average_coro()
    new_cap_running_average = running_average_coro()
    next(old_cap_running_average)  # Returns NaN
    next(new_cap_running_average)  # Returns NaN

    old_cap_displacement = 0
    new_cap_displacement = 0

    old_cap_velocity = 5
    new_cap_velocity = 5

    total_displacement = 0

    while -45 < total_displacement < 45:

        output(total_displacement)

        old_cap.acquire_data(old_cap.sample_frequency)
        new_cap.acquire_data(new_cap.sample_frequency)

        # old_cap_transform = old_cap.transform(map(sum, zip(*map(old_cap.channel, ['C3', 'C4']))))
        old_cap_transform = transform(old_cap.channel_data['C3'][-150:] + old_cap.channel_data['C4'][-150:],
                                      sample_frequency=old_cap.sample_frequency)
        new_cap_transform = transform(new_cap.channel_data['F4'][-150:] + new_cap.channel_data['C3'][-150:],
                                      sample_frequency=new_cap.sample_frequency)

        # Get the max signal between 10 & 14 Hz
        old_cap_signal = max(filter(lambda x: 10 < x[0] < 14, old_cap_transform), key=itemgetter(1))[1]
        new_cap_signal = max(filter(lambda x: 10 < x[0] < 14, new_cap_transform), key=itemgetter(1))[1]

        old_cap_average = old_cap_running_average.send(old_cap_signal)
        new_cap_average = new_cap_running_average.send(new_cap_signal)

        if old_cap_signal >= old_cap_average:
            old_cap_displacement += old_cap_velocity
            old_cap_velocity *= EXPONENT

        if new_cap_signal >= new_cap_average:
            new_cap_displacement += new_cap_velocity
            new_cap_velocity *= EXPONENT

        # print(old_cap_average, new_cap_average)
        # print(old_cap_displacement, old_cap_velocity, new_cap_displacement, new_cap_velocity)

        total_displacement = old_cap_displacement - new_cap_displacement

    print('Winner!')
    output(total_displacement)
    sleep(1)
    # display(total_displacement)
    output(0)


if __name__ == '__main__':
    import sys

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
