There are three components to this repo:

 1. print.go
    A simple script which prints its first argument to /dev/USBtty0. When
    compiled and placed in /home/pi and called 'print' it is called from the
    printserver through ssh to print labels to the ZPL printer.

 2. provision_modem.py
    A setup script which configures the modems DHCP server, firewall, and mac
    filtering so that the only device which has network access through it is
    this pi. It also assigns a static IP to the modem and forwards port 2022
    to port 22 on the pi. This allows the webserver, scripts, technicians, etc.
    to access the device for maintenance/print jobs.

 3. crontab.sh crontab.setup
    crontab.setup is to be installed as the systems crontab file. It executes
    crontab.sh on reboot which sets the environment variable NEW_PASSWORD_HASH
    to the hash of the password for the modem and then executes provision_modem.py.
    At the end of setup the modem's password has been reset from the default.

To install this on a new pi:
    go get github.com/johncobb/print_services
    cd $GOPATH/src/github.com/johncobb/print_services
    go build
    go build print.go
    mv print ~/print
    crontab crontab.setup
    ### Setup a script ~/initenv.sh which initializes the environment
        variable NEW_PASSWORD_HASH to the desired hash of the modem. This
        hash is not kept in the repo for security reasons. Be sure to
        export the variable. ###
