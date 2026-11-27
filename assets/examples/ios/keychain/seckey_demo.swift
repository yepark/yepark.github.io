// SecKeyCreateRandomKey로 Secure Enclave 키 만들기
// 빌드: swiftc seckey_demo.swift -o seckey_demo
import Foundation
import Security

func makeKey(permanent: Bool) {
    var err: Unmanaged<CFError>?
    guard let access = SecAccessControlCreateWithFlags(
        nil,
        kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
        .privateKeyUsage,
        &err
    ) else { print("access 실패"); return }

    let attrs: [String: Any] = [
        kSecAttrKeyType as String:
            kSecAttrKeyTypeECSECPrimeRandom,
        kSecAttrKeySizeInBits as String: 256,
        kSecAttrTokenID as String:
            kSecAttrTokenIDSecureEnclave,
        kSecPrivateKeyAttrs as String: [
            kSecAttrIsPermanent as String: permanent,
            kSecAttrApplicationTag as String:
                Data("com.example.se.demo".utf8),
            kSecAttrAccessControl as String: access,
        ] as [String: Any],
    ]

    guard let priv = SecKeyCreateRandomKey(
        attrs as CFDictionary, &err) else {
        let e = err!.takeRetainedValue()
        print("permanent=\(permanent) 실패:", e)
        return
    }
    print("permanent=\(permanent) 성공")

    // 개인 키 내보내기 시도
    var exErr: Unmanaged<CFError>?
    if let d = SecKeyCopyExternalRepresentation(
        priv, &exErr) {
        print("  개인 키 내보내기:", (d as Data).count)
    } else {
        print("  개인 키 내보내기 실패:",
              exErr!.takeRetainedValue())
    }

    // 공개 키는 꺼낼 수 있다
    let pub = SecKeyCopyPublicKey(priv)!
    let pubData = SecKeyCopyExternalRepresentation(
        pub, nil)! as Data
    print("  공개 키:", pubData.count, "바이트")

    // 서명과 검증
    let alg = SecKeyAlgorithm.ecdsaSignatureMessageX962SHA256
    let msg = Data("hello".utf8) as CFData
    let sig = SecKeyCreateSignature(priv, alg, msg, &err)!
    print("  검증:",
          SecKeyVerifySignature(pub, alg, msg, sig, &err))
}

makeKey(permanent: false)
makeKey(permanent: true)
