
from time import sleep

try:
    import serial
except ImportError:
    class Fake_Serial(object):
        def write(self, *args): pass
        def flush(self): pass
        def readline(self): pass
    arms = Fake_Serial()
    balloon = Fake_Serial()

    def output(value):
        print('{0:>23}|{1:<23}'.format('<' * int(value/2), '>' * -int(value/2)))

else:
    arms = serial.Serial(13)
    balloon = serial.Serial(12)

    def output(value):
        value = str(90 + int(value))
        print(value)
        arms.write(value)
        arms.flush()
        print(arms.readline())


    def display(value):
        color_code = 'g' if value > 0 else 'o'
        balloon.write(color_code)
        balloon.flush()
        sleep(3)
        balloon.write('r')
        balloon.flush()
