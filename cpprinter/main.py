# deployment checklist:
# 0. CpDefs.SiteId = "???"
# 1. CpDefs.RunAsService = True
# 2. CpDefs.PrinterPort = "/dev/ttyUSB0"
# 3. CpDefs.WatchdogWaitNetworkInterface = True
# 4. crontab: @reboot /usr/bin/python /home/pi/print_services/main.py > /home/pi/log.dat (optional logging)

import sys, getopt
import threading
import time
from datetime import datetime
from cpdefs import CpDefs
from cpprinterservice import CpPrinterService
from cpprinter import CpPrinter
from printerid PrinterInfo

def main(argv):

    printerServices = []
    for i in xrange(len(PrinterInfo.PrinterIds)):
        printerID = PrinterInfo.PrinterIds[i]
        printerPort = PrinterInfo.PrinterPorts[i]
        printerThread = CpPrinter(printerID, printerPort)
        printerThread.start()

        printerServiceThread = CpPrinterService(printerThread)
        printerServiceThread.start()

        printerServices.append(printerServiceThread)
    

    if CpDefs.RunAsService == True:
        print "running as service...\r\n"
        while True:
            time.sleep(.005)

    printerServiceThread = printerServices[0]

    print "running as console...\r\n"
    while True:
        input = raw_input(">> ").lower()

        if input == 'exit':
            printerServiceThread.shutdown_thread()

            while printerServiceThread.isAlive():
                time.sleep(.005)

            printerThread.shutdown_thread()

            while printerThread.isAlive():
                time.sleep(.005)

            print "Exiting app"
            break

        time.sleep(.5)

if __name__ == '__main__':

    main(sys.argv[1:])

