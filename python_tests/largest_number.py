#! /usr/local/bin/python3
#Find the largest number among three numbers
#num1= -5
#num2= 12
#num3= 8

#num = int(input("Enter a number:"))
#while num:
#    if num < 0:
#       print("the number is negative")
#       largest = num
#       num = int(input("Enter a number:"))
#    elif num > 0 and num <= 10:
#       print("the number is between 0 - 10")
#       largest = num
#       num = int(input("Enter a number:"))
#    else:
#       largest = num
#       print("found the largest number:" , largest)
#       break

def largest_number_of_three(num1,num2,num3):
    if num1 > num2 and num1 > num3:
        print("num1 is the largest")
        largest=num1
        return largest
    elif num2 > num1 and num2 > num3:
        print("num2 is the largest")
        largest=num2
        return largest
    else:
        print("num3 is the largest")
        largest=num3
        return largest

largest=largest_number_of_three(-5,12,8)
print(largest)
