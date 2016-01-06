import threading
import time
import Queue
import serial
from cpresponseparser import CpResponseParser
from cpdefs import CpDefs
from cpdefs import CpAscii
from cpzpldefs import CpZplDefs as ZPL
from datetime import datetime
from cpdebug import debug_func
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
    
    def __init__(self, printerResponseCallbackFunc=None, *args):
        self._target = self.print_handler
        self._args = args
        self.__lock = threading.Lock()
        self.closing = False # A flag to indicate thread shutdown
        self.printer_commands = Queue.Queue(128)
        self.data_buffer = Queue.Queue(128)
        self.printer_timeout = 0
        self.printerResponseCallbackFunc = printerResponseCallbackFunc
        self.printerBusy = False
        self.printerResult = CpPrinterResult()
        self.printerToken = ""
        # Used to find the first 0x00 in the byte stream
        # Once found ignore that message and continue processing
        # onto the next 0x00 found. This is our first full message
        self.ser = serial.Serial(CpDefs.PrinterPort, baudrate=CpDefs.PrinterBaud, parity='N', stopbits=1, bytesize=8, xonxoff=0, rtscts=0)
        self.local_buffer = []

        # Holds a list of strings containing errors/warnings
        # returned by the printer

        self.response_parser = CpResponseParser()
        self.printer_errors = self.response_parser.errors
        self.printer_warnings = self.response_parser.warnings
        threading.Thread.__init__(self)
        
    def run(self):
        self._target(*self._args)
        
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
    
    @debug_func
    def printer_send(self, cmd):
        if CpDefs.LogVerbosePrinter:
            print 'sending printer command ', cmd
        self.ser.write(cmd)

        self.update_printer_status()

    def update_printer_status(self):
        self.ser.write(ZPL.ZplPrinterQueryStatus)
        for response in self.process_response():
            print response
            if ZPL.ZplPrinterStatusIndicator in response:
                self.response_parser.parse_printer_status(response)

        self.printer_errors = self.response_parser.errors
        self.printer_warnings = self.response_parser.warnings
        
        
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

            update_printer_status()
            
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
                        
    def queue_get(self):
        # TODO: Be aware of this forced return of 0x00
        # will return one byte of 0x00 if you aren't checking
        # qsize() before calling queue_get()
        printer_data = "\x00"
        
        if self.data_buffer.qsize() > 0:
            printer_data = self.data_buffer.get(True)
            self.data_buffer.task_done()
            
        return printer_data
                    
    def enqueue_command(self, cmd):
        try:
            self.printerBusy = True
            self.printer_commands.put(cmd, block=True, timeout=1)
        except:
            self.__lock.acquire()
            print "The Printer queue is full"
            self.__lock.release()
    
    def is_timeout(self):
        return datetime.now() >= self.printer_timeout
    
    def is_error(self, token):        
        return token.find(CpPrinterResponses.TOKEN_ERROR) > -1
        
    def printer_parse_result(self, result):
        
        printer_result = CpPrinterResult()
        
        if result.find(CpPrinterResponses.TOKEN_OK) > -1:
            printer_result.Data = result
            printer_result.ResultCode = CpPrinterResultCode.RESULT_OK

        elif result.find(CpPrinterResponses.TOKEN_ERROR) > -1:
            printer_result.Data = result
            printer_result.ResultCode = CpPrinterResultCode.RESULT_ERROR

        elif result.find(CpPrinterResponses.TOKEN_CONNECT) > -1:
            printer_result.Data = result
            printer_result.ResultCode = CpPrinterResultCode.RESULT_CONNECT   

        elif result.find(CpPrinterResponses.TOKEN_NOCARRIER) > -1:
            printer_result.Data = result
            printer_result.ResultCode = CpPrinterResultCode.RESULT_NOCARRIER

        else:
            printer_result.Data = result
            printer_result.ResultCode = CpPrinterResultCode        
            return printer_result

    def printer_send_at(self, callback):
        self.enqueue_command(CpPrinterDefs.CMD_AT)
        self.printerResponseCallbackFunc = callback
   
import sys
import getopt
 
def printerDataReceived(data):
    print 'Callback function printerDataReceived ', data

def main(argv):
    
    printerThread = CpPrinter(printerDataReceived)
    printerThread.start()
    

    if CpDefs.RunAsService == True:
        print "running as service...\r\n"
        while True:
            time.sleep(.005)
    
    print "running as console...\r\n"
    while True:
        user_input = raw_input(">> ").tolower()
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
            in_file = file("PrestigeLabel.zpl", 'r')
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
