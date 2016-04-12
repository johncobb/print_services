import threading
import time
import Queue
import serial
from cpdefs import CpDefs
from cpdefs import CpAscii
from cpzpldefs import CpZplDefs as ZPL
from datetime import datetime
from printerinfo import PrinterInfo
#import Adafruit_BBIO.UART as UART
#import Adafruit_BBIO.GPIO as GPIO

class CpPrinterResultCode:
    RESULT_UNKNOWN = 0
    RESULT_OK = 1
    RESULT_ERROR = 2
    RESULT_CONNECT = 3
    RESULT_TIMEOUT = 4

class CpPrinterResponses:
    TOKEN_OK = "OK"
    TOKEN_ERROR = "ERROR"
    TOKEN_CONNECT = "CONNECT"

class CpPrinterDefs:
    CMD_CTLZ = 0x1b
    CMD_ESC = 0x1a

class CpPrinterResult:
    ResultCode = 0
    Data = ""

class CpPrinter(threading.Thread):
    def __init__(self, printerID, printerPort):
        self._target = self.print_handler
        self.__lock = threading.Lock()
        self.printerID = printerID
        self.closing = False # A flag to indicate thread shutdown
        self.printer_commands = Queue.Queue(128)
        self.data_buffer = Queue.Queue(128)
        self.printer_timeout = 0
        self.printerBusy = False
        self.printerResult = CpPrinterResult()
        # Used to find the first 0x00 in the byte stream
        # Once found ignore that message and continue processing
        # onto the next 0x00 found. This is our first full message
        self.ser = serial.Serial(printerPort, baudrate=CpDefs.PrinterBaud, parity='N', stopbits=1, bytesize=8, xonxoff=0, rtscts=0)
        self.local_buffer = []

        # self.response_parser = CpResponseParser()
        # self.printer_errors = self.response_parser.errors
        # self.printer_warnings = self.response_parser.warnings

        threading.Thread.__init__(self)

    def run(self):
        self._target()

    def shutdown_thread(self):
        print 'shutting down CpPrinter...'
        self.__lock.acquire()
        self.closing = True
        self.__lock.release()

        # Wait for print_handler to stop
        # Allow approx 5 sec. before forcing close on serial
        for i in range (0, 10):
            if self.printerBusy:
                time.sleep(.5)
            else:
                break

        if self.ser.isOpen():
            try:
                self.ser.close()
            except Exception, e:
                print "CpPrinter::shutdown_thread ERROR: ", e

    def printer_send(self, cmd):
        if CpDefs.LogVerbosePrinter:
            print 'sending printer command ', cmd
        self.ser.write(cmd)

    def print_handler(self):
        """
            method: print_handler
            1. Open serial port
            2. process local printer commands
            3. accumulate characters over serial port
            4. check for new message indicator (0x00)
            5. enqueue new message
            6. reset the buffer
        """
        if self.ser.isOpen():
            self.ser.close()

        self.ser.open()

        self.printerBusy = True

        while not self.closing:

            # self.update_printer_status()

            if self.printer_commands.qsize() > 0:
                printer_command = self.printer_commands.get(True)
                self.printer_commands.task_done()
                self.printer_send(printer_command)
                if CpDefs.PrinterQueryStatus:
                    self.printer_send(ZPL.ZplPrinterQueryStatus)
                    self.process_response()

                continue
            time.sleep(.005)

        self.printerBusy = False


    def process_response(self):

        time.sleep(.5)
        temp_buffer = ""
        self.local_buffer = []


        #While we have serial data process the buffer
        while(self.ser.inWaiting() > 0):
            # Sanity check for tight loop processing
            if self.closing:
                break

            temp_char = self.ser.read(1)

            # check for start of text
            if temp_char == CpAscii.STX:
                temp_buffer = ""
                continue

            # check for end of text
            if temp_char == CpAscii.ETX:
                # append to local buffer because we can
                # receive multiple stx and etx per read
                self.local_buffer.append(temp_buffer)
            else:
                temp_buffer += temp_char

        return self.local_buffer

    def enqueue_printer(self, cmd):
        try:
            self.data_buffer.put(cmd, block=True, timeout=1)
        except:
            self.__lock.acquire()
            print "The queue is full"
            self.__lock.release()

    def enqueue_command(self, cmd):
        try:
            self.printerBusy = True
            self.printer_commands.put(cmd, block=True, timeout=1)
        except:
            self.__lock.acquire()
            print "The Printer queue is full"
            self.__lock.release()

import sys
import getopt

def printerDataReceived(data):
    print 'Callback function printerDataReceived ', data

def main(argv):
    printerThread = CpPrinter(PrinterInfo.PrinterIds[0], PrinterInfo.PrinterPorts[0])
    printerThread.start()


    if CpDefs.RunAsService == True:
        print "running as service...\r\n"
        while True:
            time.sleep(.005)

    print "running as console...\r\n"
    while True:
        user_input = raw_input(">> ").lower()
                # Python 3 users
                # input = input(">> ")
        if user_input == 'exit':

            printerThread.shutdown_thread()

            while(printerThread.isAlive()):
                time.sleep(.005)

            print "Exiting app"
            break

        elif user_input == 'hoststatus':
            printerThread.enqueue_command(ZPL.ZplHostQueryStatus)

        elif user_input == 'printerstatus':
            printerThread.enqueue_command(ZPL.ZplPrinterQueryStatus)

        elif user_input == 'headdiagnostic':
            printerThread.enqueue_command(ZPL.ZplQueryHeadDiagnostic)

        elif user_input == 'aztec':
            printerThread.enqueue_command("^XA^BY8,0^FT124,209^BON,8,N,0,N,1,^FDYourTextHere^FS^XZ\r")

        elif user_input == 'test':
            in_file = file("../InteriorLabel-corrected.zpl", 'r')
            printerThread.enqueue_command(in_file.read())
            in_file.close()

        elif user_input == 'matrix':
            printerThread.enqueue_command("^XA^FO50,100^BXN,10,200^FDYourTextHere^FS^XZ\r")

        elif user_input == 'qr':
            printerThread.enqueue_command("^XA^FO100,100^BQN,2,10^FDYourTextHere^FS^XZ\r")

        elif user_input[0] == '~':
            # Let's the user send commands to the printer directly
            print '**WARNING** Commands are sent directly to printer. You better know what you are doing.'
            command = raw_input('Enter command: ').tolower()
            if command == "" or command == "exit":
                continue
            printerThread.enqueue_command(command)

        time.sleep(.5)

if __name__ == '__main__':

    main(sys.argv[1:])
