// Secure Enclave 키 실습 (macOS, Apple silicon)
// 빌드: swiftc se_demo.swift -o se_demo
import CryptoKit
import Foundation

typealias SEKey = SecureEnclave.P256.Signing.PrivateKey

print("1. isAvailable:", SecureEnclave.isAvailable)
guard SecureEnclave.isAvailable else { exit(1) }

// 2. Secure Enclave 안에서 키 만들기
let key = try SEKey()
let pub = key.publicKey
print("2. 공개 키 (x963):", pub.x963Representation.count,
      "바이트")

// 3. 서명은 Secure Enclave 안에서 일어난다
let msg = Data("hello enclave".utf8)
let sig = try key.signature(for: msg)
print("3. 서명 (DER):", sig.derRepresentation.count,
      "바이트")

// 4. 일반 CryptoKit 공개 키로 검증
let verifier = try P256.Signing.PublicKey(
    x963Representation: pub.x963Representation)
print("4. 검증:", verifier.isValidSignature(sig, for: msg))
let bad = Data("hello enclavE".utf8)
print("   바꾼 메시지 검증:",
      verifier.isValidSignature(sig, for: bad))

// 5. 개인 키를 "꺼내" 보기
let blob = key.dataRepresentation
print("5. dataRepresentation:", blob.count, "바이트")
print("   앞 16바이트:",
      blob.prefix(16).map { String(format: "%02x", $0) }
          .joined())
// 일반 P256 개인 키로 읽어 보기
do {
    _ = try P256.Signing.PrivateKey(rawRepresentation: blob)
    print("   일반 키로 읽힘")
} catch {
    print("   일반 P256 키로 읽기 실패:", error)
}

// 6. blob으로 같은 키 되살리기
let again = try SEKey(dataRepresentation: blob)
print("6. 되살린 키의 공개 키 같음:",
      again.publicKey.rawRepresentation
          == pub.rawRepresentation)
let sig2 = try again.signature(for: msg)
print("   되살린 키 서명 검증:",
      verifier.isValidSignature(sig2, for: msg))

// 7. 키 합의(ECDH)용 키도 만들 수 있다
let ka = try SecureEnclave.P256.KeyAgreement.PrivateKey()
let peer = P256.KeyAgreement.PrivateKey()
let s1 = try ka.sharedSecretFromKeyAgreement(
    with: peer.publicKey)
let s2 = try peer.sharedSecretFromKeyAgreement(
    with: ka.publicKey)
print("7. 공유 비밀 같음:", s1 == s2)
