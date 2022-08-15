#!/usr/local/bin/python3
#list all possible outcomes of 'a', 'e', 'i', 'o', 'u'
#where each letter can only be used once

def possible_outcomes(vowels):
    len_vowels=len(vowels)
    total_possible_outcomes = len_vowels * len_vowels
    return total_possible_outcomes
    


vowels = ['a', 'e', 'i', 'o', 'u', 'y']
out=possible_outcomes(vowels)
print(out)

