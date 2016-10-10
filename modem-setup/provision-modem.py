import subprocess
import platform # platform.system()

NEW_PASSWORD_HASH = '"blah"'

def getCommands():
    return [
        #'set /config/system/users/0/password ' + NEW_PASSWORD_HASH,
        'set /config/system/timezone "+6"',
        'set /config/firewall/macfilter/enabled "true"',
        'set /config/dhcpd/reserve/0/ip6_address null',
        'set /config/dhcpd/reserve/0/hostname "raspberrypi"',
        'set /config/dhcpd/reserve/0/ip_address "192.168.0.2"',
        'set /config/dhcpd/reserve/0/mac ' + getPiMacAddress(),
        'set /config/dhcpd/reserve/0/duid "01:b8:27:eb:fb:ca:79"',

        'set /config/firewall/portfwd/0/enabled true',
        'set /config/firewall/portfwd/0/ip_address "192.168.0.2"',
        'set /config/firewall/portfwd/0/lan_port_offt 22',
        'set /config/firewall/portfwd/0/name "PiPrinter"',
        'set /config/firewall/portfwd/0/protocol "both"',
        'set /config/firewall/portfwd/0/wan_port_end 2022',
        'set /config/firewall/portfwd/0/wan_port_start 2022',

    ]

def main():
    
    commands = getCommands()
    sshpassCommand = getSshpassCommand()

    for command in commands:
        subprocess.call(sshpassCommand + [command])

def getModemDefaultPassword():
    if platform.system() == 'Darwin':
        return '$PASSWORD'

    arpLines = os.popen('arp').readlines()
    arpLines = [line.split() for line in os.popen('arp').readlines()]
    arpDict = {key: val for key, val in zip(arpLines[0], arpLines[1])}
    return arpDict['HWaddress'].replace(':', '')[-8:]


def getSshpassCommand():
    return ('sshpass -p ' + getModemDefaultPassword() + ' ssh -oStrictHostKeyChecking=no admin@cp').split()

def getPiMacAddress():
    with open('/sys/class/net/eth0/address', 'r') as macFile:
        return macFile.read()

if __name__ == '__main__':
    main()
