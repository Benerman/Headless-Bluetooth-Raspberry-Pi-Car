#!/usr/bin/python
#
# Monitor removal of bluetooth reciever
import os, sys, subprocess, time, re, json
btconn = False # used to monitor if Bluetooth connection is triggered
ACTIVE_MAC_ADDRESS = None

def read_file(path=None):
        with open(path) as f:
                contents = f.read()
        return contents

def get_connected_mac_address():
        command = subprocess.check_output('''bluetoothctl paired-devices | cut -f2 -d' '| while read -r uuid; do     info=`bluetoothctl info $uuid`;     if echo "$info" | grep -q "Connected: yes"; then        echo "$info" | grep "Device";     fi; done''', shell=True
                                          ).decode().strip()
        return command.split(' ')[1]

def get_connected_device_name():
        command = subprocess.check_output('''bluetoothctl paired-devices | cut -f2 -d' '| while read -r uuid; do     info=`bluetoothctl info $uuid`;     if echo "$info" | grep -q "Connected: yes"; then        echo "$info" | grep "Name";     fi; done''', shell=True
                                          ).decode().strip()
        return ' '.join(command.split(' ')[1:])

def compile_fresh_connection():
        name = get_connected_device_name()
        mac = get_connected_mac_address()
        return {"name":name, "mac_addr": mac, "connection_count": 1}

def blue_it():
        global btconn
        global connnumloop
        global ACTIVE_MAC_ADDRESS
        status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
        connnumloop = 0
        while status == 0:
                print("Bluetooth UP")
                status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
                time.sleep(1)
                if connnumloop == 0:
                        btconn = True
                        # subprocess.call('sudo cp /boot/config.txt.wifioff.bak /boot/config.txt', shell=True)
                        # print('Wifi Off next boot')
                        ACTIVE_MAC_ADDRESS = get_connected_mac_address()
                        clean_mac_addr = ACTIVE_MAC_ADDRESS.replace(':', '_')
                        subprocess.call('qdbus --system org.bluez /org/bluez/hci0/dev_{}/player0 org.bluez.MediaPlayer1.Play'.format(clean_mac_addr), shell=True)
                        print("Sent Play command to phone")
                print("BT Device has connected since boot: {}".format(btconn))
                connnumloop += 1
                time.sleep(14)
        else:
                waiting()

def waiting():
        global btconn
        global numloop
        global ACTIVE_MAC_ADDRESS
        # check if event0(Bluetooth connection is established)
        status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
        numloop = 0
        while status == 2:
                print("Bluetooth DOWN")
                print(status)
                with open('previous_connections.json') as fp:
                        conns = json.load(fp)
                previous_connections = conns['previous_addresses'].items()
                for i,conn in previous_connections:
                        print('Attempting to Pair to {}'.format(conn['name']))
                        subprocess.call('sudo ~/scripts/autopair {}'.format(conn['mac_addr']), shell=True)
                        time.sleep(10)
                        # Need to check if the pairing was successful 
                        status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
                # if btconn == False:
                #         if numloop == 6:
                #                 subprocess.call('sudo cp /boot/config.txt.bak /boot/config.txt', shell=True)
                #                 time.sleep(1)
                #                 print("Wifi enabled for next boot")
                time.sleep(14)
                status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
                numloop += 1
                print("Loop count: {} | BT Device has connected since boot: {}".format(numloop,btconn))
        else:
                ACTIVE_MAC_ADDRESS = get_connected_mac_address()
                if ACTIVE_MAC_ADDRESS in [x['mac_addr'] for x in conns['previous_addresses'].values()]:
                        conns['previous_addresses'][i]['connection_count'] += 1
                else:        
                        fresh_conn = compile_fresh_connection()
                        total_prev_conns = len(conns['previous_addresses']) + 1
                        conns["previous_addresses"][str(total_prev_conns)] = fresh_conn
                with open("previous_connections.json", 'w') as fp:
                        json.dump(conns, fp)
                blue_it()

blue_it()