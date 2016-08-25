import sys
from datetime import datetime
from cpdefs import CpDefs
from cpdefs import CpLoggerConfig
import os

class CpLogger:
    def __init__(self):
        self.createLogDirectory(CpLoggerConfig.LOG_DIRECTORY)

    def error(self, message):
        self.log("ERROR", message)

    def warning(self, message):
        self.log("WARNING", message)

    def verbose(self, message):
        if CpLoggerConfig.LOG_VERBOSE:
            self.log("VERBOSE", message)

    def debug(self, message):
        if CpDefs.DEBUG:
            self.log("DEBUG", message)

    def log(self, levelString, message):
        logString = '[' + levelString + ': '
        logString += str(datetime.now()) + '] '
        logString += message + '\n'

        outFile = open(self.logFilePath(), "a")
        outFile.write(logString)
        outFile.close()

    def logFilePath(self):
        return CpDefs.LOG_DIRECTORY + datetime.now().strftime(self.FILE_FORMAT_STR)

    def createLogDirectory(self, dirPath):
        if not os.path.exists(os.path.dirname(dirPath)):
            os.makedirs(os.path.dirname(dirPath))

if __name__ == '__main__':

    logger.error("An Error")
    logger.warning("A Warning")
    logger.verbose("Verbose Logging")
