import os
from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

key = AESGCM.generate_key(bit_length=256)
aes = AESGCM(key)

plaintext = "계좌 비밀번호: 1234".encode()
header = b"user-id=42"            # 암호화하지 않지만 변조는 막고 싶은 값
nonce = os.urandom(12)            # 같은 키로 절대 재사용하면 안 된다

ct = aes.encrypt(nonce, plaintext, header)
print("평문", len(plaintext), "바이트 → 암호문+태그", len(ct), "바이트")
print("복호화:", aes.decrypt(nonce, ct, header).decode())

# 암호문 1바이트 변조
bad = bytearray(ct); bad[0] ^= 1
try:
    aes.decrypt(nonce, bytes(bad), header)
except InvalidTag:
    print("암호문 변조 → InvalidTag")

# 부가 데이터 변조
try:
    aes.decrypt(nonce, ct, b"user-id=43")
except InvalidTag:
    print("부가 데이터 변조 → InvalidTag")

# nonce 재사용의 위험: 두 암호문을 XOR하면 두 평문의 XOR이 드러난다
p1, p2 = b"attack at dawn!!", b"retreat at noon!"
n = os.urandom(12)
c1 = aes.encrypt(n, p1, None)[:16]
c2 = aes.encrypt(n, p2, None)[:16]
x = bytes(a ^ b for a, b in zip(c1, c2))
print("c1^c2 == p1^p2:", x == bytes(a ^ b for a, b in zip(p1, p2)))
print("p1을 아는 공격자가 복원한 p2:", bytes(a ^ b for a, b in zip(x, p1)).decode())
