import threading
import time
from datetime import datetime
import Queue
import socket
import mmap
from cpdefs import CpDefs
from cpdefs import CpAscii
from cplog import CpLog
from cpstats import CpInetStats
from cpprinter import CpPrinter

class CpStateKey:
    NUMBER = 'number'
    NAME = 'name'
    TIMEOUT = 'timeout'

class CpPrinterState:
    """
    States are represented as dictionaries with the following attributes:
        CpStateKey.NUMBER  => The State's number. Used as identification
        CpStateKey.NAME    => The string representation of the state. Only used for
                       debugging purposes
        CpStateKey.TIMEOUT => The state's timeout value in seconds
    """

    INITIALIZE = {CpStateKey.NUMBER:0, CpStateKey.NAME:'INITIALIZE', CpStateKey.TIMEOUT:5}
    IDLE       = {CpStateKey.NUMBER:1, CpStateKey.NAME:'IDLE',       CpStateKey.TIMEOUT:30}
    CONNECT    = {CpStateKey.NUMBER:2, CpStateKey.NAME:'CONNECT',    CpStateKey.TIMEOUT:5}
    CLOSE      = {CpStateKey.NUMBER:3, CpStateKey.NAME:'CLOSE',      CpStateKey.TIMEOUT:0}
    SLEEP      = {CpStateKey.NUMBER:4, CpStateKey.NAME:'SLEEP',      CpStateKey.TIMEOUT:30}
    SEND       = {CpStateKey.NUMBER:5, CpStateKey.NAME:'SEND',       CpStateKey.TIMEOUT:5}
    RECEIVE    = {CpStateKey.NUMBER:7, CpStateKey.NAME:'RECEIVE',    CpStateKey.TIMEOUT:10}
    HEARTBEAT  = {CpStateKey.NUMBER:8, CpStateKey.NAME:'HEARTBEAT',  CpStateKey.TIMEOUT:5}
    WAITNETWORKINTERFACE = {CpStateKey.NUMBER:6, CpStateKey.NAME:'WAITNETWORKINTERFACE', CpStateKey.TIMEOUT:120}

class CpInetResultCode:
    RESULT_UNKNOWN = 0
    RESULT_OK = 1
    RESULT_ERROR = 2
    RESULT_CONNECT = 3
    RESULT_SCKTIMEOUT = 4
    RESULT_SCKSENDERROR = 5
    RESULT_SCKRECVERROR = 6
    RESULT_TCPACK = 7
    RESULT_TCPNAK = 8

class CpInetResponses:
    TOKEN_HTTPOK = "HTTP/1.1 200"
    TOKEN_HTTPACCEPTED = "HTTP/1.1 202"
    TOKEN_HTTPNORESPONSE = "HTTP/1.1 204"
    TOKEN_HTTPERROR = "ERROR"
    TOKEN_HTTPCONNECT = "CONNECT"
    TOKEN_TCPACK = "ACK"
    TOKEN_TCPNAK = "NAK"
    TOKEN_TCPHBACK = "HBACK"

class CpInetDefs:
    INET_HOST = CpDefs.InetHost
    INET_PORT = CpDefs.InetPort
    INET_TCPPARAMS = CpDefs.InetTcpParms
    INET_TIMEOUT = CpDefs.InetTimeout
    INET_HEARTBEAT_TIME = 20
    INET_HEARTBEAT = "HB"
    INET_HEARTBEAT_ACK_TIME = 10


class CpInetError:
    InitializeErrors = 0
    InitializeMax = 3
    ConnectErrors = 0
    ConnectMax = 3
    SendErrors = 0
    SendMax = 3
    CloseErrors = 0
    CloseMax = 3

class CpInetResult:
    ResultCode = 0
    Data = ""

class CpWatchdogStatus:
    Success = "1"
    Error = "2"

class InitVars:
    NetWorkActive = 0
    NumTry_Connection = 1
    NumTry_EnableModem = 0
    EchoBaseStatus = 0  #0 = Unreported, 1 = Success, 2 = Fail
    NumTry_EchoBase = 1
    MaxRetry = 3
    TimeDelayIncrement = 5
    RxBytes = 0
    TxBytes = 0
    Format = "%Y-%m-%d %H:%M:%S"
    WatchdogFilePath = "/home/cphappliance/cph/echobase_intel_nuc/watchdog/info.txt"
    DbPath = "/home/cphappliance/cph/echobase_intel_nuc/test.db"
    TimeAtLastReboot = datetime.now()


