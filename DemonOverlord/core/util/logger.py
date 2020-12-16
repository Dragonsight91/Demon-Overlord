import discord
import datetime


class TermFormat:
    HEADER = "\033[95m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    @staticmethod
    def format(fstring: str, *args, **kwargs) -> str:
        text = fstring + TermFormat.ENDC
        for formatting in args:
            text = f"{formatting}{text}"
        return text


class LogMessage:
    """Builds a message with optional Timestamp

    output: `[{prefix="MESSAGE"}] [TIME: {utctime}] {message}`

    message --- a string representing the message
    prefix  --- a string representing the message prefix "MESSAGE" by default
    time    --- a boolean value to turn timestamp on or off (timestamp is in utc time)
    color   --- a string representing the
    """

    def __init__(
        self,
        message: str,
        msg_type="MESSAGE",
        time=True,
        color=TermFormat.OKGREEN
    ):
        self.type = TermFormat.format(msg_type, color)
        self.time = datetime.datetime.utcnow() if time else None
        self.message = message

    def __str__(self):
        if self.time:
            return f"[{self.type}] [TIME: {self.time}] {self.message}"
        else:
            return f"[{self.type}] {self.message}"

class LogHeader(LogMessage):
    def __init__(self, message:str, header_char="=", header_dep=6, header_col=TermFormat.HEADER):
        super().__init__("message", time=False)
        self.message = message.upper()
        self.sides = header_dep*header_char
        self.color = header_col
    
    def __str__(self)->str:
        return f"[{self.type}] {TermFormat.format(f'{self.sides} {self.message} {self.sides}', self.color)}"


class LogCommand(LogMessage):
    def __init__(self, command):
        super().__init__("", msg_type="COMMAND")
        self.message = f"INCOMING COMMAND"
        self.message += f"\n\t{TermFormat.format('COMMAND', TermFormat.UNDERLINE)}: {str(command.command)}"
        self.message += f"\n\t{TermFormat.format('ACTION', TermFormat.UNDERLINE):7}: {command.action}"
        self.message += f"\n\t{TermFormat.format('PARAMS', TermFormat.UNDERLINE):7}: {str(command.params)}"
    
