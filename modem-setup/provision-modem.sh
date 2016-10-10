#!/bin/bash

MODEM_PASSWORD=`./get-modem-pass.py`

sshpass -p $MODEM_PASSWORD ssh -oStrictHostKeyChecking=no admin@cp "set /config/system/users/0/password \$1\$19dea550\$rlEEoW3nT29UXyfY/tuUEg=="
########## DHCP Reservation ##########
