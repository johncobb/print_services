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
    # Defined on Table 13 Pg 225 of ZPL Documentation
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
    # Defined on Table 14 Pg 226 of ZPL Documentation
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
        self.current_warnings = self.parse_warnings(warnings)

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

        # First bit indicates existing errors on '1' or none on '0'
        if errors[0] is "0":
            return []

        error_list = []

        # The first set of nibbles never holds a value, so we only consider
        # the second
        error_nibbles = errors[2]
        for idx in range(len(error_nibbles)):
            # These nibbles are numbered backwards from typical indexing
            # so we have to adjust the index
            nibble_number = 8 - idx
            nibble = error_nibbles[idx]

            # Value of '0' indicates no error
            if nibble is '0':
                continue
            error_list.append(ResponseCodes.get_error(nibble_number, int(nibble)))

        return error_list

    def parse_warnings(self, warning_str):
        """
            errors is the "ERRORS:" string from the printer
            status response. It takes the form:

            > WARNINGS: 0 00000000 00000000

            Each character in the latter 3 strings represents a 
            hexadecimal digit. The meaning of each character is
            defined in the ZPL documentation
        """

        #"WARNINGS:" is useless, ignore it
        warnings = (warning_str.split())[1:]

        # First bit indicates existing warnings on '1' or none on '0'
        if warnings[0] is '0':
            return []

        warning_list = []
        # The first set of nibbles never holds a value, so we only consider
        # the second
        warning_nibbles = warnings[2]
        for idx in range(len(warning_nibbles)):
            # These nibbles are numbered backwards from typical indexing
            # so we have to adjust the index
            nibble_number = 8 - idx
            nibble = warning_nibbles[idx]

            # Value of '0' indicates no error
            if nibble is "0":
                continue
            warning_list.append(RespnoseCodes.get_warning(nibble_number, int(nibble)))

        return warning_list
