#! /usr/local/bin/python3
"""
Fn = Fn-1 + Fn-2
F0 = 0 
F1 = 1
"""

def fib(n):
    if n==0 :
        return 0
    elif n ==1 :
        return 1
    else :
        return fib(n-1) +fib(n-2)

while True:
    try:
        out=fib(int(input("Enter a fibonacci nth term: ")))
        print(out)
    except ValueError:
        print("Error you did not enter an integer")
        out=input("If you want to exit program please type 'exit': ")
        if out == 'exit':
           break
        else:
           pass
        continue
