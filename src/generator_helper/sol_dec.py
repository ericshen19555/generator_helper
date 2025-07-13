# -*- coding: utf-8 -*-
"""
sol_dec.py

Provides a decorator to capture standard input and output for a callable function,
typically representing a solution to a programming problem.
"""

import sys
from io import StringIO
from typing import Any, Callable, NoReturn
from functools import wraps


def override_io(solution: Callable) -> Callable:
    """
    Decorator to redirect sys.stdin and sys.stdout for a function call.

    This is useful for testing functions that read from stdin and write to stdout,
    allowing programmatic provision of input and capture of output.

    Args:
        solution: The function (callable) to be decorated. It's expected to read
                  from stdin and write to stdout.

    Returns:
        A wrapper function that, when called, executes the original function
        with redirected I/O. The wrapper accepts an optional 'testcase' keyword
        argument. It returns a tuple containing the original function's return
        value and the captured stdout content, or raises any exception encountered
        during the function's execution.

    Raises:
        TypeError: If 'solution' is not callable, or if 'testcase' is provided
                   but is not a string.
        Exception: Any exception raised by the decorated 'solution' function
                   during its execution will be propagated after restoring stdio.

    Example:
        @override_io
        def my_solver():
            data = input()
            print(f"Received: {data}")
            return 42

        result, output = my_solver(testcase="hello")
        # result will be 42
        # output will be "Received: hello\n"
    """
    if not isinstance(solution, Callable):
        raise TypeError("The 'solution' argument must be callable.")

    @wraps(solution)
    def inner(*args, testcase: str | None = None, **kwargs) -> tuple[Any, str] | NoReturn:
        """
        Inner wrapper function that handles the I/O redirection.

        Args:
            *args: Positional arguments to pass to the original solution.
            testcase: An optional string to be used as sys.stdin content.
            **kwargs: Keyword arguments to pass to the original solution.

        Returns:
            A tuple: (return value of the solution, captured stdout string).

        Raises:
            TypeError: If 'testcase' is not None and not a string.
            Exception: Propagates exceptions from the decorated function.
        """
        if testcase is not None and not isinstance(testcase, str):
            raise TypeError("The 'testcase' argument must be a string or None.")

        try:
            # Redirect stdin if testcase is provided
            if testcase is not None:
                sys.stdin = StringIO(testcase)
            # Redirect stdout to capture output
            sys.stdout = StringIO()

            # Execute the original function
            ret = solution(*args, **kwargs)
            # Get the captured output
            output = sys.stdout.getvalue()

        except Exception as e:
            # If any exception occurs, re-raise it after cleanup
            raise e
        finally:
            # Always restore original stdin and stdout
            sys.stdin = sys.__stdin__
            sys.stdout = sys.__stdout__

        # Return the original function's return value and the captured output
        return ret, output

    return inner
