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
from cpdefs import HttpCodes
from cpprinterservice import CpPrinterService
from cpprinter import CpPrinter
from printerinfo import PrinterInfo
from cplogger import CpLogger
import urllib


def main(argv):

    printerServices = []
    myLogger = CpLogger()
    for i in xrange(len(PrinterInfo.PrinterIds)):
        printerID = PrinterInfo.PrinterIds[i]
        printerPort = PrinterInfo.PrinterPorts[i]
        printerThread = CpSyncPrinter(printerID, printerPort)
        printerThread.start()

        printerServices.append(HttpPrinter(printerThread, myLogger))

    pollLoop(printerServices)

def pollLoop(printerList):
    while True:
        for printer in printerList:
            while printer.poll():
                pass # no action besides what poll does
        time.sleep(CpDefs.MESSAGE_CHECK_DELAY_S)

class CpSyncPrinter:
    def __init__(self, printerID, printerPort):
        self.printerID = printerID
        self.printer_commands = Queue.Queue(128)
        self.printerSerial = serial.Serial(printerPort, baudrate=CpDefs.PrinterBaud, parity='N', stopbits=1, bytesize=8, xonxoff=0, rtscts=0)

    def send_command(self, command):
        self.ser.write(command)

class HttpPrinter:
    """
    Receives print commands from CPHandheld's printer RESTful service and
    enqueue's those commands in printerThread.
    """
    def __init__(self, printerThread, logger):
        self.printerThread = printerThread
        self.printerID = printerThread.printerID
        self.logger = logger
        self.apiUrl = CpDefs.API_URL + printerID

    def poll(self):
        """
        Polls the printer's URL in CPHandheld's printer RESTful service.

        Returns true if a printer command is sent to the printer. False otherwise.

        The response will be HTTP 204 if no content is received. This is not
        an error.
        """
        try:
            url = "http://10.0.0.130/api/printer/getprintjob/1989"
            httpResponse = urllib.urlopen(self.apiUrl)
            if httpResponse.getcode() == HttpCodes.SUCCESS_NO_CONTENT:
                self.logger.verbose("No Content")
                return False
            printerCommand = "".join(httpResponse.readlines())
            printerCommand = printerCommand.replace('\\r\\n', '\n')
            self.printerThread.enqueue_command(printerCommand)
            self.logger.verbose("Received command: " + printerCommand)
            return True
        except IOError as e:
            self.logger.logError()
            #log "could not access server URL"
            pass

        return False


if __name__ == '__main__':

    main(sys.argv[1:])

