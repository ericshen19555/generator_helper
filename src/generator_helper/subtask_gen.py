# -*- coding: utf-8 -*-
"""
subtask_gen.py

Core logic for generating test cases using a generator function and verifying
them against expected outcomes using a verifier function. Includes features
like reproducible randomness and custom assertions for test case validation.
"""

import traceback
from random import Random
from typing import Callable, Any, NoReturn, Optional, Protocol

from .exceptions import TestcaseInvalidError, GeneratorRuntimeError


class SupportsBool(Protocol):
    def __bool__(self) -> bool: ...


class ReproducibleRandom(Random):
    """
    A subclass of random.Random that stores its initial seed and state.

    This allows resetting the generator to its exact starting point, although
    the current 'generator_runner' implementation creates a new instance for
    each attempt, making 'back_to_initial' potentially unused in that context.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initializes the random number generator.

        Args:
            seed: An optional integer seed for the random number generator.
                  If None, the generator is initialized using default sources
                  of randomness.
        """
        super().__init__(seed)
        self._seed = seed
        self.initial_state = self.getstate()  # Store the initial state

    def back_to_initial(self):
        """Resets the random generator state to its initial state."""
        self.setstate(self.initial_state)


def assert_testcase(statement: SupportsBool, msg: Any = "", *, from_: Optional[Exception] = None) -> None | NoReturn:
    """
    Custom assertion function for validating test cases during generation or verification.

    If the statement is False, raises a TestcaseInvalidError, including a
    custom message and context about where the assertion failed.

    Args:
        statement: The boolean condition to assert.
        msg: An optional message to include in the error if assertion fails.
        from_: An optional original exception to chain with the TestcaseInvalidError.

    Raises:
        TestcaseInvalidError: If 'statement' is False.
    """
    if statement:
        # Assertion passed, do nothing.
        # print(f"{msg} -> True")  # Debugging print, commented out
        return

    # Assertion failed, gather context
    stack = traceback.extract_stack()
    # Get the frame where assert_testcase was called from
    caller_frame = stack[-2]
    # Get the source code line of the assertion call
    caller_statement = caller_frame.line.strip()

    error_message = f"{msg} <- Assertion failed at: '{caller_statement}'"

    if from_ is None:
        raise TestcaseInvalidError(error_message)
    else:
        # Chain the original exception if provided
        raise TestcaseInvalidError(error_message) from from_


def generator_runner(generator: Callable[[int, Random], str],
                     verifier: Callable[[int, str], str | NoReturn],
                     retry_limit: int = -1) -> Callable[[int], tuple[str, str] | NoReturn]:
    """
    Creates a runner function that generates and verifies a test case.

    The runner repeatedly calls the generator and verifier until a test case
    is produced that successfully passes the verifier without raising
    TestcaseInvalidError, or until the retry limit is reached.

    Args:
        generator: A function that takes a test case index (int) and a
                   ReproducibleRandom instance, and returns a string
                   representing the generated test case input.
        verifier: A function that takes a test case index (int) and the
                  generated test case string. It should run various solutions
                  against the test case. If the test case correctly distinguishes
                  the solutions as expected, it should return the correct answer
                  string (typically from an AC solution). If the test case is
                  invalid (e.g., doesn't distinguish solutions correctly), it
                  should raise TestcaseInvalidError.
        retry_limit: The maximum number of times to retry generation/verification
                     if TestcaseInvalidError is raised. A value of -1 means
                     retry indefinitely (original behavior). Defaults to -1.

    Returns:
        A runner function. This runner function takes a test case index (int)
        and returns a tuple (testcase_string, answer_string) if successful.

    Raises:
        GeneratorRuntimeError: Wraps unexpected exceptions from the generator
                               or verifier, including the initial random state
                               for reproducibility.
        RuntimeError: If a valid test case cannot be generated within the
                      specified retry_limit.
    """

    def runner(testcase_index: int) -> tuple[str, str] | NoReturn:
        """
        The actual runner function that generates and verifies a single test case,
        respecting the retry limit.

        Args:
            testcase_index: The index of the test case to generate.

        Returns:
            A tuple containing the generated test case string and the verified
            answer string if successful within the retry limit.

        Raises:
            GeneratorRuntimeError: If an unexpected error occurs during generation
                                   or verification.
            RuntimeError: If a valid test case could not be generated after
                          'retry_limit' attempts.
            TestcaseInvalidError: Can be raised directly by the verifier if needed,
                                  though typically caught and retried by this runner.
        """
        retry_count = 0
        # Loop until retry_limit is reached (if limit is >= 0)
        # If retry_limit is -1, the condition retry_count != -1 is always true,
        # effectively creating an infinite loop until success or other error.
        while retry_count != retry_limit:
            # Create a new reproducible random generator for each attempt
            rnd = ReproducibleRandom()
            try:
                # 1. Generate a test case
                testcase = generator(testcase_index, rnd)
                # print(repr(testcase))  # Debugging print

                # 2. Verify the test case using the provided verifier
                # The verifier should raise TestcaseInvalidError if the case is bad
                answer = verifier(testcase_index, testcase)

                # If verification succeeds (no TestcaseInvalidError), return
                return testcase, answer

            except TestcaseInvalidError as e:
                # Test case was deemed invalid by the verifier.
                # Log the error and prepare for the next attempt (if within limit).
                # TODO: Consider using logging instead of print for better control
                print(f"[#{testcase_index}] Attempt {retry_count + 1}:\n\tTestcaseInvalidError (retrying):\n\t{e}")
                # Increment retry count and loop continues

            except Exception as e:
                # An unexpected, non-TestcaseInvalidError occurred in the generator or verifier.
                print(f"Unexpected Error Class: {e.__class__}")
                # Wrap the exception with context (initial random state) and re-raise immediately.
                raise GeneratorRuntimeError(
                    f"Unexpected error during generation/verification on attempt {retry_count + 1}. "
                    f"Random generator initial state = {rnd.initial_state}", rnd) from e

            # Increment the retry counter only after a TestcaseInvalidError occurred
            retry_count += 1
            # Loop continues to retry generation/verification if limit not reached

        # If the loop finishes, it means the retry_limit was reached
        raise RuntimeError(f"Failed to generate a valid test case for index {testcase_index} "
                           f"after {retry_limit} attempts.")

    return runner


