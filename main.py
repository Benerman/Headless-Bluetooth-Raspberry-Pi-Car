import os
from flask import Flask, render_template, Response
import datetime


data=[]
now=datetime.datetime.now()
timeString=now.strftime("%Y-%m-%d %H:%M")
templateData={
	'title':'Raspberry Pi 3B+ Web Controller',
	'time':timeString,
	'data':data,
}

app=Flask(__name__)
def getData():
    # Do something here
	return

@app.route('/')
def index():
	now=datetime.datetime.now()
	timeString=now.strftime("%Y-%m-%d %H:%M")
	data=getData()
	templateData={
		'title':'Raspberry Pi 3B+ Web Controller',
		'time':timeString,
		'data':data,
	}
	return render_template('rpi3b_webcontroller.html',**templateData)           

@app.route('/<actionid>') 
def handleRequest(actionid):
	print("Button pressed : {}".format(actionid))
	return "OK 200"   
	                      	
if __name__=='__main__':
	# os.system("sudo rm -r  ~/.cache/chromium/Default/Cache/*")
	app.run(debug=True, port=5000, host='0.0.0.0',threaded=True)
	#local web server http://192.168.1.200:5000/
	#after Port forwarding Manipulation http://xx.xx.xx.xx:5000/