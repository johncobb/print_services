# 4. crontab: @reboot /usr/bin/python /home/pi/print_services/main.py > /home/pi/log.dat (optional logging)

import sys, getopt
import threading
import time
from datetime import datetime
from cpdefs import CpDefs
from cpdefs import HttpCodes
from printerinfo import PrinterInfo
from cplogger import CpLogger
import serial
import urllib


def main(argv):
    httpListeners = []
    logger = CpLogger()
    for i in xrange(len(PrinterInfo.PrinterIds)):
        printerID = PrinterInfo.PrinterIds[i]
        printerPort = PrinterInfo.PrinterPorts[i]
        printer = CpSyncPrinter(printerID, printerPort, logger)
        httpListeners.append(HttpListener(printer, myLogger))

    pollLoop(httpListeners)

def pollLoop(httpListeners):
    while True:
        for listener in httpListener:
            while listener.poll():
                pass # no action besides what poll does
        time.sleep(CpDefs.MESSAGE_CHECK_DELAY_S)

class CpSyncPrinter:
    def __init__(self, printerID, printerPort, logger):
        self.logger = logger
        self.printerID = printerID
        self.printer_commands = Queue.Queue(128)
        self.printerSerial = serial.Serial(printerPort, baudrate=CpDefs.PrinterBaud, parity='N', stopbits=1, bytesize=8, xonxoff=0, rtscts=0)
        if not self.printerSerial.isOpen():
            self.logger.error("Serial connection not open on port: " + printerPort)

    def send_command(self, command):
        self.printerSerial.write(command)

class HttpListener:
    """
    Polls the RESTful service URL for available print jobs and sends them 
    """
    def __init__(self, printer, logger):
        self.printer = printer
        self.printerID = printer.printerID
        self.logger = logger
        self.apiUrl = CpDefs.API_URL + self.printerID

    def poll(self):
        """
        Polls the printer's URL in CPHandheld's printer RESTful service.

        Returns true if a printer command is sent to the printer. False otherwise.

        The response will be HTTP 204 if no content is received. This is not
        an error.

        HTTP 200 is returned if a printer command is available.

        If a printer command is found it is forwarded to self.printer.send_command
        """
        try:
            httpResponse = urllib.urlopen(self.apiUrl)

            if httpResponse.getcode() == HttpCodes.SUCCESS:
                printerCommand = self.fromHttpResponse(httpResponse)
                self.printer.send_command(printerCommand)
                return True

            elif httpResponse.getcode() == HttpCodes.SUCCESS_NO_CONTENT:
                self.logger.verbose("No Content")
                return False
        except IOError as e:
            self.logger.error("Could not access: " + self.apiUrl)

        return False

    def fromHttpResponse(self, httpResponse):
        return "".join(httpResponse.readlines()).replace('\\r\\n', '\n')


if __name__ == '__main__':
    main(sys.argv[1:])
