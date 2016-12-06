import os
import subprocess
import time
import re
import urllib2 as url
import platform # platform.system()
import sys
import json

NEW_PASSWORD_HASH = ''
try:
    NEW_PASSWORD_HASH = os.environ['NEW_PASSWORD_HASH']
except KeyError as e:
    print '[ERROR]: Environment not set up correctly.'
    print '         Expecting NEW_PASSWORD_HASH var from shell.'
    sys.exit(1)

def getCommands():
    """List of commands to be executed on the modem for initial setup.
    Each element of the list is a command which is executed in a remote ssh
    session on a CradlePoint LBR650LPE-VZ modem.
    """
    return [
        ('/config/system/timezone', '"+6"'),

        ('/config/firewall/macfilter/enabled', 'true'),

        ('/config/dhcpd/reserve', '[{"enabled":true, "ip6_address": null, "hostname":"raspberrypi", "ip_address":"192.168.0.2", "mac":"' + getPiMacAddress() + '", "duid":"01:b8:27:eb:fb:ca:79"}]'),

        ('/config/firewall/portfwd', '[{"enabled": true, "ip_address": "192.168.0.2", "lan_port_offt": 22, "name": "PiPrinter", "protocol": "both", "wan_port_end": 2022, "wan_port_start":2022}]'),

        ('/config/firewall/remote_admin', '{"enabled":true, "port":8080, "restrict_ips":false, "secure_only":false, "secure_port":8443, "usb_logging":false, "allowed_ips":[]}'),

        ('/config/firewall/ssh_admin', '{"enabled": true, "port": 22, "weak_ciphers": false, "remote_access": true}'),

        ('/config/system/ui_activated', 'true'),

        ('/config/firewall/macfilter', '{"enabled": true, "macs": [{"addr": "' + getPiMacAddress() + '"}], "whitelist": true}')
    ]

def main():
    commands = getCommands()
    blockUntilModemFound()
    sshpassCommand = getSshpassCommand()

    for command in commands:
        setModemVariable(command[0], command[1])

    subprocess.call(getSshpassCommand() + ['reboot'])
    print('Sleep for 60 seconds.')
#    time.sleep(60)
    setPassword()

    os.system('sudo shutdown -r now')

def setModemVariable(path, value):
    """The modem's file system is a JSON key-value store. It
    is accessed with the "get" command and modified with the
    "set" command. This sets the value of path on the modem
    value.

    path -- string -- absolute path of file on modem file system
    value -- string -- JSON string representing the value that
                       path will be set to. Keys are folders and
                       values are their contents.
    """
    sshPassCommand = getSshpassCommand()
    while True:
        try:
            if canonicalizeJSON(getModemVariable(path)) == canonicalizeJSON(value):
                return
            subprocess.call(sshPassCommand + ['set ' + path + ' ' + value])
        except ValueError as e: # Guards against invalid JSON strings
            print str(e)

        except subprocess.CalledProcessError as e:
            print str(e)

def getModemVariable(path):
    """The 'get' command is used to get values from the modem's file system.
    Unfortunately, the modem's SSH implementation is hot garbage, so it
    always returns 255 no matter what. So here we make the call and catch
    the output error and return whatever output we get.
    """
    output = ''
    try:
        output = subprocess.check_output(getSshpassCommand() + ['get ' + path])
    except subprocess.CalledProcessError as e:
        output = e.output

    # The modem sends a leading null byte because it sucks
    return output.replace(b'\0', '')         
    
def setPassword():
    """Attempts to reset the password until successful. The modem is
    rebooting so this may take several attempts.
    """
    blockUntilModemFound()
    passwordCommand = 'set /config/system/users/0/password ' + '"' + NEW_PASSWORD_HASH + '"'
    subprocess.call(getSshpassCommand() + [passwordCommand])

def blockUntilModemFound():
    """wget -q --spider google.com will return 0 whenever there is
    internet connection (more specifically, when google is reachable)
    to determine when there is an internet connection.
    """
    print('Searching for modem...')
    while(subprocess.call('wget -q --spider http://google.com'.split()) != 0):
        pass
    print('Found modem.')

def arp():
    """The arp command finds devices connected to ethernet to the raspberry
    pi. In this case that will only ever be the modem. So, this function
    blocks until the modem is found, then returns the output of arp."""
    arpRet = subprocess.check_output(['/usr/sbin/arp'])
    while arpRet == '':
        arpRet = subprocess.check_output(['/usr/sbin/arp'])
        time.sleep(5)
    return arpRet

def getModemDefaultPassword():
    """The modem's default password is the
    last 8 digits of its mac address
    """
    blockUntilModemFound()
    arpRet = arp()
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

def canonicalizeJSON(jsonStr):
    """Reduces jsonStr to canonical form by loading it as python
    object then parsing it back to a string from the returned object.
    """
    return json.dumps(json.loads(jsonStr))

if __name__ == '__main__':
    main()
