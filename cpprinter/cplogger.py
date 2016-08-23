import sys
from datetime import datetime
from cpdefs import CpDefs
import os


class CpLogger:

    def __init__(self):
        self.LOG_DIR = "../logs/"
        self.FILE_FORMAT_STR = "%H%M_%d_%m_%Y.log"
        self.createLogDirectory(self.LOG_DIR)

    def error(self, message):
        self.log("ERROR", message)

    def warning(self, message):
        self.log("WARNING", message)

    def verbose(self, message):
        if CpDefs.LogVerbosePrinter:
            self.log("VERBOSE", message)

    def log(self, levelString, message):
        logString = '[' + levelString + ': '
        logString += str(datetime.now()) + '] '
        logString += message + '\n'

        print(message)
        outFile = open(self.logFilePath(), "a")
        outFile.write(logString)
        outFile.close()

    def logFilePath(self):
        return self.LOG_DIR + datetime.now().strftime(self.FILE_FORMAT_STR)

    def createLogDirectory(self, dirPath):
        if not os.path.exists(os.path.dirname(dirPath)):
            os.makedirs(os.path.dirname(dirPath))

logger = CpLogger()

if __name__ == '__main__':

    logger.logError("An Error")
    logger.logWarning("A Warning")
    logger.logVerbose("Verbose Logging")
