import sys
from datetime import datetime

class CpLog:

    LOG_PATH = "errlog.dat"
    STDOUT_PATH = "stdout.dat"
    
    def logError(self, error):
        
        log = "%s\t%s\n" % (datetime.now(), error)
        
        f = open(self.LOG_PATH, "a")
        f.write(log)
        f.close()
        
        pass
    
    def logStdOut(self):
        f = open(self.STDOUT_PATH, 'a')
        sys.stdout = f
        print "test"
        
        
if __name__ == '__main__':
    
    log = CpLog()
    log.logError("One")
    log.logError("Two")
    log.logError("Three")