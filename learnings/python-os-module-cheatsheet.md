# Python `os` Module: Common Functions Cheat Sheet

The `os` module lets Python talk to the operating system: folders, files, paths, environment variables and processes. It is built in, so no install is needed.

```python
import os
```

---

## 1. Current Directory and Navigation

| Function | What it does | Example |
|---|---|---|
| `os.getcwd()` | Returns the current working directory | `os.getcwd()` -> `'/Users/me/project'` |
| `os.chdir(path)` | Changes the current working directory | `os.chdir("/tmp")` |
| `os.listdir(path=".")` | Lists files and folders in a directory | `os.listdir(".")` -> `['a.py', 'data']` |
| `os.scandir(path=".")` | Like `listdir`, but returns entries with type info (faster) | see below |
| `os.walk(top)` | Walks a folder tree, yields `(dirpath, dirnames, filenames)` | see below |

```python
# scandir: tell files and folders apart
with os.scandir(".") as entries:
    for entry in entries:
        print(entry.name, "DIR" if entry.is_dir() else "FILE")

# walk: visit every file under a folder
for root, dirs, files in os.walk("tests"):
    for f in files:
        print(os.path.join(root, f))
```

---

## 2. Creating and Removing Directories

| Function | What it does |
|---|---|
| `os.mkdir(path)` | Creates one directory (parent must exist) |
| `os.makedirs(path, exist_ok=True)` | Creates nested directories, no error if it already exists |
| `os.rmdir(path)` | Removes an **empty** directory |
| `os.removedirs(path)` | Removes empty directories recursively upward |

```python
os.makedirs("reports/2026/screenshots", exist_ok=True)
os.rmdir("reports/2026/screenshots")
```

> To delete a folder that still has files in it, use `shutil.rmtree(path)` from the `shutil` module.

---

## 3. Working with Files

| Function | What it does |
|---|---|
| `os.remove(path)` | Deletes a file |
| `os.unlink(path)` | Same as `os.remove` |
| `os.rename(src, dst)` | Renames or moves a file or folder |
| `os.replace(src, dst)` | Rename that overwrites `dst` if it exists |
| `os.stat(path)` | Returns file info: size, timestamps, permissions |

```python
os.rename("old_report.html", "report.html")

info = os.stat("report.html")
print(info.st_size)   # size in bytes
print(info.st_mtime)  # last modified time (epoch seconds)

if os.path.exists("temp.log"):
    os.remove("temp.log")
```

---

## 4. `os.path`: Path Helpers (most used in tests)

| Function | What it does | Example result |
|---|---|---|
| `os.path.join(a, b, ...)` | Joins path parts with the right separator for the OS | `'data/users.csv'` |
| `os.path.exists(path)` | `True` if the file or folder exists | `True` |
| `os.path.isfile(path)` | `True` if it is a file | `True` |
| `os.path.isdir(path)` | `True` if it is a directory | `False` |
| `os.path.abspath(path)` | Converts to an absolute path | `'/Users/me/project/data'` |
| `os.path.basename(path)` | Last part of the path (file name) | `'users.csv'` |
| `os.path.dirname(path)` | Everything except the last part | `'data'` |
| `os.path.split(path)` | `(dirname, basename)` tuple | `('data', 'users.csv')` |
| `os.path.splitext(path)` | `(name, extension)` tuple | `('users', '.csv')` |
| `os.path.getsize(path)` | File size in bytes | `2048` |
| `os.path.getmtime(path)` | Last modified time (epoch seconds) | `1763200000.0` |
| `os.path.expanduser("~")` | Expands `~` to the home folder | `'/Users/me'` |
| `os.path.isabs(path)` | `True` if the path is absolute | `False` |
| `os.path.relpath(path, start)` | Relative path from `start` to `path` | `'../data'` |

```python
# Classic test pattern: build a path relative to the current test file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "testdata", "login.json")

name, ext = os.path.splitext("screenshot_01.png")
print(name, ext)  # screenshot_01 .png
```

