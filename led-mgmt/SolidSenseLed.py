#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Laurent Carré
#
# Created:     31/12/2019
# Copyright:   (c) Laurent Carré Sterwen Technologies 2019
# Licence:     <your licence>
#-------------------------------------------------------------------------------


import sys
import struct
import time

class SolidSenseLed:

    led_path="/sys/class/leds/"
    lr1=led_path+'red1/brightness'
    lr2=led_path+'red2/brightness'
    lg1=led_path+'green1/brightness'
    lg2=led_path+'green2/brightness'
    OFF=0
    RED=1
    GREEN=2


    @staticmethod
    def set(led,level) :
        if level < 0 or level > 255 :
            print("Invalid light level for LED")
            return
        l=("%d"%level).encode()
        fd=open(led,'bw')
        fd.write(l)
        fd.close()


    @staticmethod
    def led1(color,level=0):
        if color==SolidSenseLed.RED :
            led=SolidSenseLed.lr1
        elif color == SolidSenseLed.GREEN :
            led=SolidSenseLed.lg1
        else:
            SolidSenseLed.set(SolidSenseLed.lg1,0)
            SolidSenseLed.set(SolidSenseLed.lr1,0)
            return
        SolidSenseLed.set(led,level)

    @staticmethod
    def led2(color,level=0):
        if color==SolidSenseLed.RED :
            led=SolidSenseLed.lr2
        elif color == SolidSenseLed.GREEN :
            led=SolidSenseLed.lg2
        else:
            SolidSenseLed.set(SolidSenseLed.lg2,0)
            SolidSenseLed.set(SolidSenseLed.lr2,0)
            return
        SolidSenseLed.set(led,level)




def main():

    SolidSenseLed.led1(SolidSenseLed.GREEN,255)
    SolidSenseLed.led2(SolidSenseLed.RED,255)

if __name__ == '__main__':
    main()
