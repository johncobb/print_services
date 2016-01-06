class ResponseCodes:
    """
        NIBBLES is a dict mapping the "Nibble Number" as
        defined in the ZPL documentation Page 225 to a 
        dictionary mapping nibble value to it's error
        condition.
    """

    @classmethod
    def get_error(cls, nibble, value):
        return cls.ERRORS[nibble][value]

    @classmethod
    def get_warning(cls, nibble, value):
        return cls.WARNINGS[nibble][value]

    # Map of Nibble # => {Nibble value => Error String}
    ERRORS = {3:{0:"",
                 1:"Invalid Firmware Config",
                 2:"Printhead Thermistor Open"},

              2:{0:"",
                 1:"Printhead Over Temperature",
                 2:"Motor Over Temperature",
                 4:"Bad Printhead Element",
                 8:"Printhead Detection Error"},

              1:{0:"",
                 1:"Media Out",
                 2:"Ribbon Out",
                 4:"Head Open",
                 8:"Cutter Fault"}
             }

    # Map of Nibble # => {Nibble value => Warning String}
    WARNINGS = {1:{0:"",
                   4:"Replace Printhead",
                   2:"Clean Printhead",
                   1:"Need to Calibrate Media"}
               }

class CpResponseParser():
    def __init__(self):
        self.current_errors = []
        self.current_warnings = []

    def parse_printer_status(self, response):
        """
            This function takes the printer's response to the
            ~HQES command and determines which errors/warnings
            have been encountered.

            The response takes the form:

            >
            >
            > PRINTER STATUS
            >    ERRORS: 0 00000000 00000000
            >    WARNINGS: 0 00000000 00000000
            >

            The meaning of the hex digit strings are defined
            in the ZPL documentation
        """

        for line in response.splitlines():
            if "ERROR" in line:
                errors = line

            elif "WARNING" in line:
                warnings = line

        self.current_errors = self.parse_errors(errors)
        print self.current_errors
        # self.current_warnings = parse_warnings(warnings)

    def parse_errors(self, error_str):
        """
            errors is the "ERRORS:" string from the printer
            status response. It takes the form:

            > ERRORS: 0 00000000 00000000

            Each character represents a hexadecimal digit.
            The meaning of each character is defined in the
            ZPL documentation
        """

        #"ERRORS:" is useless, ignore it
        errors = (error_str.split())[1:]

        if errors[0] is "0":
            return []

        error_list = []
        error_nibbles = errors[2]
        for idx in range(len(error_nibbles)):
            nibble_number = 8 - idx
            nibble = error_nibbles[idx]
            if nibble is "0":
                continue
            error_list.append(ResponseCodes.get_error(nibble_number, int(nibble)))

        return error_list

    def parse_warnings(self, warnings):
        pass
