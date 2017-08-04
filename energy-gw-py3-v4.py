#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import sys, os

#logging.getLogger('openzwave').addHandler(logging.NullHandler())
#logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger('openzwave')

### openzwave dependencies #####
import openzwave
from openzwave.node import ZWaveNode
from openzwave.value import ZWaveValue
from openzwave.scene import ZWaveScene
from openzwave.controller import ZWaveController
from openzwave.network import ZWaveNetwork
from openzwave.option import ZWaveOption
import time
#rustamchange#from louie import dispatcher, All

import six
if six.PY3:
   from pydispatch import dispatcher
   import _thread as thread
else:
   from louie import dispatcher
   import thread


### mqtt dependencies and event handlers #######
import paho.mqtt.client as mqtt
import json
from time import sleep
from datetime import datetime
import threading

def on_connect(client, userdata, flags, rc):
   print("Connected with result code", str(rc))

   client.subscribe("/keti/energy/fromserver/")
   client.subscribe("/keti/energy/statusrequest")
   print("Subscribed to topics fromserver and statusrequest")

def on_message(client, userdata, msg):
   #print(msg.topic, " ", str(msg.payload))
   if msg.topic == "/keti/energy/statusrequest":
      client.publish("/keti/energy/systemstatus", '{"nodename":"Gateway", "status":"on"}')
      

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect("117.16.136.173", 1883, 600)
#mqtt_client = None

def MQTTStarterThread():
   mqtt_client.loop_start()

t = threading.Thread(target=MQTTStarterThread())
t.start()


def generateSensorDataDict(sname, sid, stat, temperature, humidity, trainID):
   sensordata = dict()
   sensordata['TrainID']=trainID
   sensordata['SensorName']=sname
   sensordata['SensorID']=sid
   if stat==False:
      sensordata['Status']='On'
   else:
      sensordata['Status']='Off'
   sensordata['temp']= (temperature-32)/1.8 #convert to celsius#temperature
   sensordata['hum']=humidity
   sensordata['timestamp']=str(datetime.now())
   return sensordata

def sendSensorData(mqttclient, sensordata):
   mqttclient.publish("/keti/energy/fromgw", json.dumps(sensordata))
   print("mqtt message is sent!")
   #print("mqtt mock interaction")

################################################

device="/dev/ttyACM0"
#device="/dev/ttyUSB0"
log="None"
sniff=300.0

trainID = "111"

for arg in sys.argv:
    if arg.startswith("--device"):
        temp,device = arg.split("=")
    elif arg.startswith("--log"):
        temp,log = arg.split("=")
    elif arg.startswith("--sniff"):
        temp,sniff = arg.split("=")
        sniff = float(sniff)
    elif arg.startswith("--help"):
        print("help : ")
        print("  --device=/dev/yourdevice ")
        print("  --log=Info|Debug ")
        print("  --trainID=1901 ")
    #rustamchange adding train id related argument
    elif arg.startswith("--trainID"):
        temp,trainID = arg.split("=")

#Define some manager options
options = ZWaveOption(device, \
  config_path="../openzwave/config", \
  user_path=".", cmd_line="")
options.set_log_file("OZW_Log.log")
options.set_append_log_file(False)
options.set_console_output(False)
options.set_save_log_level(log)
options.set_logging(True)
options.lock()

def louie_network_started(network):
    print("Hello from network : I'm started : homeid {:08x} - {} nodes were found.".format(network.home_id, network.nodes_count))

def louie_network_failed(network):
    print("Hello from network : can't load :(.")

def louie_network_ready(network):
    print("Hello from network : I'm ready : {} nodes were found.".format(network.nodes_count))
    print("Hello from network : my controller is : {}".format(network.controller))
    dispatcher.connect(louie_node_update, ZWaveNetwork.SIGNAL_NODE)
    dispatcher.connect(louie_value_update, ZWaveNetwork.SIGNAL_VALUE)

def louie_node_update(network, node):
    print("Hello from node : {}.".format(node))

def louie_value_update(network, node, value):
    print("Hello from value : {}.".format( value ))


#rustamchange# Signal events experiments ##############
global driverisready

def louie_driver_ready(network):
    print("The driver is READY !!!!!")
    driverisready = True

def signal_event_NodeQueriesComplete(network):
    print("Signal Event Node Queries Complete!")

def signal_event_AwakeNodesQueried(network):
    print("Signal Event Awake Nodes Queried !")

def signal_value_refreshed(network, node, value):
    print('Signal value refreshed')

#rustamchange ##################################################################
driverisready = False
dispatcher.connect(louie_driver_ready, ZWaveNetwork.SIGNAL_DRIVER_READY)
dispatcher.connect(signal_event_NodeQueriesComplete, ZWaveNetwork.SIGNAL_NODE_QUERIES_COMPLETE)
dispatcher.connect(signal_event_AwakeNodesQueried, ZWaveNetwork.SIGNAL_AWAKE_NODES_QUERIED)
dispatcher.connect(signal_value_refreshed, ZWaveNetwork.SIGNAL_VALUE_REFRESHED)
################################################################################


#Create a network object
#rustamchange#orig#network = ZWaveNetwork(options, autostart=False)
network = ZWaveNetwork(options)

#We connect to the louie dispatcher
dispatcher.connect(louie_network_started, ZWaveNetwork.SIGNAL_NETWORK_STARTED)
dispatcher.connect(louie_network_failed, ZWaveNetwork.SIGNAL_NETWORK_FAILED)
dispatcher.connect(louie_network_ready, ZWaveNetwork.SIGNAL_NETWORK_READY)


#rustamchange# polling issues
#print("network get poll interval: ", network.get_poll_interval())
#network.set_poll_interval()
#print("network set poll interval is called!: ", network.get_poll_interval())


