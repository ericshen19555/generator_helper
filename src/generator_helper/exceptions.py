from random import Random

from func_timeout import FunctionTimedOut


class TestcaseInvalidError(Exception): pass


class GeneratorRuntimeError(Exception):
    def __init__(self, message: str, rnd: Random):
        super().__init__(message)
        self.rnd = rnd


TimeLimitExceededError = FunctionTimedOut
TimeLimitExceededError.__repr__ = lambda self: "TimeLimitExceededError('TLE')"
TimeLimitExceededError.__str__ = lambda self: "TLE"
TimeLimitExceededError.__module__ = __name__
TimeLimitExceededError.__name__ = "TimeLimitExceededError"
TimeLimitExceededError.__qualname__ = "TimeLimitExceededError"

TLE = TimeLimitExceededError
