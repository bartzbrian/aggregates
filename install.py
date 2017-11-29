import sys
sys.path.insert(1,'/usr/local/Cellar/opencv3/3.2.0/lib/python2.7/site-packages')
import threading
import cv2
import os
import time
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import PIL
import random, string
import dlib
import glob
from skimage import io
import cognitive_face as CF
import httplib, urllib, base64
import json
from operator import itemgetter
import faceAverage
import logging
import numpy
import ftplib

#global vars
KEY = ''  # Replace with a valid Subscription Key here.
CF.Key.set(KEY)
imagePath = os.getcwd()+'/current/current.jpg'
cascPath = os.getcwd()+'/haarcascade_frontalface_default.xml'

#these 3 vars for the dlib facial landmark generator
predictor_path = "./shape_predictor_68_face_landmarks.dat"

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_path)

#FTPs the newest version of the average face to my website for display purposes
def uploadNew():
	print("uploading new aggregate to server\n")
	filename = "Average.jpg"
	ftp = ftplib.FTP("host.com")
	ftp.login("admin", "password")
	ftp.cwd("/public_html/media/")
	myfile = open("./faceAverage/Average.jpg", 'rb')
	ftp.storbinary('STOR ' + filename, myfile)
	myfile.close()
	print("done\n\n\n\n\n\n\n")

#this function will take all the cropped face images and produce and display an averaged image of them 
def averageFace():

	print("producing aggregate with new User data \n")

	faceAverage.Average()

	newImage = Image.open(os.getcwd() + '/faceAverage/average.jpg')
	draw = ImageDraw.Draw(newImage)

	lms = open("./faceAverage/average.txt", "r")
	# print lms.readline()
	lms = lms.readlines()

	for x in xrange(0,68):
		cs = lms[x].split(',')
		draw.ellipse((float(cs[0])-.75, float(cs[1])-.75, float(cs[0])+.75, float(cs[1])+.75), fill=(0,255,0,0))

	newImage.save((os.getcwd()+ '/faceAverage/average.jpg'),'jpeg')

#facial landmark .txt file generation. Necessary for facial averaging 
def generateLandmarks(filename): 
	err = True
	# print("")
	img = io.imread(os.getcwd()+ "/averaging/" + filename + ".jpg")
	dets = detector(img, 1)
	for k, d in enumerate(dets):
		err = False 
		shape = predictor(img, d)
		name = os.getcwd() + "/averaging/" + filename + ".jpg.txt"
		file = open(name,"w")
		for x in xrange(0,68):
			file.write(str(shape.part(x).x) + "," + str(shape.part(x).y) + "\n")
	return err

#random naming function for each face file
def randomword(length):
   return ''.join(random.choice(string.lowercase) for i in range(length))


#returns the likeliest 3 emotions of an input face
def emotion(rectangle):

	#preprocess face rectangle before API call
	neworder=[3,2,0,1]
	rectangle = [ rectangle[i] for i in neworder]
	for x in xrange(0,len(rectangle)):
		rectangle[x] = str(rectangle[x])
	rectangle = ",".join(rectangle)

	headers = {
    # Request headers
    'Content-Type': 'application/octet-stream',
    'Ocp-Apim-Subscription-Key': '4d3648f0ea7f4df299a0c8302d0aacf5',
	}

	#use face rectangle
	params = urllib.urlencode({
		'faceRectangles': rectangle,
	})

	#open image as binary lump for API call
	img = open(imagePath)
	body = img.read()
	img.close()

	try:
		conn = httplib.HTTPSConnection('westus.api.cognitive.microsoft.com')
		conn.request("POST", "/emotion/v1.0/recognize?%s" % params, body, headers)
		response = conn.getresponse()
		data = response.read()
		data = json.loads(data)
		data = (data[0].values())[1]
		data = data.items()
		conn.close()
	except Exception as e:
		print("error occurred")
		return "error,", "could not", "detect emotions", "", "", "", ""

	sorted_data = sorted(data,key=itemgetter(1),reverse=True)

	for x in xrange(0,7):
		(k,v) = sorted_data[x]
		v = v * 100
		v = str(v) + " %"
		replace = (k + " " + v)
		sorted_data[x] = replace

	return sorted_data[0], sorted_data[1], sorted_data[2], sorted_data[3], sorted_data[4], sorted_data[5], sorted_data[6]


