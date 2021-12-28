#! /usr/local/bin/python3
#Find the largest number among three numbers
#num= -5
#num= 12
#num= 8

num = int(input("Enter a number:"))
while num:
    if num < 0:
       print("the number is negative")
       largest = num
       num = int(input("Enter a number:"))
    elif num > 0 and num <= 10:
       print("the number is between 0 - 10")
       largest = num
       num = int(input("Enter a number:"))
    else:
       largest = num
       print("found the largest number:" , largest)
       break
   
