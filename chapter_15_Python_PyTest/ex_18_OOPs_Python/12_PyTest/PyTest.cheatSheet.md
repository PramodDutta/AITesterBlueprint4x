# PyTest Cheatsheet

A quick reference for pytest, the most popular Python testing framework. Examples use the same style as the files in this folder (`test_180.py`, `test_181.py`).

---

## 1. Installation & Running

```bash
pip install pytest

pytest                          # run all tests in current dir
pytest test_180.py              # run one file
pytest -k "smoke"               # run tests matching keyword (name or marker)
pytest -m smoke                 # run tests with marker @pytest.mark.smoke
pytest -v                       # verbose output (shows each test name)
pytest -s                       # show print() output (disables capture)
pytest -v -s                    # combine both
pytest --maxfail=2              # stop after 2 failures
pytest -x                       # stop at first failure
pytest --lf                     # rerun only last failed tests
pytest --co                     # collect only (dry run, no execution)
```

> Note: `pytest -k "smoke"` matches by *keyword* (substring of test name or marker). `pytest -m smoke` matches by *marker* exactly.

---

## 2. Naming Conventions (IMPORTANT)

PyTest auto-discovers files/functions following these rules:

| Item | Rule |
|------|------|
| Test files | `test_*.py` or `*_test.py` |
| Test functions | `test_*` prefix |
| Test classes | `Test*` prefix, no `__init__` method |

```python
def test_login():        # ✅ discovered
def check_login():       # ❌ ignored (no test_ prefix)
class TestCart:          # ✅ discovered
class CartTests:         # ❌ ignored
```

---

## 3. Basic Assertions

PyTest uses plain Python `assert`. No need for `self.assertEqual` like unittest.

```python
import pytest

def test_addition():
    assert 1 + 1 == 2

def test_string():
    assert "hello" in "hello world"

def test_type():
    assert isinstance(42, int)

def test_raises():
    with pytest.raises(ZeroDivisionError):
        1 / 0
```

On failure, pytest shows the actual values automatically (assertion rewriting).

---

## 4. Markers

Tag tests to run groups selectively.

```python
import pytest

@pytest.mark.smoke
def test_method2():
    assert 1 - 1 == 2

@pytest.mark.regression
def test_login():
    assert 1 + 1 == 2
```

```bash
pytest -m smoke            # only smoke tests
pytest -m "not smoke"      # everything except smoke
pytest -m "smoke or regression"
```

**Register custom markers** to avoid warnings, in `pytest.ini`:

```ini
[pytest]
markers =
    smoke: quick sanity checks
    regression: full regression suite
```

Skip and expected-failure markers:

```python
@pytest.mark.skip(reason="feature not ready")
def test_new_feature(): ...

@pytest.mark.skipif(sys.version_info < (3, 10), reason="needs py3.10+")
def test_modern(): ...

@pytest.mark.xfail(reason="known bug QA-123")
def test_known_bug(): ...
```

---

## 5. Fixtures (Setup / Teardown)

Fixtures provide reusable setup code. Tests request them by name as arguments.

```python
import pytest

@pytest.fixture
def sample_data():
    return {"user": "admin", "password": "Admin@123"}

def test_with_fixture(sample_data):
    assert sample_data["user"] == "admin"
```

Fixture scopes (how long the fixture lives):

```python
@pytest.fixture(scope="function")   # default: fresh per test
@pytest.fixture(scope="module")     # once per file
@pytest.fixture(scope="session")    # once per entire run (e.g., DB connection)
```

Teardown using `yield` (code after yield runs after each test):

```python
@pytest.fixture
def browser():
    print("open browser")     # setup
    yield "chrome"
    print("close browser")    # teardown
```

Common built-in fixtures: `tmp_path` (temp dir), `capsys` (capture stdout), `monkeypatch` (patch env/attrs), `caplog` (capture logs).

```python
def test_file(tmp_path):
    f = tmp_path / "data.txt"
    f.write_text("hello")
    assert f.read_text() == "hello"
```

---

## 6. Parametrized Tests (Data-Driven)

Run the same test with multiple inputs. Perfect for login test data like our `TD.csv`.

```python
import pytest

@pytest.mark.parametrize("username, password, expected", [
    ("admin@example.com", "Admin@123", "valid_login"),
    ("user1@example.com", "wrongpass", "invalid_password"),
    ("", "password123", "empty_username"),
])
def test_login(username, password, expected):
    result = fake_login(username, password)
    assert result == expected
```

Each tuple becomes a separate test case shown individually in output.

Parametrize + fixture combo (`indirect` passes params into a fixture) exists but is advanced; keep it for later.

---

## 7. Reading CSV Test Data (with pandas)

Pattern used in this chapter:

```python
import pandas as pd
import os
import pytest

base_dir = os.path.dirname(os.path.abspath(__file__))

@pytest.fixture(scope="session")
def login_data():
    return pd.read_csv(os.path.join(base_dir, "..", "ex_20_Collections_FileIO", "TD.csv"))

@pytest.mark.parametrize("row", range(10))
def test_rows(login_data, row):
    data = login_data.iloc[row]
    assert pd.notna(data["username"]) or pd.isna(data["username"])
```

Or simpler, load rows directly into parametrize:

```python
df = pd.read_csv(file_path)
params = [(r.username, r.password, r.expected_result) for r in df.itertuples()]

@pytest.mark.parametrize("u,p,e", params)
def test_login(u, p, e): ...
```

---

## 8. conftest.py

Special file where fixtures are shared across multiple test files **without importing them**. Pytest picks it up automatically from the same directory (or any parent).

```
ex_21_PyTest/
├── conftest.py        # shared fixtures live here
├── test_180.py
└── test_181.py
```

```python
# conftest.py
import pytest

@pytest.fixture
def base_url():
    return "https://api.example.com"
```

Any test file in that folder can now just take `base_url` as an argument.

Also good place for hooks like `pytest_addoption` (custom CLI flags).

---

## 9. Configuration Files

| File | Purpose |
|------|---------|
| `pytest.ini` | Main config: markers, testpaths, addopts |
| `conftest.py` | Shared fixtures & hooks |
| `pyproject.toml` | Can also hold `[tool.pytest.ini_options]` |

Example `pytest.ini`:

```ini
[pytest]
testpaths = .
addopts = -v -s
markers =
    smoke: quick sanity checks
    regression: full regression suite
```

Now plain `pytest` runs verbosely with prints visible.

---

## 10. Useful Plugins

```bash
pip install pytest-xdist      # parallel: pytest -n 4
pip install pytest-html       # HTML report: pytest --html=report.html
pip install pytest-cov        # coverage: pytest --cov=mypackage
pip install pytest-ordering   # control test order (avoid if possible)
pip install pytest-mock       # mocker fixture wrapping unittest.mock
```

---

## 11. Quick Reference Card

| Command / Feature | What it does |
|---|---|
| `pytest` | Run all tests |
| `pytest -v` | Verbose per-test output |
| `pytest -s` | Show print statements |
| `pytest -k "expr"` | Filter by keyword |
| `pytest -m marker` | Filter by marker |
| `@pytest.fixture` | Reusable setup function |
| `scope="session"` | Fixture runs once per run |
| `yield` in fixture | Teardown after yield |
| `@pytest.mark.parametrize` | Data-driven tests |
| `@pytest.mark.skip` | Skip a test |
| `pytest.raises(Error)` | Assert exception raised |
| `conftest.py` | Auto-shared fixtures |
| `pytest.ini` | Global config |

---

*Created for AI Tester Blueprint, Chapter 11 (Python Learning).*