import hashlib
sha1 = hashlib.sha1()
sha1.update('0014748935908575f6cd917cc764883a345926107e10b0d000'.encode("utf-8"))
sha1.update(b':')
sha1.update('123456'.encode("utf-8"))

a = sha1.hexdigest()
print(a)
