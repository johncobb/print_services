import os
import subprocess
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

        'set /config/dhcpd/reserve [{"enabled":true, "ip6_address": null, "hostname":"raspberrypi", "ip_address":"192.168.0.2", "mac":"' + getPiMacAddress() + '", "duid":"01:' + getPiMacAddress() + '"}]',

        'set /config/firewall/portfwd [{"enabled": true, "ip_address": "192.168.0.2", "lan_port_offt": 22, "name": "PiPrinter", "protocol": "both", "wan_port_end": 2022, "wan_port_start":2022}]',

        'set /config/firewall/remote_admin {"enabled":true, "port":8080, "restrict_ips":false, "secure_only":true, "secure_port":8443, "usb_logging":false, "allowed_ips":[]}',

        'set /config/system/users/0/password ' + NEW_PASSWORD_HASH,
    ]

def main():
    commands = getCommands()
    sshpassCommand = getSshpassCommand()

    for command in commands:
        subprocess.call(sshpassCommand + [command])

def getModemDefaultPassword():
    """The modem's default password is the
    last 8 digits of its mac address
    """
    arpLines = os.popen('arp').readlines()
    arpLines = [line.split() for line in os.popen('arp').readlines()]
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
