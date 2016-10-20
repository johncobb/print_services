import os
import subprocess
import time
import re
import urllib2 as url
import platform # platform.system()

NEW_PASSWORD_HASH = ''
PRINTER_ID_API_URL = ''

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

        'set /config/firewall/remote_admin {"enabled":true, "port":8080, "restrict_ips":false, "secure_only":false, "secure_port":8443, "usb_logging":false, "allowed_ips":[]}',

        'set /config/firewall/ssh_admin {"enabled": true, "port": 22, "weak_ciphers": false, "remote_access": true}',

        'set /config/system/ui_activated true',

        'set /config/firewall/macfilter {"enabled": true, "macs": [{"addr": "' + getPiMacAddress() + '"}], "whitelist": true}'
    ]

def main():
    if NEW_PASSWORD_HASH == '""':
        print('[ERROR]: Must initialize new password hash. Exiting.')
        return
    commands = getCommands()
    blockUntilModemFound()
    sshpassCommand = getSshpassCommand()

    for command in commands:
        print('Calling: ' + " ".join(sshpassCommand + [command]))
        if subprocess.call(sshpassCommand + [command]) != 0:
            pass

    ip = getOutwardIp()

    subprocess.call(sshpassCommand + ['reboot']) # send reboot cmd to modem
    print('Sleep for 60 seconds.')
    time.sleep(60)
    setPassword()

    ids = requestPrinterIds(ip)
    subprocess.call(['../setup'] + ids)
    os.system('sudo shutdown -r now')

def setPassword():
    """Attempts to reset the password until successful. The modem is
    rebooting so this may take several attempts.
    """
    blockUntilModemFound()
    passwordCommand = 'set /config/system/users/0/password ' + NEW_PASSWORD_HASH
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

def getOutwardIp():
    while True:
	result = os.popen(" ".join(getSshpassCommand()) + ' "get /status/wan/ipinfo/ip_address"').readlines()
        print('IP Result: ' + str(result))
	result = result[0]
	foundIp = re.search('".*"', result)
	if foundIp:
	    return foundIp.group(0)
	time.sleep(5)

def requestPrinterIds(outwardIp):
    while True:
        try:
            resp = url.urlopen(url.Request(PRINTER_ID_API_URL))
            return resp.readlines()
        except url.URLError as e:
            print('Printer ID Request Failed.')

if __name__ == '__main__':
    main()
