#!/bin/bash

DEFAULT_PASSWORD=`./get-modem-pass.py`
NEW_PASSWORD_HASH=''


########## DHCP Reservation ##########


#### Change Password ####
sshpass -p $DEFAULT_PASSWORD ssh -oStrictHostKeyChecking=no admin@cp "set /config/system/users/0/password \"$NEW_PASSWORD_HASH\""
