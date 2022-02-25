#!/usr/local/bin/python3
"""
Given a number \’n\’, how to check if n is a Fibonacci number. First few Fibonacci numbers are 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, .. 
Examples : 

Input : 8
Output : Yes

Input : 34
Output : Yes

Input : 41
Output : No
"""

def fib(n_term):
    n1=0
    n2=1
    count=0
    fib_stored = []
    #print("fib seq is:")
    while count < n_term:
        nth = n1 + n2
        fib_stored.append(n1)
    #    print(n1)
        n1 = n2
        n2 = nth
        count += 1
    #    print(fib_stored)
    #return nth
    print(fib_stored)
    #return nth
    return fib_stored


def check_fib(num):
    if num in fib(100):
       return "Yes its a fib number"
    else:
       return "No its not a fib number"

out=check_fib(int(input("Enter a number to check if its in Fib: ")))
print(out)
