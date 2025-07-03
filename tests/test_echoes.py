import subprocess
import sys


def run_echoes(message, times=1):
    cmd = [sys.executable, 'echoes.py', message, '-n', str(times)] if times != 1 else [sys.executable, 'echoes.py', message]
    result = subprocess.run(cmd, text=True, capture_output=True, check=True)
    return result.stdout.strip().splitlines()


def test_single_echo():
    output = run_echoes('hello')
    assert output == ['hello']


def test_multiple_echoes():
    output = run_echoes('hi', 3)
    assert output == ['hi', 'hi', 'hi']
