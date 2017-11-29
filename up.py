import os
import glob
import ftplib
import time
import httplib, urllib, base64



def ftpUp(paths):
	for x in xrange(0,len(paths)):	
		path = "./faces/" + paths[x] + ".jpg"
		filename = str(x) + ".jpg"
		# filename = ".jpg"
		ftp = ftplib.FTP("brianbartz.com")
		ftp.login("bartzbrian", "Senixodo1")
		ftp.cwd("/public_html/media/")
		myfile = open(path, 'rb')
		ftp.storbinary('STOR ' + filename, myfile)
		myfile.close()
		print("uploaded")


def WhichOnesAreDuplicates(fa):
	if len(fa) != 4:
		return False
	else:
		print("checking against other faces")
		checks = [[0,1],[0,2],[0,3],[1,2],[1,3],[2,3]]
		duplicates = []
		x = 0
		while x < 7:
			time.sleep(.5)
			headers = {
			# Request headers
			'Content-Type': 'application/json',
			'Ocp-Apim-Subscription-Key': '2b80ff373c164984b44382da66fa7295',
			}
			body = {
			"faceId1":fa[checks[x][0]],
			"faceId2":fa[checks[x][1]],
			}
			params = urllib.urlencode({
			})
			try:
				conn = httplib.HTTPSConnection('westus.api.cognitive.microsoft.com')
				conn.request("POST", "/face/v1.0/verify?%s" % params, str(body), headers)
				response = conn.getresponse()
				data = response.read()
				print data
				conn.close()
			except Exception as e:
				print("[Errno {0}] {1}".format(e.errno, e.strerror))
			if "RateLimitExceeded" in data:
				print("duplicate checking timed out because of too many verification calls.\n uploading regardless of duplicate faces")
				return []
			elif "true" in data:
				print("duplicate detected")
				duplicates.append(checks[x])
			x = x + 1
		return duplicates



def main():

	new = max(glob.iglob('./faces/*.jpg'), key=os.path.getctime)
	counter = 4
	faceArray = []

	while True:
		time.sleep(.1)
		currentNew = max(glob.iglob('./faces/*.jpg'), key=os.path.getctime) 
		if currentNew != new:									#if the newest file changes
			print("new image")
			time.sleep(3)									
			files = glob.glob("./faces/*.jpg")					#find the 4 newest face files
			files.sort(key=os.path.getctime)
			if len(files) > 75:									#deletes any files that exceed 75 for efficiency
				toDel = len(files) - 75
				for x in xrange(0,toDel):	
					os.remove(files[x])
			files = list(reversed(files))
			for x in xrange(0,len(files)):
				fid = files[x]
				fid = fid[8:(len(fid)-4)]
				files[x] = fid
			faceArray = files[:4]
			print ("the four newest files: ", faceArray)
			# duplicates = ["greater than zero"]
			# while len(duplicates) > 0:							#while those four faces are not unique
			# 	print ("checking", faceArray)
			# 	duplicates = WhichOnesAreDuplicates(faceArray)	
			# 	print faceArray, duplicates 
			# 	for x in xrange(0,len(duplicates)):				#swap all but one of the duplicates for however many new faces come next in files[]
			# 		print("swapping duplicates")
			# 		faceArray[duplicates[x][1]] = files[counter]
			# 		counter = counter + 1	

			ftpUp(faceArray)       								#upload them to the server once the four are unique

			new = currentNew
			

main()



