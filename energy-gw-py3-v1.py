import paho.mqtt.client as mqtt
import json
from time import sleep

def on_connect(client, userdata, flags, rc):
   print("Connected with result code", str(rc))

   client.subscribe("/keti/energy/fromserver/")

def on_message(client, userdata, msg):
   print(msg.topic, " ", str(msg.payload))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("117.16.136.173", 1883, 60)

res = dict()
res['SensorName']='TempHum'
res['SensorID']=1
res['Status']='On'
res['temp']=200
res['hum']=123

print(res)
print('---------')
print(json.dumps(res))

for i in range(10):
   res['temp'] += 1
   client.publish("/keti/energy/fromgw", json.dumps(res))
   sleep(1)


#client.loop_forever()

