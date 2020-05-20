

class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class CommandLineError(Error):
    """Exception raised for incorrect command line

    Attributes:
        expression -- input expression in which the error occurred
        message -- explanation of the error
    """

    def __init__(self, expression, message):
        self.expression = expression
        self.message = message