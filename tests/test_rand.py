import random
knownPrices = [0,1,2,3,4,5]
x = random.choice([i for i in range(0, 2) if i not in knownPrices]) # TODO check if failed
print(x)
print(type(x))