#here the most recent image taken will be processed using the cognitive face API
#if it detects faces, it will return the pertinent metadata about that face, 
#and also the bounding box of the face on the image
#this needs to be adapted for multiple faces
def detectFace():
	
	result = CF.face.detect(imagePath,face_id=True,landmarks=False,attributes='age,gender')

	faceRects = []
	faceDetails = []

	for x in xrange(0,len(result)):	
		info = result[x]
		vals = info.values()
		fid = vals[0]
		fr = vals[1].values() 
		fd = vals[2].values()
		n1, n2, n3, n4, n5, n6, n7 = emotion(fr)
		fd.append(n1)
		fd.append(n2)
		fd.append(n3)
		fd.append(n4)
		fd.append(n5)
		fd.append(n6)
		fd.append(n7)
		fd.append(fid)
		faceRects.append(fr)
		faceDetails.append(fd)


	# print faceDetails

	return faceRects, faceDetails


#crops any faces found in the photo and creates a new image of the cropped face
# along with the details found in the API 
def processFace(faceArray,text):
	img = Image.open(imagePath)
	for x in xrange(0,len(faceArray)):
		textArray = text[x]
		coords = faceArray[x]
		box = (coords[3], coords[1], (coords[0] + coords[3]), (coords[2] + coords[1]),)
		area = img.crop(box)
		area = area.resize((1000,1000))
		filename = textArray[len(textArray)-1]

		#saves a version without the extra details to /averaging for faceaveraging 
		#and runs landmark generation on that saved copy
		area.save((os.getcwd()+ "/averaging/" + filename + ".jpg"),'jpeg')
		e = generateLandmarks(filename)
		if e:
			print("\n")
			os.remove(os.getcwd() + "/averaging/" + filename +".jpg")



		#saves a copy of the face onto a new image with the API details into /faces
		new_background = (0, 0, 0)
		mode = area.mode
		newImage = Image.new(mode,(1600,1000),new_background)
		newImage.paste(area,(0,0,1000,1000))

		font = ImageFont.truetype("/Library/Fonts/Courier New.ttf", 40)
		subfont = ImageFont.truetype("/Library/Fonts/Courier New.ttf", 40)
		draw = ImageDraw.Draw(newImage)
		if not e:
			lms = open("./averaging/" + filename + ".jpg.txt", "r")
			lms = lms.readlines()

			for x in xrange(0,68):
				cs = lms[x].split(',')
				draw.ellipse((float(cs[0])-2, float(cs[1])-2, float(cs[0])+2, float(cs[1])+2), fill=(0,255,0,0))

		draw.text((1100,100), "Age:  " + str(textArray[1]), (0,255,0), font=font)
		draw.text((1100,225), "Gender:  " + str(textArray[0]), (0,255,0), font=font)
		draw.text((1100,350), "Emotions:  ", (0,255,0), font=font)
		draw.text((1080,430), str(textArray[2]), (0,255,0), font=subfont)
		draw.text((1080,510), str(textArray[3]), (0,255,0), font=subfont)
		draw.text((1080,590), str(textArray[4]), (0,255,0), font=subfont)
		draw.text((1080,670), str(textArray[5]), (0,255,0), font=subfont)
		draw.text((1080,750), str(textArray[6]), (0,255,0), font=subfont)
		draw.text((1080,830), str(textArray[7]), (0,255,0), font=subfont)
		draw.text((1080,910), str(textArray[8]), (0,255,0), font=subfont)

		draw = ImageDraw.Draw(newImage)
		
		newImage.save((os.getcwd()+ "/faces/" + filename + ".jpg"),'jpeg')

#this is a more rudimentary face detection which I will use 
#to gauge if I even should pass an image to the API, 
#saving me from making extra calls to the API
def isFace(): 
	# Create the haar cascade
	faceCascade = cv2.CascadeClassifier(cascPath)
	# Read the image
	image = cv2.imread(imagePath)
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	# Detect faces in the image
	faces = faceCascade.detectMultiScale(
    	gray,
    	scaleFactor=1.1,
    	minNeighbors=5,
    	minSize=(30, 30)
	)
	if len(faces) > 0:
		return True
	else:
		return False

def takePhoto():
	print("checking...\n")
	cam = cv2.VideoCapture(0)
	s, im = cam.read() # captures image
	cv2.imwrite(os.path.join("current", "current.jpg"),im) # writes image to disk
	cam.release()

def main():
	while True:
		takePhoto()
		if isFace():
			faceLocation, faceDetails = detectFace()
			if len(faceLocation) > 0:
				print("User(s) have appeared\n")
				print("sending user images to the Cloud for analysis by neural network\n")
				print("processing data analysis...\n")
				for x in xrange(0,len(faceDetails)):
					print str(faceDetails[x][0]) + ", age " + str(faceDetails[x][1])
				processFace(faceLocation,faceDetails)
				averageFace()
				uploadNew()
			print "Waiting for users\n"
		else:
			print("Still no user\n")
			print "Waiting for user\n"
		time.sleep(18)
		
if __name__ == "__main__": 
	main()
