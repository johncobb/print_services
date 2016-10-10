import subprocess
import platform # platform.system()

NEW_PASSWORD_HASH = '"blah"'

def getCommands():
    commands =  [
        #'set /config/system/users/0/password ' + NEW_PASSWORD_HASH,
        'set /config/system/timezone "+6"'
    ]
    return ['"' + command + '"' for command in commands]

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

if __name__ == '__main__':
    main()
