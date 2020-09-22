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
import threading

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

    @staticmethod
    def ledref(led):
        if led == 1 :
            return SolidSenseLed(SolidSenseLed.lr1,SolidSenseLed.lg1)
        elif led == 2 :
            return SolidSenseLed(SolidSenseLed.lr2,SolidSenseLed.lg2)
        else:
            return None

    def __init__(self,red,green):
        self._r=red
        self._g=green
        self._glevel=0
        self._rlevel=0
        self._timer=None
        self._lock=threading.Lock()

    def green(self,level):
        SolidSenseLed.set(self._g,level)
        self._glevel=level

    def red(self,level):
        SolidSenseLed.set(self._r,level)
        self._rlevel=level

    def green_only(self,level):
        if self._timer != None :
            self._timer.cancel()
            self._timer=None
        self.red(0)
        self.green(level)

    def red_only(self,level):
        if self._timer != None :
            self._timer.cancel()
            self._timer=None
        self.red(level)
        self.green(0)

    def off(self):
        if self._timer != None :
            self._timer.cancel()
            self._timer=None
        SolidSenseLed.set(self._g,0)
        SolidSenseLed.set(self._r,0)
        self._glevel=0
        self._rlevel=0

    def _switch_blink(self):
        if self._cur_i == self._blink_min :
            self._cur_i=self._blink_max
        else:
            self._cur_i=self._blink_min
        SolidSenseLed.set(self._blink_led,self._cur_i)
        self._timer=threading.Timer(self._period,self._switch_blink)
        self._timer.start()

    def _switch_color(self):
        l=self._blink_led
        self._blink_led=self._off_led
        self._off_led=l
        SolidSenseLed.set(self._blink_led,self._blink_max)
        SolidSenseLed.set(self._off_led,0)
        self._timer=threading.Timer(self._period,self._switch_color)
        self._timer.start()



    def blink_red(self,min_i,max_i, period):
        self._blink_min=min_i
        self._blink_max=max_i
        self._period=period
        SolidSenseLed.set(self._g,0)
        SolidSenseLed.set(self._r,min_i)
        self._blink_led=self._r
        self._cur_i=min_i
        self._timer=threading.Timer(self._period,self._switch_blink)
        self._timer.start()

    def blink_green(self,min_i,max_i, period):
        self._blink_min=min_i
        self._blink_max=max_i
        self._period=period
        SolidSenseLed.set(self._r,0)
        SolidSenseLed.set(self._g,min_i)
        self._blink_led=self._g
        self._cur_i=min_i
        self._timer=threading.Timer(self._period,self._switch_blink)
        self._timer.start()

    def blink_red_green(self,period,level):
        self._blink_max=level
        self._period=period
        self._blink_led=self._r
        self._off_led=self._g
        SolidSenseLed.set(self._blink_led,self._blink_max)
        SolidSenseLed.set(self._off_led,0)
        self._timer=threading.Timer(self._period,self._switch_color)
        self._timer.start()


    def stop_blink(self):
        if self._timer != None:
            self._timer.cancel()
            self._timer=None
        SolidSenseLed.set(self._g,self._glevel)
        SolidSenseLed.set(self._r,self._rlevel)






def main():

    SolidSenseLed.led1(SolidSenseLed.GREEN,255)
    SolidSenseLed.led2(SolidSenseLed.RED,255)
    led=SolidSenseLed.ledref(1)
    led.blink_red(0,255,0.5)
    time.sleep(10.)
    led.stop_blink()
    time.sleep(3.)
    led.blink_green(0,255,0.5)
    time.sleep(10.)
    led.stop_blink()
    time.sleep(1.0)
    led.blink_red_green(0.5,255)
    time.sleep(10.)
    led.stop_blink()


if __name__ == '__main__':
    main()
