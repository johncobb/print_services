from cpzpldefs import CpZplDefs as ZPL

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
        self.errors = []
        self.warnings = []

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
        lines = response.splitlines()

        #There should be exactly one line containing each of these
        errors = filter(lambda line: ZPL.ZplErrorIndicator in line, lines)
        warnings = filter(lambda line: ZPL.ZplWarningIndicator in line, lines)

        if len(errors) is not 1 or len(warnings) is not 1:
            print 'Invalid response string.'
            return

        self.errors = self.parse_message(errors[0], 'error')
        self.warnings = self.parse_message(warnings[0], 'warning')
        print "Errors: ", self.errors
        print "Warnings: ", self.warnings
        # self.errors = self.parse_errors(errors[0])
        # self.warnings = self.parse_warnings(warnings[0])

    def parse_message(self, message_str, message_name):
        #"ERRORS:" is useless, ignore it
        words = (message_str.split())[1:]

        # First bit indicates existing errors on '1' or none on '0'
        if words[0] is "0":
            return []

        response_list = []

        # The first set of nibbles never holds a value, so we only consider
        # the second
        response_nibbles = words[2]
        for idx in range(len(response_nibbles)):
            # These nibbles are numbered backwards from typical indexing
            # so we have to adjust the index
            nibble_number = 8 - idx
            nibble = response_nibbles[idx]

            # Value of '0' indicates no error
            if nibble is '0':
                continue

            # This returns a function constructed from the passed in
            # method name. The strings are resolved as a member of the 
            # class ResponseCodes. In this case it doesn't do much except
            # make the code worse. But it's really cool.
            method = getattr(ResponseCodes, 'get_' + message_name)
            response_list.append(method(nibble_number, int(nibble)))
            # response_list.append(ResponseCodes.get_error(nibble_number, int(nibble)))

        return response_list


