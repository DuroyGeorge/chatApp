import json

test = {1: 1, 2: 2}
for key, val in test.items():
    print(type(key), type(val), key, val)
jo = json.dumps(test)
test = json.loads(jo)
print(jo)
for key, val in test.items():
    print(type(key), type(val), key, val)
