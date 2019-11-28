python3 simple-sensor.py -h mqtt.eclipse.org -n testclient -v -i3 -s



mosquitto_pub -h mqtt.eclipse.org -t sensors/testclient/control -m closed

