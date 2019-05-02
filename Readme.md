Gathered sources creating a RPi headless bluetooth receiver that auto connects at boot to my specific phone's MAC address

Thanks to
https://gist.github.com/mill1000
and
https://www.raspberrypi.org/forums/memberlist.php?mode=viewprofile&u=125239&sid=49e51edea1437fb918eb8ca317700ca8

Sources: 
https://gist.github.com/mill1000/74c7473ee3b4a5b13f6325e9994ff84c
https://www.raspberrypi.org/forums/viewtopic.php?t=170353
https://www.max2play.com/en/forums/topic/pi3-bluetooth-auto-reconnect-option-script/ - reconnect?
https://retropie.org.uk/forum/topic/1754/help-with-script-to-maintain-bluetooth-connection/10 - Reconnect?

https://raspberrypi.stackexchange.com/questions/53408/automatically-connect-trusted-bluetooth-speaker - Script to place your known BT devices to auto connect. Maybe add two+ mac addresses and then create logic to try for duration, then next...


## About
This gist will show how to setup Raspbian Stretch as a headless Bluetooth A2DP audio sink. This will allow your phone, laptop or other Bluetooth device to play audio wirelessly through a Rasperry Pi.

## Motivation
A quick search will turn up a plethora of tutorials on setting up A2DP on the Raspberry Pi. However, I felt this gist was necessary because this solution is:
* Automatic & Headless - Once setup, the system is entirely automatic. No user iteration is required to pair, connect or start playback. Therefore the Raspberry Pi can be run headless. 
* Simple - This solution has few dependencies, readily available packages and minimal configuration.
* Up to date - As of December 2017. Written for Raspbian Stretch & Bluez 5.43

