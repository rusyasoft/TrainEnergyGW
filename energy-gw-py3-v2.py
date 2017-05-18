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
from louie import dispatcher, All

### mqtt dependencies and event handlers #######
import paho.mqtt.client as mqtt
import json
from time import sleep
from datetime import datetime

def on_connect(client, userdata, flags, rc):
   print("Connected with result code", str(rc))

   client.subscribe("/keti/energy/fromserver/")

def on_message(client, userdata, msg):
   print(msg.topic, " ", str(msg.payload))

mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

mqtt_client.connect("117.16.136.173", 1883, 60)


def generateSensorDataDict(sname, sid, stat, temperature, humidity):
   sensordata = dict()
   sensordata['SensorName']=sname
   sensordata['SensorID']=sid
   if stat==False:
      sensordata['Status']='On'
   else:
      sensordata['Status']='Off'
   sensordata['temp']=temperature
   sensordata['hum']=humidity
   sensordata['timestamp']=str(datetime.now())
   return sensordata

def sendSensorData(mqttclient, sensordata):
   mqttclient.publish("/keti/energy/fromgw", json.dumps(sensordata))

################################################

device="/dev/ttyACM0"
#device="/dev/ttyUSB0"
log="None"
sniff=300.0

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
        print("  --log=Info|Debug")

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

#def louie_driver_ready(network, driver):
#    print("The driver is READY !!!!!")

#Create a network object
network = ZWaveNetwork(options, autostart=False)

#We connect to the louie dispatcher
dispatcher.connect(louie_network_started, ZWaveNetwork.SIGNAL_NETWORK_STARTED)
dispatcher.connect(louie_network_failed, ZWaveNetwork.SIGNAL_NETWORK_FAILED)
dispatcher.connect(louie_network_ready, ZWaveNetwork.SIGNAL_NETWORK_READY)

#rustamchange ##################################################################
#dispatcher.connect(louie_driver_ready, ZWaveNetwork.SIGNAL_DRIVER_READY)
################################################################################

while True:
   network.start()
#network.start()

#while True:
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
   #while True:
   print("Checking nodes in the network",len(network.nodes))
   for node in network.nodes:
      ret = network.nodes[node].neighbor_update()
      #time.sleep(3.0)
      #print('ret =', ret)
      #network.controller.kill_command()

      time.sleep(2.0)
      network.nodes[node].network_update()    
      time.sleep(2.0)

      #sensordata = generateSensorDataDict('TempHum',network.nodes[node].name,network.nodes[node].is_failed,  )

      print("device_type = ", network.nodes[node].device_type)
      print("is device failed = ", network.nodes[node].is_failed)
      print("is device awake  = ", network.nodes[node].is_awake)
      print("is device ready  = ", network.nodes[node].is_ready)
      print("is routing device = ", network.nodes[node].is_routing_device)
    
    
    
      #get sensor information
      print("Sensor value = ", network.nodes[node].get_sensor_value(1))
      print("Number of Sensors: ", len(network.nodes[node].get_sensors('All')) )
      temperature = -1
      humidity = -1
   
      for val in network.nodes[node].get_sensors('All'):
         print("value = ", val)
         print("node/name/index/instance : {}/{}/{}/{}".format(node, network.nodes[node].name, network.nodes[node].values[val].index, network.nodes[node].values[val].instance) )
         print("  label/help : {}/{}".format(network.nodes[node].values[val].label, network.nodes[node].values[val].help) )
         print("  id on the network : {}".format(network.nodes[node].values[val].id_on_network))
         print("  value: {} {}".format(network.nodes[node].get_sensor_value(val), network.nodes[node].values[val].units) )
         #if network.nodes[node].values[val].label == 'Temperature':
         if network.nodes[node].values[val].instance == 2:
            temperature = network.nodes[node].get_sensor_value(val)
         #if network.nodes[node].values[val].label == 'Relative Humidity':
         if network.nodes[node].values[val].instance == 3:
            humidity = network.nodes[node].get_sensor_value(val)

      if temperature != -1 or humidity != -1:
         sensordata = generateSensorDataDict('TempHum',node,network.nodes[node].is_failed, temperature, humidity)
         sendSensorData(mqtt_client, sensordata)

 

   time.sleep(10.0)
   network.stop()

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


