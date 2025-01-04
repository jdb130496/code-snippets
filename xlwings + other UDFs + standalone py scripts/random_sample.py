import random
lst=[x/20 for x in random.sample(range(60,151),10)]
while lst[-1]<=lst[0]:
	lst[-1]= random.sample(range(60,151),1)[0]/20
print(lst)
