class HttpCodes:
    SUCCESS = 200
    SUCCESS_NO_CONTENT = 204

class CpDefs:
    PrinterBaud = 9600
    API_URL = "http://10.0.0.130/api/printer/getprintjob/"
    MESSAGE_CHECK_DELAY_S = 3
    DEBUG = True

class CpLoggerConfig:
    LOG_DIRECTORY = "../logs/"
    FILE_FORMAT_STR = "%H%M_%d_%m_%Y.log"
    LOG_VERBOSE = True