> Always use `os.path.join()` instead of `"folder" + "/" + "file"` so the code works on Windows, macOS and Linux.

---

## 5. Environment Variables

| Function / attribute | What it does |
|---|---|
| `os.environ` | Dictionary-like object of all environment variables |
| `os.environ.get("KEY", default)` | Reads a variable safely, returns `default` if missing |
| `os.getenv("KEY", default)` | Same as above, shorter |
| `os.environ["KEY"] = "value"` | Sets a variable for the current process |
| `os.putenv(key, value)` | Low-level set (prefer `os.environ[...]`) |
| `os.unsetenv(key)` / `del os.environ[key]` | Removes a variable |

```python
# Keep secrets and config out of code
BASE_URL = os.getenv("BASE_URL", "https://staging.example.com")
API_KEY = os.environ.get("OPENAI_API_KEY")

if not API_KEY:
    raise RuntimeError("Set OPENAI_API_KEY before running tests")

os.environ["BROWSER"] = "chrome"
```

---

## 6. System and Process Information

| Function / attribute | What it does | Example |
|---|---|---|
| `os.name` | OS family: `'posix'` (macOS/Linux) or `'nt'` (Windows) | `'posix'` |
| `os.sep` | Path separator | `'/'` or `'\\'` |
| `os.linesep` | Line ending for the OS | `'\n'` or `'\r\n'` |
| `os.pathsep` | Separator used in `PATH` | `':'` or `';'` |
| `os.getpid()` | Current process ID | `48213` |
| `os.getppid()` | Parent process ID | `48100` |
| `os.cpu_count()` | Number of CPU cores | `8` |
| `os.getlogin()` | Name of the logged-in user | `'me'` |
| `os.uname()` | System details (POSIX only) | sysname, release, machine |

```python
# Decide how many parallel workers to use (pytest-xdist style)
workers = os.cpu_count() or 1
print(f"Running with {workers} workers")
```

---

## 7. Running Commands and Permissions

| Function | What it does |
|---|---|
| `os.system(cmd)` | Runs a shell command, returns the exit code |
| `os.popen(cmd)` | Runs a command and lets you read its output |
| `os.chmod(path, mode)` | Changes file permissions |
| `os.access(path, mode)` | Checks permission (`os.R_OK`, `os.W_OK`, `os.X_OK`) |

```python
exit_code = os.system("pytest -q")
output = os.popen("python --version").read()

os.chmod("run_tests.sh", 0o755)
print(os.access("run_tests.sh", os.X_OK))  # True
```

> For new code, prefer the `subprocess` module (`subprocess.run([...])`) over `os.system` and `os.popen`. It is safer and gives better control over output and errors.

---

## 8. Quick Practice Script

```python
import os

print("CWD:", os.getcwd())
print("OS:", os.name)

folder = os.path.join(os.getcwd(), "demo_output")
os.makedirs(folder, exist_ok=True)

file_path = os.path.join(folder, "hello.txt")
with open(file_path, "w") as f:
    f.write("Hello from the os module")

print("Exists?", os.path.exists(file_path))
print("Size:", os.path.getsize(file_path), "bytes")
print("Files:", os.listdir(folder))

os.remove(file_path)
os.rmdir(folder)
print("Cleaned up:", not os.path.exists(folder))
```

---

## Top 10 to Remember

1. `os.getcwd()`
2. `os.listdir()`
3. `os.makedirs(path, exist_ok=True)`
4. `os.remove()`
5. `os.rename()`
6. `os.walk()`
7. `os.path.join()`
8. `os.path.exists()`
9. `os.path.abspath(__file__)` + `os.path.dirname()`
10. `os.getenv()` / `os.environ`

> Modern alternative: `pathlib.Path` (from `pathlib import Path`) covers most of `os.path` with an object-style API, e.g. `Path("data") / "users.csv"`. Learn `os` first, then try `pathlib`.
