# Find the positive number is even or odd

num = int(input("Enter a numner").strip())

if  num>=0:
    if num%2 ==0:
        print("Even")
    else:
        print("Odd")
else:
    print("Negative Number!")