import os
import json
from flask import Flask, render_template, Response
import datetime


data={}
now=datetime.datetime.now()
time_string=now.strftime("%Y-%m-%d %H:%M")
template_data={
	'title':'Raspberry Pi 3B+ Web Controller',
	'time':time_string,
	'data':data,
}

app=Flask(__name__)
def get_data():
    # Do something here
	conns = load_json()
	data = {**conns}
	return data

def load_json(file_path="previous_connections.json"):
	with open(file_path) as fp:
			return json.load(fp)

def update_action(action_type, data):
	if action_type:
		conns = load_json
		print(f'{action_type =} - {data =}')
		if action_type == "connect":
			pass
		elif action_type == "remove":
			pass
		elif action_type == "priority":
			pass
		else:
			print(f"No action performed due to invalide 'action_type' - {action_type}")
	


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

@app.route('/<action_type>?<action_data>') 
def handle_request(action_type, action_data):
	print(f"Button pressed: action_type: {action_type} - action_data: {action_data}")
	return "OK 200"   
	                      	
if __name__=='__main__':
	# os.system("sudo rm -r  ~/.cache/chromium/Default/Cache/*")
	app.run(debug=True, port=5000, host='0.0.0.0',threaded=True)
	#local web server http://192.168.1.200:5000/
	#after Port forwarding Manipulation http://xx.xx.xx.xx:5000/