import sys
from datetime import datetime
from cpdefs import CpDefs
from cpdefs import CpLoggerConfig
import os

class CpLogger:
    def __init__(self):
        self.createLogDirectory(CpLoggerConfig.LOG_DIRECTORY)

    def error(self, message):
        self.log(self.buildLogMessage("ERROR", message))

    def warning(self, message):
        self.log(self.buildLogMessage("WARNING", message))

    def verbose(self, message):
        if CpLoggerConfig.LOG_VERBOSE:
            self.log(self.buildLogMessage("VERBOSE", message))

    def debug(self, message):
        if CpDefs.DEBUG:
            self.log(self.buildLogMessage("DEBUG", message))

    def log(self, logString):
        # logString = '[' + levelString + ': '
        # logString += str(datetime.now()) + '] '
        # logString += message + '\n'
        print logString

        outFile = open(self.logFilePath(), "a")
        outFile.write(logString)
        outFile.close()

    def buildLogMessage(levelString, message):
        return '[' + levelString + ': ' + str(datetime.now()) + '] ' + message + '\n'

    def logFilePath(self):
        return CpLoggerConfig.LOG_DIRECTORY + \
               datetime.now().strftime(CpLoggerConfig.FILE_FORMAT_STR)

    def createLogDirectory(self, dirPath):
        if not os.path.exists(os.path.dirname(dirPath)):
            os.makedirs(os.path.dirname(dirPath))

if __name__ == '__main__':

    logger.error("An Error")
    logger.warning("A Warning")
    logger.verbose("Verbose Logging")
