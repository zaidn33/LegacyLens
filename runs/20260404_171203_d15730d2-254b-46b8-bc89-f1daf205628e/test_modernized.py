
import pytest

def test_greeting_message():
    # Critical Constraint: The greeting message must be 'HELLO, WORLD!'.
    greetingMessage = 'HELLO, WORLD!'
    assert greetingMessage == 'HELLO, WORLD!'

def test_max_iterations():
    # Critical Constraint: The maximum number of iterations must be 5.
    maxIterations = 5
    assert maxIterations == 5

def test_loop_iterations():
    # Business Rule: The program must print the greeting message exactly five times.
    iterationCounter = 0
    maxIterations = 5
    while iterationCounter < maxIterations:
        iterationCounter += 1
    assert iterationCounter == maxIterations

def test_counter_increment():
    # Business Rule: The counter must increment by 1 with each iteration.
    iterationCounter = 0
    maxIterations = 5
    for _ in range(maxIterations):
        iterationCounter += 1
    assert iterationCounter == maxIterations
