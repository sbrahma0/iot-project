#! python3.4
#Simple Light or door type Sensor that can receive control Information to change state

import paho.mqtt.client as mqtt
#import testclient as mqtt
import json
import os
import time
import logging,random,os
import sys,getopt
#from mqtt_functions import *
options=dict()
brokers=["192.168.1.206","192.168.1.157","192.168.1.204","192.168.1.185","test.mosquitto.org",\
         "broker.hivemq.com","iot.eclipse.org"]
options["broker"]=brokers[6]
options["port"]=1883
options["verbose"]=False
options["username"]=""
options["password"]=""
options["cname"]=""
options["sensor_type"]="light"
options["topic_base"]="sensors"
options["interval"]=10 #loop time when sensor publishes in verbose
options["interval_pub"]=300 # in non chatty mode publish
# status at this interval if 0 then ignore
options["keepalive"]=120
options["loglevel"]=logging.ERROR
cname=""
QOS0=0

mqttclient_log=False

username=""
password=""

chatty=False
interval=2 #loop time when sensor publishes
sensor_pub_interval=300# how often to publish if status is unchanged
##
def command_input(options):
    topics_in=[]
    qos_in=[]

    valid_options="  -h <broker> -b <broker> -p <port>-t <topic> -q QOS -v -h <help>\
 -d logging debug  -n Client ID or Name -i loop Interval\
-s <set states to open and closed> -s1 <set states to speed> -u Username -P Password --h <help>"
    print_options_flag=False
    try:
      opts, args = getopt.getopt(sys.argv[1:],"h:b:i:dk:p:t:q:l:vss1n:r:u:P:")
    except getopt.GetoptError:
      print (sys.argv[0],valid_options)
      sys.exit(2)
    qos=0

    for opt, arg in opts:
        if opt == '-h':
             options["broker"] = str(arg)
        elif opt == "-b":
             options["broker"] = str(arg)
        elif opt == "-i":
             options["interval"] = int(arg)
        elif opt == "-k":
             options["keepalive"] = int(arg)
        elif opt=="-r":
            options["topic_base"]=str(arg)
        elif opt =="-p":
            options["port"] = int(arg)
        elif opt =="-t":
            topics_in.append(arg)
        elif opt =="-q":
             qos_in.append(int(arg))
        elif opt =="-n":
             options["cname"]=arg
        elif opt =="-d":
            options["loglevel"]=logging.DEBUG
        elif opt =="-v":
            options["verbose"]=True
        elif opt == "-P":
             options["password"] = str(arg)
        elif opt == "-u":
             options["username"] = str(arg)        
        elif opt =="-s":
            options["sensor_type"]="door"
              

    lqos=len(qos_in)
    for i in range(len(topics_in)):
        if lqos >i: 
            topics_in[i]=(topics_in[i],int(qos_in[i]))
        else:
            topics_in[i]=(topics_in[i],0)
            
        
    if topics_in:
        options["topics"]=topics_in

#######


##callback all others defined in mqtt-functions.py

def on_message(client,userdata, msg):
    topic=msg.topic
    m_decode=str(msg.payload.decode("utf-8","ignore"))
    logging.debug("Message Received "+m_decode)
    message_handler(client,m_decode,topic)

def message_handler(client,msg,topic):
    if topic==topic_control: #got control message
        print("control message ",msg)
        update_status(client,msg)
    
def on_connect(client, userdata, flags, rc):
    logging.debug("Connected flags"+str(flags)+"result code "\
    +str(rc)+"client1_id")
    if rc==0:
        client.connected_flag=True
        client.publish(connected_topic,1,retain=True)
        #publish connection status
        client.subscribe(options["topics"])
    else:
        client.bad_connection_flag=True 
def on_disconnect(client, userdata, rc):
    logging.debug("disconnecting reason  " + str(rc))
    client.connected_flag=False
    client.disconnect_flag=True
    client.subscribe_flag=False 
#######
def update_status(client,status):
    print("///////////",client)
    status=status.upper()
    if status==states[0] or status==states[1] or status==states[2]: #Valid status
        client.sensor_status=status #update
        print("updating status",client.sensor_status)

def publish_status(client):
    global start_flag #used to publish on start
    pubflag=False
    if start_flag:
        start_flag=False
        pubflag=True
    if time.time()-client.last_pub_time >=options["interval_pub"]:
        pubflag=True
    if time.time()-client.last_pub_time >=options["interval"] and chatty:
        pubflag=True
    logging.debug("old "+str(client.sensor_status_old))
    logging.debug("new "+ str(client.sensor_status))    
    if client.sensor_status_old!=client.sensor_status or pubflag:
        client.publish(sensor_status_topic,client.sensor_status,0,True)
        print("publish on",sensor_status_topic,\
              " message  ",client.sensor_status)
        client.last_pub_time=time.time()
        client.sensor_status_old=client.sensor_status

        

    

