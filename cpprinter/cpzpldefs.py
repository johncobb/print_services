class CpZplDefs:
    ZplQueryBatteryStatus = "~HB" # model dependent
    ZplPrinterSleep = "^ZZ" # model dependent
    ZplQueryHeadDiagnostic = "~HD"
    ZplHostRamStatus = "~HM"
    ZplHostIdentification = "~HI"
    ZplPrinterQueryStatus = "~HQES" # see table 13-14 p.225
    ZplHostQueryMaintenanceAlertSettings = "~HQMA"
    ZplHostQueryMaintenanceInformation = "~HQMI"
    ZplHostQueryOodometer = "~HQOD"
    ZplHostQueryPrintheadLifeHistory = "~HQPH"
    ZplHostQueryStatus = "~HS"
    ZplCancelAll = "~JA"
    ZplSetMediaSensorCalibration = "~JC"
    ZplPrintConfigurationLabel = "~WC"

    # First item in line for warnings in ~HQES return string
    ZplWarningIndicator = "WARNINGS:"

    # First item in line for errors in ~HQES return string
    ZplErrorIndicator = "ERRORS:"

    # First line of status response message
    ZplPrinterStatusIndicator = "PRINTER STATUS"