class IfConfigVars:
    #Interface = 'ppp0'
    Interface = 'eth0'
    RX_bytes = 0
    TX_bytes = 0


class CpPrinterService(threading.Thread):

    def __init__(self, printerThread, inetResponseCallbackFunc=None, *args):
        self._target = self.inet_handler
        self._args = args
        self.__lock = threading.Lock()
        self.closing = False # A flag to indicate thread shutdown
        self.commands = Queue.Queue(32)
        self.inetResponseCallbackFunc = inetResponseCallbackFunc
        self.host = CpInetDefs.INET_HOST
        self.port = CpInetDefs.INET_PORT
        self.sock = None
        self.remoteIp = None
        self.initialized = False
        self.current_state = CpPrinterState.INITIALIZE
        self.inetError = CpInetError()
        self.exponential_backoff = 30
        self.log = CpLog()
        self.state_cb = None
        self.waitRetryBackoff = {1:5, 2:15, 3:30}
        self.inet_stats = CpInetStats()
        self.inet_stats.LastSent = time
        self.command_buffer = "" #stores incomplete commands

        self.heartbeat_ack_pending = False #An ack isn't expected until a heartbeat is sent
        self.last_heartbeat_time = time.time()

        self.ack_queue = Queue.Queue(128)

        self.fmap = {0:self.inet_init,
                     1:self.inet_idle,
                     2:self.inet_connect,
                     3:self.inet_close,
                     4:self.inet_sleep,
                     5:self.inet_send,
                     6:self.inet_waitnetworkinterface,
                     7:self.inet_receive,
                     8:self.inet_heartbeat}

        self.printerThread = printerThread

        threading.Thread.__init__(self)

    def run(self):
        self._target(*self._args)

    def get_queue_depth(self):
        return self.commands.qsize()

    def get_current_state(self):
        return self.current_state[CpStateKey.NAME]

    def get_inet_stats(self):
        return self.inet_stats

    def setStateChangedCallback(self, callback):
        self.state_cb = callback

    def enter_state(self, new_state):
        """
            Sets the next state to new_state
            A call to this will not immediately change the state, but
            but will enter once the current state function has returned.
        """
        self.current_state = new_state
        self.STATEFUNC = self.fmap[self.current_state[CpStateKey.NUMBER]]
        self.timestamp = datetime.now()
        self.timeout = self.current_state[CpStateKey.TIMEOUT]

        if(CpDefs.LogVerboseInet):
            print 'enter_state: (', self.current_state[CpStateKey.NAME], ')'

        # Set the led pattern via state_cb
        # Hack if statement to prevent state_cb from being called before
        # setStateChangedCallback is set by cptaskmanager
        if (self.state_cb == None):
            return
        else:
            self.state_cb(new_state)

    def state_timedout(self):
        if((datetime.now() - self.timestamp).seconds >= self.timeout):

            if(CpDefs.LogVerboseInet):
                print 'state_timeout: (', self.current_state[CpStateKey.NAME], ')'

            return True
        else:
            return False

    def reset_state_timeout(self):
        self.timestamp = datetime.now()

    def inet_init(self):
        try:
            self.remoteIp = socket.gethostbyname(self.host)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if(CpDefs.LogVerboseInet):
                print 'inet_init: successful (%s)' %self.remoteIp

            self.initialized = True
            self.enter_state(CpPrinterState.CONNECT)

            return True
        except socket.gaierror:
            self.log.logError('inet_init: failed (hostname could not be resolved)')
            print 'inet_init: failed (hostname could not be resolved)'
        except socket.error, e:
            for error in e:
                print "error: ", e
            self.log.logError('inet_init: failed (other)')
            print 'inet_init: failed (other)'

        # If we get this far we received an error
        self.handle_inet_init_error()

        return False

    def inet_idle(self):
        """
        """

        #Process print job acks
        while self.ack_queue.qsize() > 0:
            self.sock.send(CpDefs.InetTcpParms % self.ack_queue.get())
            print "Sent ACK"
            self.ack_queue.task_done()

        #If the ack timeout is reached the thread should be recreated
        #This usually signifies a lost internet connection
        heartbeat_elapsed = time.time() - self.last_heartbeat_time
        if self.heartbeat_ack_pending and heartbeat_elapsed >= CpInetDefs.INET_HEARTBEAT_ACK_TIME:
            self.last_heartbeat_time = 0
            if CpDefs.LogVerboseInet:
                print "Heartbeat ack not received"
            self.enter_state(CpPrinterState.INITIALIZE)
            return

        result = CpInetResultCode()

        # Process the response
        try:
            print 'inet_idle: socket wait receive'

            # If no data is found in the socket an exception is thrown
            # This is the typical idle behavior of the socket
            reply = self.sock.recv(4096)

            # Connection has died unexpectedly on these conditions
            if(reply == 0 or reply == ""):
                self.inet_close()
                self.enter_state(CpPrinterState.INITIALIZE)
                return

            printer_commands = self.accumulate_commands(reply)

            for command in printer_commands:
                self.printerThread.enqueue_command(command)
                self.ack_queue.put(CpInetResponses.TOKEN_TCPACK)

        except socket.error, e:
            err = e.args[0]
            if err == 'timed out':
                result.ResultCode = CpInetResultCode.RESULT_SCKTIMEOUT
                print 'socket timeout waiting for job'
            else:
                result.ResultCode = CpInetResultCode.RESULT_SCKRECVERROR

            result.Data = e.args[0]

            self.log.logError('printer_idle jobs: 0')
            print 'inet_idle: jobs: 0 found.'

        # Check to see if there is a queued message
        if (self.commands.qsize() > 0):
            if(CpDefs.LogVerboseInet):
                print 'inet_idle record found'

            self.enter_state(CpPrinterState.SEND)
            return

        self.enter_state(CpPrinterState.HEARTBEAT)

    def inet_connect(self):
        try:
            self.sock.connect((self.remoteIp, self.port))
            # New Code for Timeout
            self.sock.settimeout(CpInetDefs.INET_TIMEOUT)
            # End New Code for Timeout

            if(CpDefs.LogVerboseInet):
                print 'inet_connect: successful'

            # TODO: automatically send up the PrinterId to check in with server
            self.enqueue_packet(CpDefs.PrinterId)

            self.enter_state(CpPrinterState.IDLE)
            self.watchdog_set_status(CpWatchdogStatus.Success)

            self.heartbeat_ack_pending = False #Don't expect heartbeat ack until heartbeat sent
            return True
        except:
            self.log.logError('inet_connect: failed')
            print 'inet_connect: failed'

        # If we get this far we received an error
        self.handle_inet_connect_error()

        return False

    def inet_sleep(self):
        # Check to see if there is a queued message
        if (self.commands.qsize() > 0):
            self.enter_state(CpPrinterState.INITIALIZE)
            return

        # Check to wake send ping once every 60s
        if(self.state_timedout() == True):
            self.enter_state(CpPrinterState.INITIALIZE)
            return

    def inet_send(self):

        # Allow the connected state to wait at least 30s before
        # going to idle. This will keep us from bouncing between
        # idle and connected states thus decreasing latency.
        # Reset the timer for each new message
        if(self.state_timedout() == True):
            self.enter_state(CpPrinterState.IDLE)
            return True

        if (self.commands.qsize() > 0):
            self.reset_state_timeout()

            if(CpDefs.LogVerboseInet):
                print 'Command found'

            packet = self.commands.get(True)

            result = self.inet_send_packet(packet)

            if(result.ResultCode == CpInetResultCode.RESULT_TCPACK or result.ResultCode == CpInetResultCode.RESULT_TCPNAK):
                print 'we received an ack'
                if(result.ResultCode == CpInetResultCode.RESULT_TCPNAK):
                    self.inet_stats.Naks += 1
                    if(CpDefs.LogVerboseInet):
                        print 'NAK: ', result.Data

                # Updated Statistics
                self.inet_stats.Sent += 1
                self.inet_stats.LastSent = time

                if(CpDefs.LogVerboseInet):
                    print 'SEND SUCCESSFUL'

                self.commands.task_done()
            else:
                print 'inet_send error: %s' % result.Data
                self.enqueue_packet(packet)
                self.handle_inet_send_error()

            return True
        else:
            # Otherwise we have no new messages and the current
            # state has not yet timed out so return True in order
            # to avoid the error handling
            return True

    def inet_waitnetworkinterface(self):
        # Allow the PON/POFF commands 120s before
        # attempting to initialize a new connection
        if(self.state_timedout() == True):
            self.enter_state(CpPrinterState.INITIALIZE)
            return False

        # TODO: REVIEW AND TEST BEFORE PROD
        found = self.query_interface(IfConfigVars.Interface)

        # Check to see if we have a network interface
        if (found):
            print 'inet_waitnetworkinterface: found successful'
            self.enter_state(CpPrinterState.INITIALIZE)
        else:
            print 'inet_waitnetworkinterface wait retry 1 sec.'
            time.sleep(1)

        return True

    def inet_receive(self):
        pass

    def inet_heartbeat(self):
        """
            Heartbeats are sent to the server to show that the
            connection remains open. A heartbeat isn't sent every
            time this state is entered, but rather once every
            INET_HEARTBEAT_TIME
        """
        elapsed_heartbeat = time.time() - self.last_heartbeat_time
        if elapsed_heartbeat > CpInetDefs.INET_HEARTBEAT_TIME:
            self.last_heartbeat_time = time.time()
            self.sock.send(CpDefs.InetTcpParms % CpInetDefs.INET_HEARTBEAT)
            self.heartbeat_ack_pending = True 
            if(CpDefs.LogVerboseInet):
                print "heartbeat sent"

        self.enter_state(CpPrinterState.IDLE)

    def inet_handler(self):
        if (CpDefs.WatchdogWaitNetworkInterface):
            # Start out waiting for network interface
            self.enter_state(CpPrinterState.WAITNETWORKINTERFACE)
        else:
            # Start out initializing (Use Case for testing without watchdog)
            self.enter_state(CpPrinterState.INITIALIZE)

        while not self.closing:
            if(self.STATEFUNC != 0):
                self.STATEFUNC()
            time.sleep(.0001)



    def shutdown_thread(self):
        print 'shutting down CpInet...'
        self.inet_close()
        self.__lock.acquire()
        self.closing = True
        self.__lock.release()

    def handle_inet_init_error(self):

        # ******** BEGIN ERROR HANDLING ********

        # If we get this far we received an error
        self.inetError.InitializeErrors += 1
        # Updated Statistics
        self.inet_stats.InitErrors += 1

        if (self.inetError.InitializeErrors > self.inetError.InitializeMax):
            print 'Max Initialize Errors'
            # Reset Error Counter
            self.inetError.InitializeErrors = 0
            # Handle Max Errors
            # TODO: TEST BEFORE PROD

            # Check to see if we need to update watchdog
            # if not we are in test mode and just want to remain in
            # inet_init indefinately
            if (CpDefs.WatchdogWaitNetworkInterface):
                self.watchdog_set_status(CpWatchdogStatus.Error)
                self.enter_state(CpPrinterState.WAITNETWORKINTERFACE)

            return False

        # Allow some settle time before trying again
        print 'Wait Retry Backoff %d sec.' % self.waitRetryBackoff[self.inetError.InitializeErrors]
        time.sleep(self.waitRetryBackoff[self.inetError.InitializeErrors])

        # ******** END ERROR HANDLING ********



    def handle_inet_connect_error(self):

        # ******** BEGIN ERROR HANDLING ********

        self.inetError.ConnectErrors += 1

        # Updated Statistics
        self.inet_stats.ConnectErrors += 1

        print 'CONNECT FAILED'

        if (self.inetError.ConnectErrors > self.inetError.ConnectMax):
            # Handle Max Errors
            self.inetError.ConnectErrors = 0
            self.enter_state(CpPrinterState.INITIALIZE)
            return False

        # Allow some settle time before trying again
        print 'Wait Retry Backoff %d sec.' % self.waitRetryBackoff[self.inetError.ConnectErrors]
        time.sleep(self.waitRetryBackoff[self.inetError.ConnectErrors])

        # ******** END ERROR HANDLING ********



    def handle_inet_send_error(self):

        # ******** BEGIN ERROR HANDLING ********

        self.inetError.SendErrors += 1

        # Updated Statistics
        self.inet_stats.SendErrors += 1

        print 'SEND FAILED'

        if (self.inetError.SendErrors > self.inetError.SendMax):
            # We have exceeded the maximum allowable attempts so
            # close and reinitialize the connection
            self.inetError.SendErrors = 0
            self.inet_close()
            self.enter_state(CpPrinterState.INITIALIZE)
            return False

        # Allow some settle time before trying again
        print 'Wait Retry Backoff %d sec.' % self.waitRetryBackoff[self.inetError.SendErrors]
        time.sleep(self.waitRetryBackoff[self.inetError.SendErrors])

        # ******** END ERROR HANDLING ********

    # inet_send_packet is explicitly called by inet_send
    def inet_send_packet(self, packet):
        #tcpPacket = "178\r"

        tcpPacket = CpInetDefs.INET_TCPPARAMS % (CpDefs.PrinterId)
        # New postData format

        result = CpInetResultCode()

        if(CpDefs.LogVerboseInet):
            print 'inet_send: (',self.remoteIp, ':', self.port, ')'
            print 'inet_send: ', tcpPacket

        # Send the HTTP request
        try:
            print 'sending (', tcpPacket, ')'
            byteCount = self.sock.send(tcpPacket)
        except socket.error, e:
            result.ResultCode = CpInetResultCode.RESULT_SCKSENDERROR
            result.Data = e.args[0]
            self.log.logError('inet_send: failed')
            print 'inet_send: failed'
            return result

        # Process the response
        try:
            reply = self.sock.recv(4096)

        except socket.error, e:
            err = e.args[0]
            if err == 'timed out':
                result.ResultCode = CpInetResultCode.RESULT_SCKTIMEOUT
                print 'socket timeout exception'
            else:
                result.ResultCode = CpInetResultCode.RESULT_SCKRECVERROR

            result.Data = e.args[0]

            self.log.logError('inet_send: failed')
            print 'inet_send: failed'
            return result

        result = self.inet_parse_result(reply)

        return result

    def accumulate_commands(self, message):
        """
            This returns a list of strings representing printer commands.
            An empty list signifies no printer commands and is expected,
            frequent behavior. All returned commands are complete
            and printable by a GX430t printer

            This accumulates partial commands from self.sock into
            complete commands. Acks are delimited by newlines. All
            printer commands begin with CpAscii.BEGIN and end with
            CpAscii.END. Anything within these delimitters is
            interpreted as a complete printer command and will be
            sent to the printer.

            Any partial commands are held in self.command_buffer
            until the next call to this wherein accumulation
            resumes.
        """
        commands = []
        for line in message.splitlines():
            if line == CpAscii.BEGIN:
                self.command_buffer = ""

            elif line == CpAscii.END:
                commands.append(self.command_buffer)
                self.command_buffer = ""

            elif line == CpInetResponses.TOKEN_TCPHBACK:
                self.heartbeat_ack_pending = False

            else:
                self.command_buffer += line

        return commands


    # inet_close is explicitly called by inet_sleep or shutdown_thread
    # inet_close is not used in conjunction with enter_state function

    def inet_close(self):
        # Check to see if we initialized the socket. If not calling shutdown and close
        # will throw an error so just return
        if(self.initialized == False):
            return

        try:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
            print 'inet_close: successful'
            return True
        except socket.error, e:
            err = e.args[0]
            logmsg = 'inet_close: failed: ', err
            self.log.logError(logmsg)
            print logmsg
        except socket.herror, he:
            herr = he.args[0]
            logmsg = 'inet_close: failed: ', herr
            self.log.logError(logmsg)
            print logmsg
        except socket.gaierror, gai:
            gerr = gai.args[0]
            logmsg = 'inet_close: failed: ', gerr
            self.log.logError(logmsg)
            print logmsg
        except socket.timeout, te:
            terr = te.args[0]
            logmsg = 'inet_close: failed: ', terr
            self.log.logError(logmsg)
            print logmsg

        return False



    def query_interface(self, interface):

        while True:
            print "Network try Count: ", InitVars.NumTry_Connection

            #wait for initialize
            time.sleep(InitVars.NumTry_Connection*InitVars.TimeDelayIncrement)

            if (interface == 'ppp0'):
                #check for connecton
                for line in open('/proc/net/dev', 'r'):
                    if interface in line:
                        #if check_for_transmission():
                        print "Active Network Found"
                        return True

            if (interface == 'eth0'):
                for line in open('/proc/net/dev', 'r'):
                    if interface in line:
                        return True

        if InitVars.NumTry_Connection > 3:
            print "Network not found, restarting service"
            #reboot_enable_modem()

        else:
            InitVars.NumTry_Connection += 1

    def enqueue_packet(self, packet):
        try:
            self.commands.put(packet, block=True, timeout=1)
        except:
            self.__lock.acquire()
            print "CpInet commands queue is full"
            self.__lock.release()

    def inet_parse_result(self, result):

        inet_result = CpInetResult()

        if(result.find(CpInetResponses.TOKEN_HTTPOK) > -1):
            inet_result.Data = result
            inet_result.ResultCode = CpInetResultCode.RESULT_OK
        elif(result.find(CpInetResponses.TOKEN_HTTPNORESPONSE) > -1):
            inet_result.Data = result
            inet_result.ResultCode = CpInetResultCode.RESULT_OK
        elif(result.find(CpInetResponses.TOKEN_HTTPERROR) > -1):
            inet_result.Data = result
            inet_result.ResultCode = CpInetResultCode.RESULT_ERROR
        elif(result.find(CpInetResponses.TOKEN_TCPACK) > -1):
            inet_result.Data = result
            inet_result.ResultCode = CpInetResultCode.RESULT_TCPACK
        elif(result.find(CpInetResponses.TOKEN_TCPNAK) > -1):
            inet_result.Data = result
            inet_result.ResultCode = CpInetResultCode.RESULT_TCPNAK
        else:
            inet_result.Data = result
            inet_result.ResultCode = CpInetResultCode.RESULT_UNKNOWN

        return inet_result


    def inet_test(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.remoteIp, self.port))
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
            return True
        except:
            self.log.logError('inet_test:')
            return False

    def watchdog_set_status(self, status):

        '''
            *** TODO: skip watchdog_set_status for now ***
        '''
        return

        try:
            with open(CpDefs.WatchdogFilePath, "r+b") as f: #mmap file
                mm = mmap.mmap(f.fileno(), 0)

            mm[1:2] = status
            mm.flush()
            mm.close()

        except IOError, e:
            #self.log.logError('watchdog_set_status: failed (%s)')  e.args[0]
            print 'watchdog_set_status: failed (%s)' % e.args[0]
        except EnvironmentError, ee:
            print 'watchdog_set_status: failed (%s)' % ee.args[0]
        except:
            print 'watchdog_set_status: failed'


def printerDataReceived(data):
    print 'Callback function printerDataReceived ', data
    pass

def inetDataReceived(data):
    #print 'Callback function inetDataReceived ', data
    pass

if __name__ == '__main__':

    printThread = CpPrinter(printerDataReceived)
    printThread.start()

    inetThread = CpPrinterService(printThread, inetDataReceived)
    inetThread.start()


    while True:
        input = raw_input(">> ")
                # Python 3 users
                # input = input(">> ")
        if input == 'exit' or input == 'EXIT':
            inetThread.shutdown_thread()

            while(inetThread.isAlive()):
                time.sleep(.005)

            printThread.shutdown_thread()

            while(printThread.isAlive()):
                time.sleep(.005)

            print "Exiting app"
            break
        elif input == '0':
            inetThread.enqueue_packet(CpDefs.PrinterId)
        elif input == '1':
            printThread.enqueue_command("hello world\r")
        else:
            pass


        time.sleep(.5)
