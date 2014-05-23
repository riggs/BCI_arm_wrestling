
from __future__ import print_function, absolute_import, unicode_literals, division

from .BCI import BCI_Session
from .output import output

from operator import itemgetter

IP_ADDRESS = '10.128.230.239'

OLD_CAP_PORT = 8844
NEW_CAP_PORT = 8888

EXPONENT = 1.2

def running_average():
    sum = 0.0
    count = 0
    value = yield(float('nan'))
    while True:
        sum += value
        count += 1
        value = yield(sum/count)


def main():

    old_cap = BCI_Session(['C3', 'C4'], IP_ADDRESS, OLD_CAP_PORT)
    new_cap = BCI_Session(['F4', 'C3'], IP_ADDRESS, NEW_CAP_PORT)

    old_cap_running_average = running_average()
    new_cap_running_average = running_average()
    next(old_cap_running_average)
    next(new_cap_running_average)

    old_cap_displacement = 0
    new_cap_displacement = 0

    old_cap_velocity = 1
    new_cap_velocity = 1

    total_displacement = 0

    while -45 < total_displacement < 45:

        output(total_displacement)

        old_cap.acquire_data(old_cap._sample_frequency/4)
        new_cap.acquire_data(new_cap._sample_frequency/4)

        # old_cap_transform = old_cap.transform(map(sum, zip(*map(old_cap.channel, ['C3', 'C4']))))
        old_cap_transform = old_cap.transform(old_cap.channel('C3') + old_cap.channel('C4'))
        new_cap_transform = new_cap.transform(new_cap.channel('F4') + new_cap.channel('C3'))

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

        print(old_cap_displacement, new_cap_displacement)

        total_displacement = old_cap_displacement - new_cap_displacement

    print('Winner!')


if __name__ == '__main__':
    import sys

    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)