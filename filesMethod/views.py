from django.shortcuts import render

# Create your views here.
from django.http import JsonResponse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import pika
import datetime
import time
import sys
import requests
import urllib.request
import datetime
import mimetypes
import zlib
import zipfile
from django.utils import timezone
import hashlib
import base64

# Create your views here.
class FilesMethods:
	@csrf_exempt
	def startOrchestrator(request):
		newSubProcess = subprocess.Popen("./process_tasks.sh", shell=True,stdout=subprocess.PIPE, preexec_fn=os.setsid)
		FilesMethods.orchestrator(newSubProcess.pid)

	@csrf_exempt
	def orchestrator(pid):
		credentials = pika.PlainCredentials('1506725003', '697670')
		connection = pika.BlockingConnection(pika.ConnectionParameters('152.118.148.103',5672,'1506725003', credentials))
		channel_fanout = connection.channel()
		exchange_fanout = '1506725003_fanout'
		channel_fanout.exchange_declare(exchange=exchange_fanout, exchange_type='fanout', passive=False, durable=False, auto_delete=False)

		result_fanout = channel_fanout.queue_declare('', exclusive=True)
		queue_name_fanout = result_fanout.method.queue
		channel_fanout.queue_bind(
		    exchange=exchange_fanout, queue=queue_name_fanout, routing_key="fanoutdataserver2")

		counterURLBerhasil = 0

		print(' [*] Waiting for logs. To exit press CTRL+C')

		allFilename = []

		def callback(ch, method, properties, body):
			print(" [x] %r:%r" % (method.routing_key, body))
			# print(body.decode("UTF-8"))
			# splitBody = body.decode("UTF-8").split(";")
			msg = body.decode("UTF-8")
			# counter = splitBody[0]
			# urlFile = splitBody[1]
			if msg[:11] == "urlberhasil":
				splitMsg = msg.split(";")
				filename = splitMsg[1]
				print(filename)
				allFilename.append(filename)
				print(len(allFilename))
				if len(allFilename) == 10:
					compressedFileReq = FilesMethods.compress(allFilename)
					url = FilesMethods.createSecureLink(filename)
					channel_fanout.basic_publish(exchange=exchange_fanout,
						routing_key='fanoutdataserver3',
						body=url)
					print(url)
				# channel.basic_publish(exchange=exchange,
				# 	routing_key='fanoutdataserver2',
				# 	body=url)

		channel_fanout.basic_consume(
			queue=queue_name_fanout, on_message_callback=callback, auto_ack=True)

		channel_fanout.start_consuming()

	@csrf_exempt
	def compress(allFilename):
		credentials = pika.PlainCredentials('1506725003', '697670')
		connection = pika.BlockingConnection(pika.ConnectionParameters('152.118.148.103',5672,'1506725003', credentials))
		channel_fanout = connection.channel()
		exchange_fanout = '1506725003_fanout'
		channel_fanout.exchange_declare(exchange=exchange_fanout, exchange_type='fanout', passive=False, durable=False, auto_delete=False)
		ts = datetime.datetime.today().strftime('%d%B%Y%H%M%S')
		filename = ts + "compressed"
		zf = zipfile.ZipFile("../files/" + filename + ".zip", mode="w")
		compression = zipfile.ZIP_DEFLATED
		try:
			counter = 10
			print(allFilename)
			for filename in allFilename:
				print(filename)
				zf.write("../files/" + filename, filename, compress_type=compression)
				channel_fanout.basic_publish(exchange=exchange_fanout,
					routing_key='fanoutdataserver3',
					body="persen " + str(counter))
				print(counter)
				counter += 10
		except FileNotFoundError:
			print("An error occurred")
		finally:
			zf.close()
		# for filepath in allFilepath:
		# 	pass

		return filename

	@csrf_exempt
	def createSecureLink(filename):
		expire = timezone.now() + datetime.timedelta(minutes=10)
		timestamp_expires = str(int(datetime.datetime.timestamp(expire)))
		url = "/files/" + filename
		secret_link_md5 = url + str(timestamp_expires)
		secret_link_md5 = secret_link_md5.encode('utf-8')
		hashMd5 = hashlib.md5(secret_link_md5).digest()
		base64_hash = base64.urlsafe_b64encode(hashMd5)
		str_hash = base64_hash.decode('utf-8').rstrip('=')
		return url + "?md5=" + str_hash + "&expires=" + str(timestamp_expires);

	@csrf_exempt
	def download(url, counter):
	# def download(url):
		# filepath = "files/" + filename
		# url = "http://i3.ytimg.com/vi/J---aiyznGQ/mqdefault.jpg"
		# url = "https://kaboompics.com/download/20325dd642cb3f812afc30aded8babb6/original"
		# url = "https://images.pexels.com/photos/2317020/pexels-photo-2317020.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=750&w=1260"
		downloadFile = urllib.request.urlopen(url)
		mime = mimetypes.guess_type(url, strict=True)
		ext = ""
		if mime != None:
			ext = mimetypes.guess_extension(mime[0])
			print(ext)
		ts = datetime.datetime.today().strftime('%d %B %Y, %H:%M:%S')
		# content_dispotition = downloadFile.getheader('Content-Dispotition')
		# print(content_dispotition)
		# filename = ""
		# if content_dispotition != None;

		filepath = "../files/" + ts + "url" + counter + ext
		# filepath = "../files/" + ts
		datatowrite = downloadFile.read()
		with open(filepath, 'wb') as f:  
		    f.write(datatowrite)

	@csrf_exempt
	def send(request):
		uniqueId = request.META['HTTP_X_ROUTING_KEY']
		credentials = pika.PlainCredentials('1506725003', '697670')
		connection = pika.BlockingConnection(pika.ConnectionParameters('152.118.148.103',5672,'1506725003', credentials))
		channel = connection.channel()
		exchange = '1506725003uas2018'
		channel.exchange_declare(exchange=exchange, exchange_type='direct', passive=False, durable=False, auto_delete=False)

		while(True) :
			ts = datetime.datetime.today()
			print(ts)
			channel.basic_publish(exchange=exchange,
								  routing_key='waktuServer',
								  body=ts)
			print(" [x] Sent " + ts)
			time.sleep(1)
		connection.close()
		return JsonResponse({"status": "ok"})

	@csrf_exempt
	def compressedFile(filename, uniqueId, access_token):
		url = "http://localhost:8300/compressed"
		files = {'filename':filename, 'access_token': access_token}
		header = {'X-ROUTING-KEY': uniqueId}
		r = requests.post(url, data=json.dumps(files), headers=header)
		return JsonResponse({
			"status" : "ok",
			"compressedFileName": "asdasd"
		})
