#! /usr/local/bin/python3
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
