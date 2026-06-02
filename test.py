import json
import math
import os
import pathlib
import sys


def test_arithmetic():
    a = 3
    b = 4
    assert a + b == 7
    assert a * b == 12
    assert b - a == 1
    assert b / a == 4 / 3
    assert b // a == 1
    assert b % a == 1
    assert pow(a, 2) == 9


def test_strings():
    s = "Hello"
    t = "World"
    assert s + " " + t == "Hello World"
    assert s.lower() == "hello"
    assert t.upper() == "WORLD"
    assert "lo" in s
    assert s[1:4] == "ell"
    assert f"{s}, {t}!" == "Hello, World!"


def test_collections():
    xs = [1, 2, 3]
    ys = (4, 5, 6)
    zs = {7, 8, 9}
    d = {"a": 1, "b": 2}
    assert xs[0] == 1
    assert len(ys) == 3
    assert 8 in zs
    assert d["a"] == 1
    xs.append(4)
    assert xs == [1, 2, 3, 4]
    squares = [x * x for x in xs]
    assert squares == [1, 4, 9, 16]


def test_loops_and_conditionals():
    total = 0
    for i in range(5):
        if i % 2 == 0:
            total += i
        else:
            total -= i
    assert total == 2
    i = 0
    while i < 3:
        i += 1
    assert i == 3


def test_functions():
    def add(x, y=1):
        return x + y

    assert add(2, 3) == 5
    assert add(4) == 5

    def factorial(n):
        return 1 if n <= 1 else n * factorial(n - 1)

    assert factorial(5) == 120


def test_classes():
    class Animal:
        def __init__(self, name):
            self.name = name

        def speak(self):
            return f"{self.name}..."

    class Dog(Animal):
        def speak(self):
            return f"{self.name} says woof"

    dog = Dog("Rex")
    assert dog.name == "Rex"
    assert dog.speak() == "Rex says woof"


def test_exceptions():
    try:
        _ = 1 / 0
    except ZeroDivisionError:
        handled = True
    else:
        handled = False
    assert handled


def test_file_io():
    path = pathlib.Path("test_temp.txt")
    text = "python IDE functionality test"
    path.write_text(text, encoding="utf-8")
    read_back = path.read_text(encoding="utf-8")
    assert read_back == text
    path.unlink()
    assert not path.exists()


def test_modules_and_system():
    assert math.sqrt(16) == 4
    assert json.loads(json.dumps({"ok": True})) == {"ok": True}
    assert isinstance(pathlib.Path.cwd(), pathlib.Path)
    assert sys.version_info.major >= 3


def main():
    tests = [
        ("arithmetic", test_arithmetic),
        ("strings", test_strings),
        ("collections", test_collections),
        ("loops_and_conditionals", test_loops_and_conditionals),
        ("functions", test_functions),
        ("classes", test_classes),
        ("exceptions", test_exceptions),
        ("file_io", test_file_io),
        ("modules_and_system", test_modules_and_system),
    ]

    passed = 0
    failed = 0
    for name, test in tests:
        try:
            test()
            print(f"PASS: {name}")
            passed += 1
        except AssertionError:
            print(f"FAIL: {name}")
            failed += 1
        except Exception as exc:
            print(f"ERROR: {name} -> {exc.__class__.__name__}: {exc}")
            failed += 1

    print(f"\nSummary: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
