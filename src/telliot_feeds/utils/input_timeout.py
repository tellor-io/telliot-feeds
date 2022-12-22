""""
Original code taken from unmaintained package:
https://github.com/johejo/inputimeout/blob/master/inputimeout/inputimeout.py
"""
import sys
from typing import Any

DEFAULT_TIMEOUT = 600.0  # 10 mins
# DEFAULT_TIMEOUT = 10.0  # 10 secs
INTERVAL = 0.05

SP = " "
CR = "\r"
LF = "\n"
CRLF = CR + LF


class TimeoutOccurred(Exception):
    pass


def echo(string: str) -> None:
    sys.stdout.write(string)
    sys.stdout.flush()


def posix_inputimeout(prompt: str = "", timeout: float = DEFAULT_TIMEOUT) -> Any:
    echo(prompt)
    sel = selectors.DefaultSelector()
    sel.register(sys.stdin, selectors.EVENT_READ)
    events = sel.select(timeout)

    if events:
        key, _ = events[0]
        return key.fileobj.readline().rstrip(LF)  # type: ignore
    else:
        echo(LF)
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
        raise TimeoutOccurred


def win_inputimeout(prompt: str = "", timeout: float = DEFAULT_TIMEOUT) -> str:
    echo(prompt)
    begin = time.monotonic()
    end = begin + timeout
    line = ""

    while time.monotonic() < end:
        if msvcrt.kbhit():  # type: ignore
            c = msvcrt.getwche()  # type: ignore
            if c in (CR, LF):
                echo(CRLF)
                return line
            if c == "\003":
                raise KeyboardInterrupt
            if c == "\b":
                line = line[:-1]
                cover = SP * len(prompt + line + SP)
                echo("".join([CR, cover, CR, prompt, line]))
            else:
                line += c
        time.sleep(INTERVAL)

    echo(CRLF)
    raise TimeoutOccurred


try:
    import msvcrt

except ImportError:
    import selectors
    import termios

    input_timeout_func = posix_inputimeout

else:
    import time

    input_timeout_func = win_inputimeout


class InputTimeout:
    def __call__(self, prompt: str = "", timeout: float = DEFAULT_TIMEOUT) -> Any:
        return input_timeout_func(prompt, timeout)


input_timeout = InputTimeout()


if __name__ == "__main__":
    try:
        user_input = input_timeout("Type something: ", 5.0)
        print(f"You typed: {user_input}")
    except TimeoutOccurred:
        print("Timeout occurred")
