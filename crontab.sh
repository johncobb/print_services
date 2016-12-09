. /home/pi/initenv.sh
. /home/pi/.bashrc
/bin/mv /home/pi/provisioning.log /home/pi/provisioning.log.bak
/usr/bin/python /home/pi/print_services/provision_modem.py > /home/pi/provisioning.log 2>&1
