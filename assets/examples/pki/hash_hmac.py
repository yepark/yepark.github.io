import hashlib
import hmac
import secrets

# 1. 해시: 같은 입력 → 같은 값, 한 글자만 바뀌어도 완전히 다른 값
for text in ["이체 금액: 10000원", "이체 금액: 10001원"]:
    print(hashlib.sha256(text.encode()).hexdigest()[:32], text)

# 2. 길이는 입력과 상관없이 고정
print(len(hashlib.sha256(b"a").digest()), len(hashlib.sha256(b"a" * 1_000_000).digest()), "bytes")

# 3. HMAC: 비밀 키가 있어야 만들 수 있는 검사값
key = secrets.token_bytes(32)
msg = b'{"to":"lee","amount":10000}'
tag = hmac.new(key, msg, hashlib.sha256).hexdigest()
print("tag:", tag[:32])

# 받는 쪽: 같은 키로 다시 계산해 비교 (시간이 일정한 비교 함수를 쓴다)
def verify(key, msg, tag):
    expected = hmac.new(key, msg, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, tag)

print("원본 검증:", verify(key, msg, tag))
print("변조 검증:", verify(key, b'{"to":"lee","amount":90000}', tag))
print("다른 키:", verify(secrets.token_bytes(32), msg, tag))
