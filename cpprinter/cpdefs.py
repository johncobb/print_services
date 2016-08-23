class HttpCodes:
    SUCCESS = 200
    SUCCESS_NO_CONTENT = 204

class CpDefs:
    RunAsService = True
    PrinterQueryStatus = False
    PrinterQueueTimeout = 5
    # PrinterPorts = ["/dev/ttyUSB0"]
    PrinterBaud = 9600
    InetHost = "korevpn02.cphandheld.com"
    API_URL = "http://10.0.0.130/api/printer/getprintjob/"
    # InetHost = "96.27.198.215"
    InetPort = 1665
    InetTcpParms = "%s\r"
    InetTimeout = 1
    WatchdogFilePath = "/home/cphappliance/cph/echobase_intel_nuc/watchdog/info.txt"
    WatchdogWaitNetworkInterface = False
    Debug = True
    LogVerbose = True
    LogToStdOut = True
    LogPacketLevel = False
    LogVerbosePrinter = True
    LogVerboseInet = True
    LogEncodedMessage = False
    MESSAGE_CHECK_DELAY_S = 3
    
class CpSystemState:
    INITIALIZE = 0
    IDLE = 1
    CONNECT = 2
    CLOSE = 3
    SLEEP = 4
    SEND = 5
    WAITNETWORKINTERFACE = 6
    

class CpAscii:
    STX = "\x02"
    ETX = "\x03"
    ACK = "\x06"
    NAK = "\x21"
    BEGIN = "**CPbegin**"
    END   = "**CPend**"

