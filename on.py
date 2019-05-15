#!/usr/bin/python
#
# Monitor removal of bluetooth reciever
import os
import sys
import subprocess
import time
btconn = False # used to monitor if Bluetooth connection is triggered

def blue_it():
        global btconn
        global connnumloop
        status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
        connnumloop = 0
        while status == 0:
                print("Bluetooth UP")
                print(status)
                status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
                time.sleep(1)
                if status == 0:
                        if connnumloop == 0:
                                btconn = True
                                subprocess.call('sudo cp /boot/config.txt.wifioff.bak /boot/config.txt', shell=True)
								subprocess.call('qdbus --system org.bluez /org/bluez/hci0/dev_A0_10_81_21_68_34/player11 org.bluez.MediaPlayer1.Play', shell=True) # type 'qdbus --system org.bluez' then hit tab to see what '/playerXX' number you have
								print("Sent Play command to phone")
                                print("Wifi disabled for next boot")
                print("BT Device has connected since boot: {}".format(btconn))
                connnumloop += 1
                time.sleep(29)
        else:
                waiting()

def waiting():
        global btconn
        global numloop
        status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
        numloop = 0
        while status == 2:
                print("Bluetooth DOWN")
                print(status)
                if numloop % 2 == 0:
                        print('Attempting to Pair to Phone 1')
                        subprocess.call('sudo /home/pi/scripts/autopair', shell=True)
                else:
                        print('Attempting to Pair to Phone 2')
                        subprocess.call('sudo /home/pi/scripts/autopair2', shell=True)
                time.sleep(1)
                if btconn == False:
                        if numloop == 6:
                                subprocess.call('sudo cp /boot/config.txt.bak /boot/config.txt', shell=True)
                                time.sleep(1)
                                print("Wifi enabled for next boot")
                time.sleep(13)
                status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
                numloop += 1
                print("Loop count: {} | BT Device has connected since boot: {}".format(numloop,btconn))
        else:
                blue_it()

blue_it()
