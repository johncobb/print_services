import sys, getopt
import threading
import time
import urllib2
import signal
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

class TimeoutError(Exception):
    pass

def alarmHandler(signum, frame):
    raise TimeoutError("SIGALRM raised")

def main(argv):
    signal.signal(signal.SIGALRM, alarmHandler)
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
            try:
                signal.alarm(30)
                while listener.poll():
                    pass  # no action besides what poll does
                signal.alarm(0)
            except TimeoutError:
                logger.warning("URLOpen halted. Retrying connection.")

        logger.purgeOldLogs()
        time.sleep(CpDefs.MESSAGE_CHECK_DELAY_S)


class CpSyncPrinter:
    def __init__(self, printerID, printerPort, logger):
        self.logger = logger
        self.printerID = printerID
        self.printerPort = printerPort

    def send_command(self, command):
        try:
            with serial.Serial(self.printerPort) as printerSerial:
                try:
                    printerSerial.write(command)
                    self.logger.status('Wrote print command to printer')
                except serial.SerialException as e:
                    self.logger.error('Exception: ' + str(e) +
                                      ' on printer command send.')
        except IOError as e:
            self.logger.error('Failed to open serial port: ' + str(e))



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
