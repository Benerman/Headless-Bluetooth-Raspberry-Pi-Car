import os
import json
from flask import Flask, redirect, render_template, Response, request, url_for
import datetime
import zmq

data={}
now=datetime.datetime.now()
time_string=now.strftime("%Y-%m-%d %H:%M")
template_data={
	'title':'Raspberry Pi 3B+ Web Controller',
	'time':time_string,
	'data':data,
}

# Create a context
context = zmq.Context()

# Create a publisher socket
publisher = context.socket(zmq.PUB)
publisher.bind("tcp://*:5555")

app=Flask(__name__)

def get_data():
    # Do something here
	conns = load_json()
	data = {**conns}
	return data

def load_json(file_path="previous_connections.json"):
	with open(file_path) as fp:
			return json.load(fp)


@app.route('/')
def index():
	now=datetime.datetime.now()
	time_string=now.strftime("%Y-%m-%d %H:%M")
	data=get_data()
	template_data={
		'title':'GenesisPiZ Web Interface',
		'time':time_string,
		'data':data,
		'addresses': data['previous_addresses']	
	}
	# return render_template('rpi3b_webcontroller.html',**template_data)           
	return render_template('index.html',**template_data)           

# This route is to be used to queue up actions to be performed by the GenesisPiZ
# 


@app.route('/<action_type>', methods=['POST'])
def handle_request(action_type):
	print(f"Button pressed: action_type: {action_type}")
	# a post request is sent without form data
	data = json.loads(request.data.decode())
	index = data.get('address_id')
	if index:
		index -= 1
	message = {
		'action_type': action_type, # 'connect', 'remove', 'priority
		'payload': {
			'index': index,
			'name': data.get('name'),
			'mac_addr': data.get('mac_addr'),
			'default': data.get('default')
		}
	}
	# Publish a message to the topic
	publisher.send_string(json.dumps(message))
	print(f"Message: {message}")
	return redirect(url_for('index'))

# @app.route('/<action_type>?<action_data>') 
# def handle_request(action_type, action_data):
# 	print(f"Button pressed: action_type: {action_type} - action_data: {action_data}")
	# return "OK 200"   
	                      	
if __name__=='__main__':
	# os.system("sudo rm -r  ~/.cache/chromium/Default/Cache/*")
	app.run(debug=True, port=5000, host='0.0.0.0')
	#local web server http://192.168.1.200:5000/
	#after Port forwarding Manipulation http://xx.xx.xx.xx:5000/