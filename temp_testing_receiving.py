import time
import json
import datetime
import zmq
import logging

logging.basicConfig(level=logging.DEBUG)
logging.debug("Starting up...")

class BluetoothAction:

    def __init__(self, action_type: str, payload: dict):
        self.action_type = action_type
        self.message = payload
        self.load_json()
        self.prev_connected = self.conns['previous_addresses']

    def __repr__(self):
        return f"BluetoothAction({self.action_type}, {self.message})"

    def debug_info(self, message):
        logging.debug(message)


    def load_json(self, file_path="previous_connections.json"):
        with open(file_path) as fp:
            self.conns = json.load(fp)
        self.debug_info(f"Loaded content from {file_path}")
        
    def save_json(self, file_path="previous_connections.json"):
        with open(file_path, 'w') as fp:
            json.dump(self.conns, fp)
        self.debug_info(f"Saved content to {file_path}")

    def update_previous_addresses(self):
        self.conns['previous_addresses'] = self.prev_connected
        print(f"Updated previous_addresses to {self.prev_connected}")
    
    def update_name(self):
        self.prev_connected[self.message['index']] = self.message['name']
        self.update_previous_addresses()
        self.save_json()
        self.debug_info(f"Updated name to {self.message['name']}") 

    def update_mac_addr(self):
        self.prev_connected[self.message['index']]['mac_addr'] = self.message['mac_addr']
        self.update_previous_addresses()
        self.save_json()
        self.debug_info(f"Updated mac_addr to {self.message['mac_addr']}")

    def update_default(self):
        [e.update({'default': False}) for e in self.prev_connected]
        self.prev_connected[self.message['index']]['default'] = self.message['default']
        self.update_previous_addresses()
        self.save_json()
        self.debug_info(f"Updated default to {self.message['default']}")

    def update_order(self):
        self.prev_connected.insert(self.message['index'], self.prev_connected.pop(self.message['index']))
        self.update_previous_addresses()
        self.save_json()
        self.debug_info(f"Updated order to {self.message['index']}")

    def update(self):
        if self.action_type == 'update_name':
            self.update_name()
        elif self.action_type == 'update_mac_addr':
            self.update_mac_addr()
        elif self.action_type == 'update_order':
            self.update_order()
        elif self.action_type == 'update_default':
            self.update_default()
        else:
            print(f"Invalid action_type: {self.action_type}")

    def add_entry(self):
        new_entry = {
            'name': self.message['name'],
            'mac_addr': self.message['mac_addr'],
            'connecton_count': 0,
            'default': False
            }
        self.prev_connected.append(new_entry)
        self.update_previous_addresses()
        self.save_json()
        self.debug_info(f"Added entry: {new_entry}")

    def remove_entry(self):
        try:
            self.prev_connected.pop(self.message['index'])
            self.update_previous_addresses()
            self.save_json()
        except IndexError:
            print(f"Index {self.message['index']} out of range")

    def connect(self):
        raise NotImplementedError

    def process_message(self):
        if self.action_type == "connect":
            self.connect()
        elif "update" in self.action_type:
            self.update()
        elif self.action_type == "add":
            self.add_entry()
        elif self.action_type == "delete":
            self.remove_entry()
        else:
            print(f"No action performed due to invalide 'action_type' - {self.action_type}")
        self.debug_info(f"Processed message: {self.message}")



context = zmq.Context()

# Create a subscriber socket
subscriber = context.socket(zmq.SUB)
subscriber.connect("tcp://localhost:5555")
subscriber.setsockopt_string(zmq.SUBSCRIBE, '')

if __name__ == '__main__':
    while True:
        time.sleep(1)
        message = json.loads(subscriber.recv_string())
        if message:
            print(f"Received: {message}")
            bta = BluetoothAction(message['action_type'], message['payload'])
            bta.process_message()
        # # Receive the message on the subscriber socket
        # print(f"Received: {subscriber.recv_string()}")
