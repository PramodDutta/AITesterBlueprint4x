names = ["QA", "", "Automation", "", "Tester"]

def non_empty(x):
    if x != "":
        return True
    return None


non_empty = list(filter(non_empty, names))  # removes empty strings
print(non_empty)