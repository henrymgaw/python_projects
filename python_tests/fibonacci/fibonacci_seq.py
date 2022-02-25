#! /usr/local/bin/python3
"""
#Fn = Fn-1 + Fn-2
count=0
n1=0
n2=1
n_term=10

print("fib seq is:")
while count < n_term:
    print(n1)
    nth = n1 + n2
    n1 = n2
    n2 = nth
    count += 1

"""





"""
Turned into a function

"""

def fib(n_term):
    count=0
    n1=0
    n2=1
    while count < n_term:
        nth = n1 + n2
        print(n1)
        n1 = n2
        n2 = nth
        count += 1
        
    return nth

out=fib(10)
print(out)

