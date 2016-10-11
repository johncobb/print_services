import os
import subprocess
import time
import platform # platform.system()

NEW_PASSWORD_HASH = '""'

def getCommands():
    """List of commands to be executed on the modem for initial setup.
    Each element of the list is a command which is executed in a remote ssh
    session on a CradlePoint LBR650LPE-VZ modem.
    """
    return [
        'set /config/system/timezone "+6"',

        'set /config/firewall/macfilter/enabled true',

        'set /config/dhcpd/reserve [{"enabled":true, "ip6_address": null, "hostname":"raspberrypi", "ip_address":"192.168.0.2", "mac":"' + getPiMacAddress() + '", "duid":"01:b8:27:eb:fb:ca:79"}]',

        'set /config/firewall/portfwd [{"enabled": true, "ip_address": "192.168.0.2", "lan_port_offt": 22, "name": "PiPrinter", "protocol": "both", "wan_port_end": 2022, "wan_port_start":2022}]',

        'set /config/firewall/remote_admin {"enabled":true, "port":8080, "restrict_ips":false, "secure_only":true, "secure_port":8443, "usb_logging":false, "allowed_ips":[]}'
    ]

def main():
    commands = getCommands()
    sshpassCommand = getSshpassCommand()

    for command in commands:
        if subprocess.call(sshpassCommand + [command]) != 0:
            pass

    subprocess.call(sshpassCommand + ['reboot']) # send reboot cmd to modem
    setPassword()

def setPassword():
    """Attempts to reset the password until successful. The modem is
    rebooting so this may take several attempts.
    """
    passwordCommand = 'set /config/system/users/0/password ' + NEW_PASSWORD_HASH
    while subprocess.call(sshpassCommand + [passwordCommand]) != 0:
        time.sleep(5)

def getModemDefaultPassword():
    """The modem's default password is the
    last 8 digits of its mac address
    """
    arpRet = subprocess.check_output(['arp'])
    while arpRet == '':
        arpRet = subprocess.check_output(['arp'])
        time.sleep(5)

    arpLines = [line.split() for line in arpRet.split('\n')[:-1]]
    arpDict = {key: val for key, val in zip(arpLines[0], arpLines[1])}
    return arpDict['HWaddress'].replace(':', '')[-8:]

def getSshpassCommand():
    """The command to send remote commands
    with a password to the modem
    """
    return ('sshpass -p ' + getModemDefaultPassword() + ' ssh -oStrictHostKeyChecking=no admin@cp').split()

def getPiMacAddress():
    with open('/sys/class/net/eth0/address', 'r') as macFile:
        return macFile.read().replace('\n', '')

if __name__ == '__main__':
    main()
