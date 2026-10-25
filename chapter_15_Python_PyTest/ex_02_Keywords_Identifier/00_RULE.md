# Rules for Identifiers in Python

An **identifier** is the name you give to a variable, function, class, or module.

```python
name = "Pramod"
# name     -> identifier / variable name
# =        -> assignment operator
# "Pramod" -> literal / value
```

---

## Rule 1: Allowed characters are letters, digits, and underscore

Only `a-z`, `A-Z`, `0-9`, and `_` are allowed. Nothing else.

```python
age = 65            # valid
first_name = "Pramod"   # valid
abc123 = "abc123"   # valid

# first-name = "Pramod"   # INVALID -> hyphen not allowed
# first name = "Pramod"   # INVALID -> space not allowed
# total$ = 100            # INVALID -> $ not allowed
```

---

## Rule 2: Cannot start with a digit

Can start with a letter or an underscore, never a number.

```python
abc123 = "abc123"   # valid
_age = 65           # valid, underscore start is fine

# 123abc = 90       # INVALID -> SyntaxError
```

---

## Rule 3: Cannot be a Python keyword

Keywords are reserved by the language.

```python
import keyword
print(keyword.kwlist)
# ['False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break',
#  'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'finally',
#  'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal',
#  'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield']

# class = "Selenium"   # INVALID -> class is a keyword
# for = 10             # INVALID -> for is a keyword

class_name = "Selenium"   # valid workaround
```

Quick check:

```python
print(keyword.iskeyword("class"))       # True
print(keyword.iskeyword("class_name"))  # False
```

---

## Rule 4: Identifiers are case sensitive

`age`, `Age`, and `AGE` are three different variables.

```python
age = 65
Age = 30
AGE = 18
print(age, Age, AGE)   # 65 30 18
```

---

## Rule 5: No length limit

Long names are legal, but keep them readable.

```python
this_is_a_very_long_but_perfectly_valid_identifier = 1
n = 1   # legal but tells you nothing
```

---

## Rule 6: A single underscore `_` is a valid identifier

Often used for a throwaway or "last value" variable.

```python
_ = 12
print(_)      # 12
_ = _ + 1
print(_)      # 13
```

---

## Rule 7: Avoid shadowing built-in names

Not an error, but it breaks the built-in for the rest of your code.

```python
# list = [1, 2, 3]    # works, but now list() is broken
# print(list("abc"))  # TypeError

my_list = [1, 2, 3]   # do this instead
```

---

## Naming conventions (PEP 8)

Not enforced by Python, but expected by every Python developer.

| Thing | Style | Example |
|---|---|---|
| Variable / function | `snake_case` | `first_name`, `get_user()` |
| Constant | `UPPER_SNAKE_CASE` | `PI = 3.14`, `MAX_RETRY = 3` |
| Class | `PascalCase` | `LoginPage`, `TestUser` |
| Module / file | `lowercase` | `login_page.py` |
| Internal / private | leading `_` | `_counter` |

```python
PI = 3.14
MAX_RETRY = 3

class LoginPage:
    pass

def get_user_name():
    return "Pramod"
```

---

## Cheat sheet

| Identifier | Valid? | Reason |
|---|---|---|
| `age` | Yes | letters only |
| `_age` | Yes | underscore start allowed |
| `abc123` | Yes | digit not in first position |
| `_` | Yes | single underscore is legal |
| `first_name` | Yes | underscore separator |
| `123abc` | No | starts with a digit |
| `first-name` | No | hyphen not allowed |
| `first name` | No | space not allowed |
| `class` | No | Python keyword |
| `total$` | No | `$` not allowed |
| `age` vs `Age` | Both valid | different variables, case sensitive |

---

## In Simple Terms

Start with a letter or `_`, use only letters/digits/`_` after that, do not pick a keyword, and remember Python sees uppercase and lowercase as different names.