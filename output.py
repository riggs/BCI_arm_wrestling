
import serial

from time import sleep

arms = serial.Serial(13)

#balloon = serial.Serial(12)


def output(value):
    
    #print('{0:>23}|{1:<23}'.format('*' * int(value/2), '*' * -int(value/2)))
    #print(str(90+int(value)))
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
