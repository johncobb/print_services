import unittest
import cpprinter.cpresponseparser as CP

class TestCpResponseParser(unittest.TestCase):

    def setUp(self):
        self.parser = CP.CpResponseParser()

    def test_parse_message_no_errors(self):
        self.assertEqual(self.parser.parse_message('ERRORS: 0 00000000 00000000'), [])

    def test_parse_message_one_error(self):
        self.assertEqual(self.parser.parse_message('ERRORS: 1 00000000 00000001'), ['Media Out'])

    def test_parse_message_two_errors(self):
        self.assertEqual(self.parser.parse_message('ERRORS: 1 00000000 00000014'), ['Printhead Over Temperature',
                                                                                    'Head Open'])
    def test_parse_message_three_errors(self):
        self.assertEqual(self.parser.parse_message('ERRORS: 1 00000000 00000188'), ['Invalid Firmware Config',
                                                                                    'Printhead Detection Error',
                                                                                    'Cutter Fault'])
    def test_parse_message_no_warnings(self):
        self.assertEqual(self.parser.parse_message('WARNINGS: 0 00000000 00000000'), [])

    def test_parse_message_one_warning(self):
        self.assertEqual(self.parser.parse_message('WARNINGS: 1 00000000 00000002'), ['Clean Printhead'])

    def test_parse_printer_status_no_messages(self):
        message = '\n\nPRINTER STATUS\n   ERRORS: 0 00000000 00000000\n WARNINGS: 0 000000000 00000000\n'
        self.parser.parse_printer_status(message)
        self.assertEqual(self.parser.errors, [])
        self.assertEqual(self.parser.warnings, [])

    def test_parse_printer_status_errors(self):
        message = '\n\nPRINTER STATUS\n   ERRORS: 1 00000000 00000182\n WARNINGS: 0 000000000 00000000\n'

        self.parser.parse_printer_status(message)
        self.assertEqual(self.parser.errors, ['Invalid Firmware Config',
                                              'Printhead Detection Error',
                                              'Ribbon Out'])
        self.assertEqual(self.parser.warnings, [])

    def test_parse_printer_status_warnings(self):
        message = '\n\nPRINTER STATUS\n   ERRORS: 0 00000000 00000000\n WARNINGS: 1 000000000 00000004\n'

        self.parser.parse_printer_status(message)

        self.assertEqual(self.parser.errors, [])
        self.assertEqual(self.parser.warnings, ['Replace Printhead'])

    def test_parse_printer_status_both(self):
        message = '\n\nPRINTER STATUS\n   ERRORS: 1 00000000 00000012\n WARNINGS: 1 000000000 00000001\n'

        self.parser.parse_printer_status(message)

        self.assertEqual(self.parser.errors, ['Printhead Over Temperature', 'Ribbon Out'])
        self.assertEqual(self.parser.warnings, ['Need to Calibrate Media'])


