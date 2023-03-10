from datetime import *

elapsed = datetime.now()-(datetime.now()-timedelta(hours=2))
print(dir(elapsed))

print(elapsed.seconds)

if elapsed.seconds//3600 <= 23:
    print(elapsed.seconds//3600)
else:
    print((elapsed.seconds//3600)//24)


