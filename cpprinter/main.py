import sys, getopt
import threading
import time
import urllib2
from datetime import datetime
from cpdefs import CpDefs
from cpdefs import HttpCodes
from cplogger import CpLogger
import serial

try:
    from printerinfo import PrinterInfo
except ImportError as e:
    print './setup script has not been run.'
    print 'Check documentation for deployment instructions.'
    exit(0)

def main(argv):
    logger = CpLogger()
    logger.status('**********SYSTEM BOOT**********')

    httpListeners = []
    for i in xrange(len(PrinterInfo.PrinterIds)):
        printerID = PrinterInfo.PrinterIds[i]
        printerPort = PrinterInfo.PrinterPorts[i]
        printer = CpSyncPrinter(printerID, printerPort, logger)
        httpListeners.append(HttpListener(printer, logger))

    pollLoop(httpListeners, logger)

def pollLoop(httpListeners, logger):
    while True:
        for listener in httpListeners:
            while listener.poll():
                pass  # no action besides what poll does

        logger.purgeOldLogs()
        time.sleep(CpDefs.MESSAGE_CHECK_DELAY_S)


class CpSyncPrinter:
    def __init__(self, printerID, printerPort, logger):
        self.logger = logger
        self.printerID = printerID
        self.printerPort = printerPort
        self.printerSerial = serial.Serial(printerPort)

        if not self.isConnected():
            self.logger.error("Serial connection not open on port: " + printerPort)

    @staticmethod
    def isConnected(printerSerialConnection):
        """The raspberry pi has a USB to RS 232 serial adapter attached
        to it which is then connected to the printer. Since the serial
        cable can be unplugged while the USB cable remains connected it
        makes the pyserial.Serial.isOpen method fail to properly determine
        if the device is connected. It also makes other methods such as
        writiable() fail to determine if the printer is actually connected.

        So, by the RS232 standard the DTR and DSR are on all the time as
        they are used to indicate the device is powered on. Given this,
        we can use the getDSR() method to determine if the device is
        truly connected.
        """
        return printerSerialConnection.getDSR()

    def send_command(self, command):
        with serial.Serial(self.printerPort) as printerSerial:
            if not self.isConnected(printerSerial):
                self.logger.error('Could not establish connection to the printer.')
                return
            try:
                printerSerial.write(command)
                self.logger.status('Wrote print command to printer')
            except serial.SerialException as e:
                self.logger.error('Exception: ' + str(e) +
                                  ' on printer command send.')



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
        request = self.generateHttpRequest(self.apiUrl)
        try:
            httpResponse = urllib2.urlopen(request)

            if httpResponse.getcode() == HttpCodes.SUCCESS:
                printerCommand = self.decodeHttpResponse(httpResponse)
                printerCommand = self.stripBeginEnd(printerCommand)
                self.printer.send_command(printerCommand)
                return True

            elif httpResponse.getcode() == HttpCodes.SUCCESS_NO_CONTENT:
                self.logger.verbose('No Content')
                return False

            else:
                self.logger.warning('Unexpected HTTP Response: ' + str(httpResponse.getcode()))
                return False

        except IOError as e:
            errorString = 'Could not access: ' + self.apiUrl + '\n' + str(e)
            self.logger.error(errorString)

        return False

    def generateHttpRequest(self, url):
        """Attaches HTTP header to a url through a urllib2.request.Request object.
        This ensures that the server knows the version of software the printer
        is on in order to prevent print queue build up on version change.
        """
        return urllib2.Request(url,
                               headers={'User-Agent': 'CPH/' + CpDefs.VERSION})

    def decodeHttpResponse(self, httpResponse):
        """Http encodes '\n' and '\r\n' as '\\n'sdf and '\\r\\n' respectively.
        This replaces those as well as removes the begin/end tokens which
        existed in legacy labels for old labels.
        """
        decoded = httpResponse.read().replace('\\r\\n', '\n')
        decoded = decoded.replace('\\n', '\n')
        return self.stripBeginEnd(decoded)

    def stripBeginEnd(self, strCommand):
        """Old labels were preceded by '**CPbegin**' and ended
        with '**CPend**'. This function returns a command with
        those delimiters removed. If strCommand does not have these
        headers then this function is a NoOp
        strCommand -- String -- A ZPL printer command
        """
        return strCommand.replace('**CPbegin**', '').replace('**CPend**', '')


if __name__ == '__main__':
    main(sys.argv[1:])
