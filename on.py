#!/usr/bin/python
#
# Monitor removal of bluetooth reciever
import os, sys, subprocess, time, re, json

BASE_DIR = os.path.dirname(__file__)
PREV_CONN_PATH = os.path.join(BASE_DIR, "previous_connections.json")
CONFIG_PATH = os.path.join(BASE_DIR, "web_config.json")

# cooldown after a real disconnect before attempting reconnects (seconds)
COOLDOWN_SECONDS = int(os.getenv("BT_DISCONNECT_DELAY", "120"))
LAST_DISCONNECT = None

# Ensure previous_connections.json exists with a valid default structure
if not os.path.exists(PREV_CONN_PATH):
    with open(PREV_CONN_PATH, "w") as fp:
        json.dump({"previous_addresses": {}}, fp)

btconn = False # used to monitor if Bluetooth connection is triggered
ACTIVE_MAC_ADDRESS = None

def read_file(path=None):
        with open(path) as f:
                contents = f.read()
        return contents

def connect_to_bt_device(addr, loop_num):
        # Use subprocess.run to capture stdout/stderr and avoid raising CalledProcessError
        if not addr:
            return "no-address"
        try:
                # if we've looped a lot, remove and try fresh
                if loop_num > 20:
                        subprocess.run(f'bluetoothctl remove {addr}', shell=True, capture_output=True, text=True)
                # try trusting device first (helps some phones)
                subprocess.run(f'bluetoothctl trust {addr}', shell=True, capture_output=True, text=True)
                p = subprocess.run(f'bluetoothctl connect {addr}', shell=True, capture_output=True, text=True, timeout=20)
                out = (p.stdout or "").strip()
                err = (p.stderr or "").strip()
                if p.returncode == 0:
                        return out or "connected"
                else:
                        # return concise failure message (avoid raising)
                        if err:
                                return f"failed({p.returncode}): {err}"
                        if out:
                                return f"failed({p.returncode}): {out}"
                        return f"failed({p.returncode})"
        except subprocess.TimeoutExpired:
                return "timeout"
        except Exception as e:
                return f"exception: {e}"

def get_connected_mac_address():
    try:
        command = subprocess.check_output('''bluetoothctl paired-devices | cut -f2 -d' '| while read -r uuid; do     info=`bluetoothctl info $uuid`;     if echo "$info" | grep -q "Connected: yes"; then        echo "$info" | grep "Device";     fi; done''', shell=True
                                          ).decode().strip()
        if not command:
            return None
        parts = command.split()
        return parts[1] if len(parts) > 1 else None
    except Exception:
        return None

def get_connected_device_name():
    try:
        command = subprocess.check_output('''bluetoothctl paired-devices | cut -f2 -d' '| while read -r uuid; do     info=`bluetoothctl info $uuid`;     if echo "$info" | grep -q "Connected: yes"; then        echo "$info" | grep "Name";     fi; done''', shell=True
                                          ).decode().strip()
        if not command:
            return None
        parts = command.split()
        return ' '.join(parts[1:]) if len(parts) > 1 else None
    except Exception:
        return None

def compile_fresh_connection():
        name = get_connected_device_name()
        mac = get_connected_mac_address()
        return {"name":name, "mac_addr": mac, "connection_count": 1}

def blue_it():
        global btconn
        global connnumloop
        global ACTIVE_MAC_ADDRESS
        global LAST_DISCONNECT
        status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
        connnumloop = 0
        had_connected = False
        while status == 0:
                print("Bluetooth UP")
                status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
                time.sleep(1)
                if connnumloop == 0:
                        btconn = True
                        had_connected = True
                        ACTIVE_MAC_ADDRESS = get_connected_mac_address()
                        # only autoplay if enabled in web_config.json
                        try:
                            autoplay = False
                            if os.path.exists(CONFIG_PATH):
                                with open(CONFIG_PATH) as cf:
                                    cfg = json.load(cf)
                                    autoplay = cfg.get("autoplay", False)
                        except Exception:
                            autoplay = False
                        if autoplay and ACTIVE_MAC_ADDRESS:
                            clean_mac_addr = ACTIVE_MAC_ADDRESS.replace(':', '_')
                            subprocess.call('qdbus --system org.bluez /org/bluez/hci0/dev_{}/player0 org.bluez.MediaPlayer1.Play'.format(clean_mac_addr), shell=True)
                            print("Sent Play command to phone")
                print("BT Device has connected since boot: {}".format(btconn))
                connnumloop += 1
                time.sleep(14)
        else:
                # if we were connected and now left the connected loop, record disconnect time
                if had_connected:
                    try:
                        LAST_DISCONNECT = time.time()
                        btconn = False
                        print(f"Device disconnected; deferring reconnect attempts for {COOLDOWN_SECONDS}s")
                    except Exception:
                        LAST_DISCONNECT = None
                waiting()

def waiting():
        global btconn
        global numloop
        global ACTIVE_MAC_ADDRESS
        global LAST_DISCONNECT
        # check if event0(Bluetooth connection is established)
        status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
        numloop = 0
        # load previous connections once (safe)
        try:
                with open(PREV_CONN_PATH) as fp:
                        conns = json.load(fp)
        except Exception:
                conns = {"previous_addresses": {}}
        # if we recently disconnected, delay reconnect attempts (only once)
        if LAST_DISCONNECT:
                elapsed = time.time() - LAST_DISCONNECT
                if elapsed < COOLDOWN_SECONDS:
                        remaining = COOLDOWN_SECONDS - elapsed
                        print(f"Waiting {int(remaining)}s before attempting reconnects to recently disconnected device")
                        time.sleep(remaining)
                LAST_DISCONNECT = None

        while status == 2:
                print("Bluetooth DOWN")
                print(status)
                with open(PREV_CONN_PATH) as fp:
                        conns = json.load(fp)
                previous_connections = conns.get('previous_addresses', {}).items()
                for i,conn in previous_connections:
                        print('Attempting to Pair to {}'.format(conn.get('name')))
                        output = connect_to_bt_device(conn.get('mac_addr'), numloop)
                        print(f"{output = }")
                        time.sleep(10)
                        status = subprocess.call('ls /dev/input/event0 2>/dev/null', shell=True)
                        if status == 0:
                            print("Device connected while searching — stopping search")
                            break
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
                if ACTIVE_MAC_ADDRESS and ACTIVE_MAC_ADDRESS in [x.get('mac_addr') for x in conns.get('previous_addresses', {}).values()]:
                        conns['previous_addresses'][i]['connection_count'] += 1
                else:
                        fresh_conn = compile_fresh_connection()
                        total_prev_conns = len(conns.get('previous_addresses', {})) + 1
                        conns["previous_addresses"][str(total_prev_conns)] = fresh_conn
                with open(PREV_CONN_PATH, 'w') as fp:
                        json.dump(conns, fp)
                blue_it()

blue_it()