# Example usage block
if __name__ == '__main__':
    # Import necessary components for the example
    from sol_dec import override_io
    # Assume verifier module defines AC, WA, TLE, verifier_factory
    from verifier import AC, WA, TLE, verifier_factory

    # Define some example solutions decorated with override_io
    @override_io
    def ac_sol():
        """Correct solution: reads two numbers, prints the first."""
        n, r = map(int, input().split())
        print(n)
        return n  # Example return value (optional)


    @override_io
    def wa_sol():
        """Wrong Answer solution: reads two numbers, prints the second."""
        n, r = map(int, input().split())
        print(r)
        return r


    @override_io
    def tle_sol():
        """Time Limit Exceeded solution: infinite loop."""
        while True:
            pass


    @override_io
    def re_sol():
        """Runtime Error solution: division by zero."""
        # This specific RE might be hard to trigger reliably via input only
        # For demonstration purposes:
        # n, r = map(int, input().split())
        # print(n // r) # Could cause ZeroDivisionError if r is 0
        print(0 / 0)  # Guarantees ZeroDivisionError


    def simple_generator(testcase_idx: int, rnd: Random) -> str:
        """
        A simple test case generator.
        Generates two numbers: the index and a random number between 1 and 3.
        """
        num1 = testcase_idx
        num2 = rnd.randint(1, 3)
        # Ensure num2 is not 0 for the RE example if it depended on input
        # if num2 == 0: num2 = 1  # Example adjustment
        return f"{num1} {num2}"


    # Configure the verifier: Define expected outcomes for test case index 0
    # For index 0, we expect:
    # - ac_sol to pass (AC)
    # - wa_sol to fail (WA)
    # - tle_sol to time out (TLE)
    # - re_sol to raise ZeroDivisionError
    verifier_config = {
        0: {  # Test case index 0
            AC: [ac_sol],
            WA: [wa_sol],
            TLE: [tle_sol],  # Use the TLE class directly
            ZeroDivisionError: [re_sol]  # Expecting a specific exception
        }
        # Add configurations for other testcase_idx if needed
    }

    # Create the verifier function using the factory
    # Timeout set to 1.0 second
    verify_func = verifier_factory(expected=verifier_config, timeout=1.0)

    # Create the generator runner
    run_generation = generator_runner(generator=simple_generator, verifier=verify_func)

    # Run the generation and verification for test case index 0
    print("Generating and verifying testcase #0...")
    try:
        generated_testcase, correct_answer = run_generation(0)
        print("\n--- Generated Testcase ---")
        print(generated_testcase)
        print("\n--- Verified Correct Answer ---")
        print(correct_answer)
    except GeneratorRuntimeError as e:
        print(f"\nError during generation: {e}")
        raise e
        # Potentially access e.rnd for debugging the random state
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        raise e