def Initialise_client_object():
    mqtt.Client.last_pub_time=time.time()
    mqtt.Client.topic_ack=[]
    mqtt.Client.run_flag=True
    mqtt.Client.subscribe_flag=False
    mqtt.Client.sensor_status=states[1]
    mqtt.Client.sensor_status_old=None
    mqtt.Client.bad_connection_flag=False
    mqtt.Client.connected_flag=False
    mqtt.Client.disconnect_flag=False
    mqtt.Client.disconnect_time=0.0
    mqtt.Client.disconnect_flagset=False
    mqtt.Client.pub_msg_count=0
    
def Initialise_clients(cname):
    #flags set
    print("**********",cname)
    client= mqtt.Client(cname)
    if mqttclient_log: #enable mqqt client logging
        client.on_log=on_log
    client.on_connect= on_connect        #attach function to callback
    client.on_message=on_message        #attach function to callback
    client.on_disconnect=on_disconnect
    #client.on_subscribe=on_subscribe
    #client.on_publish=on_publish
    return client

def Connect(client,broker,port,keepalive,run_forever=False):
    """Attempts connection set delay to >1 to keep trying
    but at longer intervals  """
    connflag=False
    delay=5
    print("connecting ",client)
    badcount=0 # counter for bad connection attempts
    while not connflag:
        logging.info("connecting to broker "+str(broker))
        print("connecting to broker "+str(broker)+":"+str(port))
        print("Attempts ",badcount)
        try:
            res=client.connect(broker,port,keepalive)      #connect to broker
            if res==0:
                connflag=True
                return 0
            else:
                logging.debug("connection failed ",res)
                badcount +=1
                if badcount>=3 and not run_forever: 
                    return -1
                    raise SystemExit #give up
                elif run_forever and badcount<3:
                    delay=5
                else:
                    delay=30

        except:
            client.badconnection_flag=True
            logging.debug("connection failed")
            badcount +=1
            if badcount>=3 and not run_forever: 
                return -1
                raise SystemExit #give up
            elif run_forever and badcount<3:
                delay=5*badcount
            elif delay<300:
                delay=30*badcount
        time.sleep(delay)
                
    return 0
def wait_for(client,msgType,period=.25,wait_time=40,running_loop=False):
    #running loop is true when using loop_start or loop_forever
    client.running_loop=running_loop #
    wcount=0  
    while True:
        logging.info("waiting"+ msgType)
        if msgType=="CONNACK":
            if client.on_connect:
                if client.connected_flag:
                    return True
                if client.bad_connection_flag: #
                    return False
        if not client.running_loop:
            client.loop(.01)  #check for messages manually
        time.sleep(period)
        #print("loop flag ",client.running_loop)
        wcount+=1
        if wcount>wait_time:
            print("return from wait loop taken too long")
            return False
###############

#####

if __name__ == "__main__" and len(sys.argv)>=2:
    command_input(options)
chatty=options["verbose"]
logging.basicConfig(level=options["loglevel"]) #error logging
#use DEBUG,INFO,WARNING,ERROR
if not options["cname"]:
    r=random.randrange(1,10000)
    r=3542
    cname="sensor-"+str(r)
else:
    cname=str(options["cname"])
##May want to change topics
connected_topic=options["topic_base"]+"/connected/"+cname
sensor_status_topic=options["topic_base"]+"/"+cname
topic_control=sensor_status_topic+"/control"
#########
options["topics"]=[(topic_control,0)]
#print(options["topics"])
if not options["verbose"]:
    print("only sending changes")

if options["sensor_type"]=="light":
    states=["ON","OFF"] #possible sensor states
elif options["sensor_type"]=="door":
    states=["OPEN","CLOSED"] #possible sensor states
elif options["sensor_type"]=="fan":
    states=["slowest","fastest"]  
Initialise_client_object() # add extra flags

logging.info("creating client"+cname)
client=Initialise_clients(cname)#create and initialise client object
if options["username"] !="":
    client.username_pw_set(options["username"],options["password"])
client.will_set(connected_topic,0, qos=0, retain=True) #set will
print("starting")
print("Publishing on ",sensor_status_topic)
print("send control to ",topic_control)
print("Sensors States are ",states)
start_flag=True #used to always publish when starting
run_flag=True
#connecting_flag=False
bad_conn_count=0
try:
    while run_flag:
        client.loop(0.05)
        if not client.connected_flag:
            if Connect(client,options["broker"],options["port"],\
                       options["keepalive"],run_forever=True) !=-1:
                if not wait_for(client,"CONNACK"):
                   run_flag=False #break
            else:
                run_flag=False #break
        #subbscribes to control in on_connect calback
        
        if client.connected_flag:
            publish_status(client)
except KeyboardInterrupt:
    print("interrrupted by keyboard")
if client.connected_flag:
    client.publish(connected_topic,0,retain=True)
    time.sleep(1)
    client.disconnect()