#whilecounter = 1
#while whilecounter>0:
#   whilecounter-=1
#
#   network.start()
#network.start()

whilecounter = 100

while whilecounter>0: # when forever is needed put just True:
   #whilecounter -= 1
   #network.heal()
   #We wait for the network.

   print("***** Waiting for network to become ready : ")
   for i in range(0,90):
      if network.state>=network.STATE_READY:
         print("***** Network is ready")
         break
      else:
         sys.stdout.write(".")
         sys.stdout.flush()
         time.sleep(1.0)

   #rustamchange#debugging purpose   
   print('Driver is ready:', driverisready)

   #time.sleep(5.0)

   #We update the name of the controller
   print("Update controller name")
   network.controller.node.name = "Hello name"

   #rustamchange#out#time.sleep(5.0)

   #We update the location of the controller
   print("Update controller location")
   network.controller.node.location = "Hello location"

   """ rustamchange#comment out
   time.sleep(5.0)

   for node in network.nodes:
      for val in network.nodes[node].get_switches() :
         print("Activate switch")
         network.nodes[node].set_switch(val,True)
         time.sleep(10.0)
         print("Deactivate switch")
         network.nodes[node].set_switch(val,False)
   #We only activate the first switch
   #exit

   time.sleep(5.0)
   """

   #rustamchange#experiment
   #network.get_value(-1)
   #print("network.get_value(-1) is just called")
   #network.set_poll_interval()
   #print("network set poll interval is called!")


   #while True:
   print("Checking nodes in the network",len(network.nodes))

   for node in network.nodes:
      #rustamchange# request state
      network.nodes[node].request_state()

      
      #ret = network.nodes[node].neighbor_update()
      time.sleep(2.0)
      #print('ret =', ret)
      #network.controller.kill_command()

      #time.sleep(2.0)
      #print('Updating network for 4 seconds')
      #network.nodes[node].network_update()    
      #time.sleep(4.0)

      #sensordata = generateSensorDataDict('TempHum',network.nodes[node].name,network.nodes[node].is_failed,  )

      #print("device_type = ", network.nodes[node].device_type)
      print("is device failed = ", network.nodes[node].is_failed)
      #print("is device awake  = ", network.nodes[node].is_awake)
      #print("is device ready  = ", network.nodes[node].is_ready)
      #print("is routing device = ", network.nodes[node].is_routing_device)
    
      if network.nodes[node].is_failed == True:
         print("------------ probably  dead node ---------------")
         sensordata = generateSensorDataDict('TempHum',node,True, temperature, humidity, trainID)
         sendSensorData(mqtt_client, sensordata)
         continue
    
      #get sensor information
      print("Sensor value = ", network.nodes[node].get_sensor_value(1))
      print("Number of Sensors: ", len(network.nodes[node].get_sensors('All')) )
      temperature = -1
      humidity = -1
   
      print('Product Name = ', network.nodes[node].product_name)

      
      if False:  #network.nodes[node].product_name.find('MultiSensor') != -1:
         #request current interval
         print('Request node interval with 111')
         network.nodes[node].get_sensors()
         print('request all config params = ', network.nodes[node].request_all_config_params())
         print('param 111: ', network.nodes[node].request_config_param(0x84))
         network.nodes[node].set_config_param(1, 255)

         network.nodes[node].set_config_param(101, 241)
         time.sleep(5.0)
         network.nodes[node].set_config_param(111, 20)
         time.sleep(5.0)
         print('Done request node of interval with 111')

      for val in network.nodes[node].get_sensors('All'):
         
         print("value = ", val)
         print("node/name/index/instance : {}/{}/{}/{}".format(node, network.nodes[node].name, network.nodes[node].values[val].index, network.nodes[node].values[val].instance) )
         print("  label/help : {}/{}".format(network.nodes[node].values[val].label, network.nodes[node].values[val].help) )
         print("  id on the network : {}".format(network.nodes[node].values[val].id_on_network))
         print("  value: {} {}".format(network.nodes[node].get_sensor_value(val), network.nodes[node].values[val].units) )
         #if network.nodes[node].values[val].label == 'Temperature':
         #if network.nodes[node].values[val].instance == 2:
         if network.nodes[node].values[val].index == 1:
            temperature = network.nodes[node].get_sensor_value(val)
         #if network.nodes[node].values[val].label == 'Relative Humidity':
         #if network.nodes[node].values[val].instance == 3:
         if network.nodes[node].values[val].index == 5:
            humidity = network.nodes[node].get_sensor_value(val)

      if temperature != -1 or humidity != -1:
         print("-------------------------------- generateSensorDataDict has been called -------------------",temperature, humidity)
         sensordata = generateSensorDataDict('TempHum',node,network.nodes[node].is_failed, temperature, humidity, trainID)
         print("---- sensor data = ", sensordata)
         sendSensorData(mqtt_client, sensordata)
      
      #else:  # this else has been wrong decision
      #   print("------------ probably  dead node --------------- ")
      #   sensordata = generateSensorDataDict('TempHum',node,True, temperature, humidity)
      #   sendSensorData(mqtt_client, sensordata)

           
       

#   time.sleep(10.0)
#   network.stop()

#rustamchange#experiment#reseting
#network.manager.resetController(0x0161d83f)
#time.sleep(5.0)
#print("type = ", type(manager))
###########



###### inclusion process ############
"""
print("Start adding devices.")
network.controller.add_node(False)
current = None
SLEEP = 45

for i in range(0, SLEEP):
   #if self.ctrl_state_result != None and self.ctrl_sate_result not in self.network.controller.STATES_LOCKED:
   #   current = self
   print("+",)
   time.sleep(1.0)
network.controller.cancel_command()
print("stopped searching!")
"""
#####################################

network.stop()


