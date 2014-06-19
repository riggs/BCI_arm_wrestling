from __future__ import print_function, absolute_import, unicode_literals, division

from .BCI import BCI_Session, transform
from .output import output, display

from operator import itemgetter
from time import sleep


IP_ADDRESS = 'localhost'

OLD_CAP_PORT = 8844
NEW_CAP_PORT = 8888

EXPONENT = 1.2


def running_average_coro():
    """
    A coroutine to compute a running average.

    Because of the peculiarities of python generator functions, this function acts more like a class. Call it to
    instantiate a new coroutine and initialize the coroutine using 'next'. Once it's operational, sending it a value
    (via it's .send method) will return the running average of everything it's been sent.
    """
    sum = 0.0
    count = 0
    value = yield (float('nan'))
    while True:
        sum += value
        count += 1
        value = yield (sum / count)


def main(data_file=None):
    old_cap = BCI_Session(['C3', 'C4'], IP_ADDRESS, OLD_CAP_PORT, data_file)
    new_cap = BCI_Session(['F4', 'C3'], IP_ADDRESS, NEW_CAP_PORT, data_file)

    old_cap_running_average = running_average_coro()
    new_cap_running_average = running_average_coro()
    next(old_cap_running_average)  # Returns float('nan')
    next(new_cap_running_average)  # Returns float('nan')

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
        old_cap_transform = transform(old_cap.channel('C3')[-150:] + old_cap.channel('C4')[-150:],
                                      sample_frequency=old_cap.sample_frequency)
        new_cap_transform = transform(new_cap.channel('F4')[-150:] + new_cap.channel('C3')[-150:],
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
