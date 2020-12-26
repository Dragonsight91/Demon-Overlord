import datetime


class LogFormat:
    """An enum that holds escape sequences for use in terminal environments"""

    HEADER = "\033[95m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    @staticmethod
    def format(fstring: str, *args) -> str:
        """a static methd to allow easy application of terminal formats"""
        text = fstring + LogFormat.ENDC
        for formatting in args:
            text = f"{formatting}{text}"
        return text


class LogType:
    """An enum that holds pre-formatted message types"""

    MESSAGE = f"{LogFormat.format('MESSAGE', LogFormat.OKGREEN)}"
    COMMAND = f"{LogFormat.format('COMMAND', LogFormat.OKGREEN)}"
    ERROR = f"{LogFormat.format('ERROR', LogFormat.FAIL)}"
    WARNING = f"{LogFormat.format('WARNING', LogFormat.WARNING)}"


class LogMessage:
    """Builds a message with optional Timestamp

    - `message` - a string representing the message
    - `msg_type` - a string representing the message prefix, see LogType
    - `time` - a boolean value to turn timestamp on or off (timestamp is in utc time)
    - `color` - a string representing the Terminal escape sequence to format the message

    implemented builtins:
    - __str__

    """

    def __init__(
        self,
        message: str,
        msg_type: LogType = LogType.MESSAGE,
        time: bool = True,
        color: LogFormat = None,
    ):
        self.type = msg_type if not color else LogFormat.format(msg_type, color)
        self.time = datetime.datetime.utcnow() if time else None
        self.message = message

    def __str__(self):
        """
        there are two outputs, based on whether time is enabled or not:

        output: `[{prefix="MESSAGE"}] [TIME: {utctime}] {message}`
        output: `[{prefix="MESSAGE"}] {message}`
        """
        if self.time:
            return f"[{self.type}] [TIME: {self.time}] {self.message}"
        else:
            return f"[{self.type}] {self.message}"


class LogHeader(LogMessage):
    """This creates a log header. default marker is "=" and default depth is 6"""

    def __init__(
        self, message: str, header_char="=", header_dep=6, header_col=LogFormat.HEADER
    ):
        super().__init__("MESSAGE", time=False)
        self.message = message.upper()
        self.sides = header_dep * header_char
        self.color = header_col

    def __str__(self) -> str:
        return f"[{self.type}] {LogFormat.format(f'{self.sides} {self.message} {self.sides}', self.color)}"


class LogCommand(LogMessage):
    """This creates a log messsage specifically for a command"""

    def __init__(self, command, time=False):
        super().__init__("", msg_type=LogType.COMMAND, time=time)
        self.message = f"INCOMING COMMAND"
        self.message += f"\n{LogFormat.format('COMMAND', LogFormat.UNDERLINE).rjust(len(self.type)+9+(len(str(self.time))+9 if self.time else 0))} : {str(command.command)}"
        self.message += f"\n{LogFormat.format('ACTION', LogFormat.UNDERLINE).rjust(len(self.type)+9+(len(str(self.time))+9 if self.time else 0)): <7} : {command.action}"
        self.message += f"\n{LogFormat.format('PARAMS', LogFormat.UNDERLINE).rjust(len(self.type)+9+(len(str(self.time))+9 if self.time else 0)): <7} : {str(command.params)}"

