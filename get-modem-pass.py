import os

arpLines = os.popen('arp').readlines()

arpLines = [line.split() for line in os.popen('arp').readlines()]
arpDict = {key: val for key, val in zip(arpLines[0], arpLines[1])}
print (arpDict['HWaddress'].replace(':', '')[-8:])
