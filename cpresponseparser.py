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

        for line in response.splitLines():
            if "ERROR" in line:
                errors = line

            elif "WARNING" in line:
                warnings = line

        print "errors: ", errors
        print "warnings: ", warnings

        # self.current_errors = parse_errors(errors)
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
        error_flags = errors[2]
        error_nibble_one = {1:"Media Out",
                            2:"Ribbon Out",
                            4:"Head Open",
                            8:"Cutter Fault"}

    def parse_warnings(self, warnings):
        pass
