import time
from datetime import datetime

class CpInetStats:
    InitErrors = 0
    ConnectErrors = 0
    Sent = 0
    SendErrors = 0
    Naks = 0
    LastSent = time.gmtime(0) # Epoch

class CpRfStats:
    RfErrors = 0
    RfReceived = 0
