#!/usr/bin/env python

'''
	QX100 interfacing for Python
	Based upon:
		https://github.com/UCSD-E4E/qx100-interfacing
		https://github.com/berak/opencv_smallfry/blob/master/mjpg_serve.py
'''
import socket
import pygame
import sys
import time
import json
import requests
import numpy
import cv2
import cv2.cv as cv
import threading
from cmd import Cmd
import time
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

host = "localhost"
port = 5000

jpg=None
global jpgg
jpgg=None

class LiveviewThread(threading.Thread):
    running = True 
    def __init(self, url):
        threading.Thread.__init__(self)
        self.url = url
        self.running = True
    def run(self):
        s = start_liveview()
        data = open_stream(s)
        while self.running:
            jpg = decode_frame(data)
        data.raw.close()
        cv2.destroyWindow('liveview')
    def stop_running(self):
        self.running = False   

class MyPrompt(Cmd):
    LVthread = LiveviewThread()
    def do_t(self, args):
        take_picture()

    def do_loop(self, args):
        for i in range(int(args)):
            take_picture()
            print i

    def do_start_liveview(self, args):
        self.LVthread.start()
        start_mjpgServer()

    def do_stop_liveview(self, args):
        self.LVthread.stop_running()

    def do_quit(self, args):
        self.do_stop_liveview([])
        raise SystemExit

class CamHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		print self.path
		if self.path.endswith('.mjpg'):
			self.send_response(200)
			self.send_header('Content-type','multipart/x-mixed-replace; boundary=--jpgboundary')
			self.end_headers()
			while True:
				try:
					buf = jpgg					
					#fps counter
					#t0 = time.clock()
					#print t0
					self.wfile.write("--jpgboundary\r\n")
					self.send_header('Content-type','image/jpeg')
					self.send_header('Content-length',str(len(buf)))
					self.end_headers()
					self.wfile.write(bytearray(buf))
					self.wfile.write('\r\n')
					time.sleep(0.004)
				except KeyboardInterrupt:
					break
			return
		if self.path.endswith('.html') or self.path=="/":
			self.send_response(200)
			self.send_header('Content-type','text/html')
			self.end_headers()
			self.wfile.write('<html><head></head><body>')
			self.wfile.write('<img src="http://127.0.0.1:9095/cam.mjpg"/>')
			self.wfile.write('</body></html>')
			return

def start_mjpgServer():
	#global capture
	#capture = jpg
	#capture.set(cv.CV_CAP_PROP_FRAME_WIDTH, 640); 
	#capture.set(cv.CV_CAP_PROP_FRAME_HEIGHT, 480);
	try:
		server = HTTPServer(('',9095),CamHandler)
		print "server started"
		server.serve_forever()
	except KeyboardInterrupt:
		capture.release()
		server.socket.close()
		
def get_payload(method, params):
    return {
    "method": method,
    "params": params,
    "id": 1,
    "version": "1.0"
    }

def take_picture():
    payload = get_payload("actTakePicture", [])
    headers = {'Content-Type': 'application/json'}
    response = requests.post('http://10.0.0.1:10000/sony/camera', data=json.dumps(payload), headers=headers)
    url = response.json()['result']
    strurl = str(url[0][0])
    return strurl

def get_event():
    payload = get_payload("getEvent", [False])
    headers = {'Content-Type': 'application/json'}
    response = requests.post('http://10.0.0.1:10000/sony/camera', data=json.dumps(payload), headers=headers)
    return response

def get_picture(url, filename):
    response = requests.get(url)
    chunk_size = 1024
    with open(filename, 'wb') as fd:
        for chunk in response.iter_content(chunk_size):
            fd.write(chunk)

### LIVEVIEW STUFF
def start_liveview():
    payload = get_payload("startLiveview", [])
    headers = {'Content-Type': 'application/json'}
    response = requests.post('http://10.0.0.1:10000/sony/camera', data=json.dumps(payload), headers=headers)
    url = response.json()['result']
    strurl = str(url[0])
    return strurl

def open_stream(url):
    return requests.get(url, stream=True)

def decode_frame(data):

    # decode packet header
    start = ord(data.raw.read(1))
    if(start != 0xFF):
        print 'bad start byte\nexpected 0xFF got %x'%start
        return
    pkt_type = ord(data.raw.read(1))
    if(pkt_type != 0x01):
        print 'not a liveview packet'
        return
    frameno = int(data.raw.read(2).encode('hex'), 16)
    timestamp = int(data.raw.read(4).encode('hex'), 16)

    # decode liveview header
    start = int(data.raw.read(4).encode('hex'), 16)
    if(start != 0x24356879):
        print 'expected 0x24356879 got %x'%start
        return
    jpg_size = int(data.raw.read(3).encode('hex'), 16)
    pad_size = ord(data.raw.read(1))
    # read out the reserved header
    data.raw.read(4)
    fixed_byte = ord(data.raw.read(1))
    if(fixed_byte is not 0x00):
        print 'expected 0x00 got %x'%fixed_byte
        return
    data.raw.read(115)

    # read out the jpg
    jpg_data = data.raw.read(jpg_size)
    data.raw.read(pad_size)

    global jpgg
    jpgg = jpg_data
    """
    #fps counter
    t0 = time.clock()
    print t0
    """
    return jpgg

prompt = MyPrompt()
prompt.prompt = '> '
prompt.cmdloop('starting qx100 control')