## Prerequisites
* Raspbian Stretch - I used the Lite version as this is a headless setup. See the [official guide](https://www.raspberrypi.org/learning/software-guide/quickstart/) if you need help.
* [Bluez-alsa](https://github.com/Arkq/bluez-alsa) - Available in the Raspbian package repo. This software allows us to stream A2DP audio over Bluetooth without PulseAudio.
* Raspberry Pi with Bluetooth - The Raspberry Pi 3 has integrated Bluetooth, however there is a [known bug](https://github.com/raspberrypi/linux/issues/1402) when the WiFi is used simultaneously. Cheap USB Bluetooth dongles work equally well.

## Disabling Integrated Bluetooth
If you are using a separate USB Bluetooth dongle, disable the integrated Bluetooth to prevent conflicts.

To disable the integrated Bluetooth add the following
```
# Disable onboard Bluetooth
dtoverlay=pi3-disable-bt
``` 
to `/boot/config.txt` and execute the following command
```
sudo systemctl disable hciuart.service
```

## Initial Setup
First make sure the system is up to date using the following commands.
```
sudo apt-get update
sudo apt-get upgrade
```
Then reboot the Pi to ensure the latest kernel is loaded.

Now install the required packages.
```
sudo apt-get install bluealsa python-dbus
```

## Make Bluetooth Discoverable
Normally a Bluetooth device is only discoverable for a limited amount of time. Since this is a headless setup we want the device to always be discoverable.

1. Set the DiscoverableTimeout in `/etc/bluetooth/main.conf` to 0
```
# How long to stay in discoverable mode before going back to non-discoverable
# The value is in seconds. Default is 180, i.e. 3 minutes.
# 0 = disable timer, i.e. stay discoverable forever
DiscoverableTimeout = 0
```

2. Enable discovery on the Bluetooth controller
```
sudo bluetoothctl
power on
discoverable on
exit
```

## Install The A2DP Bluetooth Agent
A Bluetooth agent is a piece of software that handles pairing and authorization of Bluetooth devices. The following agent allows the Raspberry Pi to automatically pair and accept A2DP connections from Bluetooth devices.
All other Bluetooth services are rejected.

Copy the included file **a2dp-agent** to `/usr/local/bin` and make the file executable with
```
sudo chmod +x /usr/local/bin/a2dp-agent
```

### Testing The Agent
Before continuing, verify that the agent is functional. The Raspberry Pi should be discoverable, pairable and recognized as an audio device.

Note: At this point the device will not output any audio. This step is only to verify the Bluetooth is discoverable and bindable.
1. Manually run the agent by executing
```
sudo /usr/local/bin/a2dp-agent
```
2. Attempt to pair and connect with the Raspberry Pi using your phone or computer.
3. The agent should output the accepted and rejected Bluetooth UUIDs
```
A2DP Agent Registered
AuthorizeService (/org/bluez/hci0/dev_94_01_C2_47_01_AA, 0000111E-0000-1000-8000-00805F9B34FB)
Rejecting non-A2DP Service
AuthorizeService (/org/bluez/hci0/dev_94_01_C2_47_01_AA, 0000110d-0000-1000-8000-00805f9b34fb)
Authorized A2DP Service
AuthorizeService (/org/bluez/hci0/dev_94_01_C2_47_01_AA, 0000111E-0000-1000-8000-00805F9B34FB)
Rejecting non-A2DP Service
```

If the Raspberry Pi is not recognized as a audio device, ensure that the bluealsa package was installed as part of the [Initial Setup](#initial-setup)

## Install The A2DP Bluetooth Agent As A Service
To make the A2DP Bluetooth Agent run on boot copy the included file **bt-agent-a2dp.service** to `/etc/systemd/system`.
Now run the following command to enable the A2DP Agent service
```
sudo systemctl enable bt-agent-a2dp.service
```

Bluetooth devices should now be able to discover, pair and connect to the Raspberry Pi without any user intervention.

## Testing Audio Playback
Now that Bluetooth devices can pair and connect with the Raspberry Pi we can test the audio playback.

The tool `bluealsa-aplay` is used to forward audio from the Bluetooth device to the ALSA output device (sound card).

Execute the following command to accept A2DP audio from any connected Bluetooth device.
```
bluealsa-aplay -vv 00:00:00:00:00:00
```

Play a song on the Bluetooth device and the Raspberry Pi should output audio on either the headphone jack or the HDMI port. See [this guide](https://www.raspberrypi.org/documentation/configuration/audio-config.md) for configuring the audio output device of the Raspberry Pi.

### Install The Audio Playback As A Service
To make the audio playback run on boot copy the included file **a2dp-playback.service** to `/etc/systemd/system`.
Now run the following command to enable A2DP Playback service
```
sudo systemctl enable a2dp-playback.service
```

Reboot and enjoy!

## Low Volume Output
If you are experiencing low volume output, run `alsamixer` and increase the volume of the Pi's soundcard.

## Now to get your main device to automatically reconnect to your Headless Bluetooth Receiver
OK! We need to enter over into the Python world. Jason Woodruff(https://raspberrypi.stackexchange.com/users/48183/jason-woodruff) wrote a Python program that will watch for the bluetooth device. In short, it will activate the connection between RPi and your bluetooth speaker, once your bluetooth speaker is turned on. And vice versa. Let's create a directory called python in your home directory To do that, type this:

mkdir -p ~/python
Now let's create the python program file. To do that, type this:

nano ~/python/on.py
Inside that file, we need to copy and paste the following:

#!/usr/bin/python
#
# Monitor removal of bluetooth reciever
import os
import sys
import subprocess
import time

def blue_it():
    status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
    while status == 0:
        print("Bluetooth UP")
        print(status)
        time.sleep(15)
        status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
    else:
        waiting()

def waiting():
    subprocess.call('killall -9 pulseaudio', shell=True)
    time.sleep(3)
    subprocess.call('pulseaudio --start', shell=True)
    time.sleep(2)
    status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)  
    while status == 2:
        print("Bluetooth DOWN")
        print(status)
        subprocess.call('~/scripts/autopair', shell=True)
        time.sleep(15)
        status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
    else:
        blue_it() 

blue_it()
Now press CTRL + x and then press Enter to save the Python program file. Now we need to make this file executable. To do that, type this:

chmod +x ~/python/on.py


go to:
nano ~/.bashrc

and place the code:
wait
~/python/on.py


Using the on.py file I modified it to my use case

#!/usr/bin/python
#
# Monitor removal of bluetooth reciever
import os
import sys
import subprocess
import time
btconn = False

def blue_it():
	global btconn 
	status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
	connnumloop = 0
	while status == 0:
		print("Bluetooth UP")
		print(status)
		time.sleep(29)
		status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
		time.sleep(1)
		if status == 0:
			btconn = True
			subprocess.call('sudo /home/pi/scripts/DisableWifiOnBoot', shell=True)
			print("Wifi disabled for next boot")
		print("BT Device has connected since boot: {}".format(btconn))
		connnumloop += 1
	else:
		waiting()

def waiting():
	global btconn 
	status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)  
	numloop = 0
	while status == 2:
		print("Bluetooth DOWN")
		print(status)
		subprocess.call('sudo /home/pi/scripts/autopair', shell=True)
		time.sleep(1)
		if btconn == False:
			if numloop == 2:
				subprocess.call('sudo /home/pi/scripts/EnableWifiOnBoot', shell=True)
				time.sleep(1)
				print("Wifi enabled for next boot")
		time.sleep(13)
		status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
		numloop += 1
		print("Loop count: {}  |  BT Device has connected since boot: {}".format(numloop,btconn))
	else:
		blue_it() 

blue_it()

Disable the onboard wlan0
#!/bin/bash

# DisableWifiOnBoot Script
# Run on BT Device Connect
# Check if line written
grep -q "dtoverlay=pi3-disable-wifi" /boot/config.txt
	if [[ $(echo $?) == 1 ]];
	then
		echo "Line not in /boot/config.txt"
		# Write Line
		echo "dtoverlay=pi3-disable-wifi" | sudo tee -a /boot/config.txt
		echo "Writing line to disable WIFI on boot"
	else
		echo "Line exists already, WIFI will be disabled on boot"
	fi
echo "Done"



Enable onboard wlan0
#!/bin/bash

# EnableWifiOnBoot Script
# Clear out line disabling WIFI on boot
# Check if line written
grep -q "dtoverlay=pi3-disable-wifi" /boot/config.txt
	if [[ $(echo $?) == 0 ]];
	then
		echo "Line is within /boot/config.txt"
		# Write Line
		sudo sed -e s/dtoverlay=pi3-disable-wifi//g -i /boot/config.txt
	fi
echo "Done"
