
class CpEncoding:
    CpRaw = 0
    CpJson = 1
    CpJsonCustom = 2
    CpJsonCustomBase64 = 3
    CpTcpAscii = 4

class CpDefs:
    PrinterId = "0000"
    RunAsService = False
    PrinterQueryStatus = False
    PrinterQueueTimeout = 5
    PrinterPort = "/dev/ttyUSB0"
    # PrinterPort = "/dev/tty.usbserial-FTUTL4CN"
    PrinterBaud = 9600
    InetHost = "appserver02.cphandheld.com"
    # InetHost = "96.27.198.215"
    InetPort = 1665
    InetTcpParms = "%s\r"
    InetTimeout = 1
    WatchdogFilePath = "/home/cphappliance/cph/echobase_intel_nuc/watchdog/info.txt"
    WatchdogWaitNetworkInterface = False
    Encoding = CpEncoding.CpTcpAscii
    HexifiyEncoding = False # Converts all fields to hex equivalent
    Debug = True
    LogVerbose = True
    LogToStdOut = True
    LogPacketLevel = False
    LogVerbosePrinter = True
    LogVerboseInet = True
    LogEncodedMessage = False
    
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

