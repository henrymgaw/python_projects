#!/usr/local/bin/python3
def check_similarities(seq1,seq2):
    s3=[]
    for s1 in str(seq1):
       for s2 in str(seq2):
           if s1 in s2:
              s3.append(s1)
              print(s1)
    return str(set(s3))

out=check_similarities(1223,1332)
print(out)
