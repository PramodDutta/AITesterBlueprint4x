import os

print("CWD:", os.getcwd())
print("OS:", os.name)

folder = os.path.join(os.getcwd(), "demo_output")
print(folder)

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
