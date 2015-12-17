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
from cpdefs import CpDefs

def printerDataReceived(data):
    print 'Callback function printerDataReceived ', data
    pass
    
def inetDataReceived(data):
    #print 'Callback function inetDataReceived ', data
    pass

def main(argv):
    
#     try:
#         opts, args = getopt.getopt(argv,"hm:",["mode="])
#     except getopt.GetoptError:
#         print 'main.py -m <service>|<console>'
#         sys.exit(2)
#         
#     for opt, arg in opts:
#         if opt == '-h':
#             print 'main.py.py -m <service>|<console>'
#             sys.exit()
#         elif opt in ("-m", "--mode"):
#             runas = arg.strip()
#             
#     if runas not in ("console", "service"):
#         print "Error invalid command line argument (%s)" % runas
#         exit(1)
        
    
    printerThread = CpPrinter(printerDataReceived)
    printerThread.start()
    
    printerServiceThread = CpPrinterService(printerThread, inetDataReceived)
    printerServiceThread.start()
    
    if CpDefs.RunAsService == True:
        print "running as service...\r\n"
        while True:
            time.sleep(.005)
    
    
    print "running as console...\r\n"
    while True:
        input = raw_input(">> ")
                # Python 3 users
                # input = input(">> ")
        if input == 'exit' or input == 'EXIT':
            printerServiceThread.shutdown_thread()
            
            while(printerServiceThread.isAlive()):
                time.sleep(.005)
                
            printerThread.shutdown_thread()
            
            while(printerThread.isAlive()):
                time.sleep(.005)
                
            print "Exiting app"
            break
        elif input == '0':
            printerServiceThread.enqueue_packet(CpDefs.PrinterId)
        elif input == '1':
            printerThread.enqueue_command("hello world\r")
        elif input == 'aztec':
            printerThread.enqueue_command("^XA^BY8,0^FT124,209^BON,8,N,0,N,1,^FDYourTextHere^FS^XZ\r")
        elif input == 'matrix':
            printerThread.enqueue_command("^XA^FO50,100^BXN,10,200^FDYourTextHere^FS^XZ\r")      
        elif input == 'qr':
            printerThread.enqueue_command("^XA^FO100,100^BQN,2,10^FDYourTextHere^FS^XZ\r")        
        else:
            pass

            
        time.sleep(.5)

if __name__ == '__main__':
    
    main(sys.argv[1:])
    
