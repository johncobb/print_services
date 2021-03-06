import sys
from datetime import datetime
from cpdefs import CpDefs
import os

class CpLoggerConfig:
    LOG_DIRECTORY = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../logs/')
    FILE_FORMAT_STR = '%d_%m_%Y.log'
    LOG_KEEP_DAYS = 7 #Number of days log files are kept before being deleted
    LOG_VERBOSE = False

class CpLogger:
    def __init__(self):
        self.createLogDirectory(CpLoggerConfig.LOG_DIRECTORY)

    def error(self, message):
        self.log(self.buildLogMessage('ERROR', message))

    def warning(self, message):
        self.log(self.buildLogMessage('WARNING', message))

    def verbose(self, message):
        if CpLoggerConfig.LOG_VERBOSE:
            self.log(self.buildLogMessage('VERBOSE', message))

    def status(self, message):
        self.log(self.buildLogMessage('STATUS', message))

    def log(self, logString):
        print(logString),

        with open(self.logFilePath(), 'a') as outFile:
            outFile.write(logString)

    def buildLogMessage(self, levelString, message):
        return '[' + levelString + ': ' + str(datetime.now()) + '] ' + message + '\n'

    def logFilePath(self):
        return CpLoggerConfig.LOG_DIRECTORY + \
               datetime.now().strftime(CpLoggerConfig.FILE_FORMAT_STR)

    def createLogDirectory(self, dirPath):
        if not os.path.exists(os.path.dirname(dirPath)):
            os.makedirs(os.path.dirname(dirPath))

    def purgeOldLogs(self):
        """ Log files older than CpLoggerConfig.LOG_KEEP_DAYS days are
        removed when this function is called.
        """
        try:
            from os import listdir
            from os.path import isfile, join
            logPath = CpLoggerConfig.LOG_DIRECTORY

            # get elements in log directory
            logFiles = [f for f in listdir(logPath)
                        if isfile(join(logPath, f))]

            # get timestamps of each file
            fileTimes = [(f, self.logFileToDatetime(f))
                         for f in logFiles
                         if self.logFileToDatetime(f) is not None]

            now = datetime.now()

            # Get files older than CpLoggerConfig.LOG_KEEP_DAYS
            filesToRemove = [f for (f, t) in fileTimes
                             if (now - t).days > CpLoggerConfig.LOG_KEEP_DAYS]

            map(lambda f: os.remove(join(CpLoggerConfig.LOG_DIRECTORY, f)),
                filesToRemove)
        except OSError:
            self.warning('Failed to purge old log files.')

    def logFileToDatetime(self, fileName):
        try:
            return datetime.strptime(fileName, CpLoggerConfig.FILE_FORMAT_STR)
        except:
            self.warning("File in LOG_DIRECTORY didn't match format. Found: " + fileName)
        return None
        

if __name__ == '__main__':
    logger = CpLogger()
    logger.error("An Error")
    logger.warning("A Warning")
    logger.verbose("Verbose Logging")
