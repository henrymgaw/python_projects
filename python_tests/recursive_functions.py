#!/usr/local/bin/python3
"""
First example of a recursive function is factorials

5! = 5 * 4 * 3 * 2 * 1 
4! = 4 * 3 * 2 * 1
3! = 3 * 2 * 1
2! = 2 * 1
1! = 1

"""
def factorial(n):
    if n==0:
        return 1
    else:
        return n*factorial(n-1)

while True:
    try:
        out=factorial(int(input("Enter a factorial: ")))
        print(out)
    except ValueError:
        print("You must provide an integer value...")
        out=str(input("If you wish to exit, type exit: "))
        if out == 'exit':
           break
        else:
           pass
        continue
    
