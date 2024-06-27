import rsa
import time

st = time.time()

publicKey, privateKey = ("pu", "pr")

for i in range(0, 128):
    print(i)
    try:
        publicKey, privateKey = rsa.newkeys(i)
        break
    except:
        pass

puk = str(publicKey.n) + "," + str(publicKey.e)
prk = str(privateKey.n) + "," + str(privateKey.e)

with open("keys.txt", 'w+') as file:
    file.write(puk + "\n" + prk)

en = time.time()

print(en - st)
