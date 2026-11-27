---
title: "블록체인"
description: "해시 체인, 머클 트리, 합의 알고리즘, 공개 키 암호의 조합으로 블록체인이 불변 원장을 만드는 원리를 설명합니다."
parent: "보안"
nav_order: 9
permalink: /pki/blockchain/
last_modified_at: 2026-11-25
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-25
tags: [PKI, 블록체인, Blockchain, 해시, 머클트리, 합의알고리즘]
---

# 블록체인
{: .no_toc }

{% include article-toc.md %}

블록체인은 새로운 암호 알고리즘이 아니다. 해시 함수, 공개 키 암호, 디지털 서명처럼 이미 존재하는 암호 기술을 특정 방식으로 조합해 **중앙 관리자 없이 조작하기 어려운 공유 원장**을 만드는 구조다.

## 왜 "불변"이 필요한가

기존 데이터베이스는 관리자가 레코드를 수정할 수 있다. 은행 원장, 토지 등기부, 계약서가 단일 서버에 있다면 그 서버를 제어하는 주체가 기록을 바꿀 수 있다. 여러 주체가 동일한 기록을 신뢰해야 하는 상황에서 "누가 원장을 관리하는가"는 항상 갈등의 씨앗이다.

블록체인은 이 문제를 세 가지 성질로 해결한다.

- **변조 감지**: 과거 기록을 바꾸면 이후 모든 블록의 해시가 달라진다.
- **분산 복제**: 동일한 원장을 수천 개의 노드가 복사해 보관한다.
- **합의**: 새 블록을 추가하려면 네트워크 참여자 대다수가 동의해야 한다.

## 블록의 구조

블록 하나는 다음 필드를 담은 데이터 덩어리다.

```text
Block N
─────────────────────────────
prev_hash   : 이전 블록의 SHA-256 해시
timestamp   : 블록 생성 시각
transactions: 거래 목록
merkle_root : 거래 목록의 머클 루트
nonce       : PoW에서 사용하는 임의 값
─────────────────────────────
block_hash  : 위 필드 전체의 SHA-256 해시
```

`block_hash`는 이 블록 전체의 지문이다. 다음 블록은 `prev_hash`에 이 값을 담는다.

## 해시 체인: 과거를 고정하는 방법

블록이 이전 블록의 해시를 포함한다는 것이 핵심이다. 체인처럼 연결되어 있어 과거 블록 하나를 바꾸면 그 블록의 해시가 달라지고, 이후 모든 블록의 `prev_hash`와 `block_hash`가 연쇄적으로 달라진다.

```text
[Block 1]              [Block 2]              [Block 3]
prev: 0000...0000  →   prev: a3f8...2c1d  →   prev: 9b2e...4f7a
data: "Alice→Bob 5"    data: "Bob→Carol 3"    data: "Carol→Dave 1"
hash: a3f8...2c1d      hash: 9b2e...4f7a      hash: 7d1c...8e3b
```

Block 2의 거래를 "Bob→Carol **10**"으로 바꾸면 Block 2의 해시가 달라지고, Block 3의 `prev_hash`와 맞지 않게 된다. 조작한 블록부터 끝까지 전부 다시 계산해야 하고, 그 사이에 나머지 네트워크는 계속 새 블록을 추가한다. 혼자 따라잡는 것이 불가능에 가까워지는 구조다.

## 머클 트리: 거래를 효율적으로 검증하기

블록 하나에 수천 개의 거래가 담긴다. 그 중 하나의 거래가 포함되어 있는지 확인하려고 블록 전체를 내려받는 것은 비효율적이다. **머클 트리(Merkle Tree)**는 이 문제를 해결한다.

```text
         [머클 루트]
        /            \
   [H(AB)]          [H(CD)]
   /     \          /     \
[H(A)] [H(B)]  [H(C)] [H(D)]
  A       B      C       D
```

각 거래를 해시하고, 두 해시를 묶어 다시 해시한다. 이를 반복해 루트 해시 하나를 만든다. 블록 헤더에는 이 루트만 저장한다.

거래 A가 포함됐는지 확인하려면 A, H(B), H(CD) 세 값만 있으면 된다. 전체 거래 목록 없이도 O(log n)개의 해시만으로 검증할 수 있다. 이를 **머클 증명(Merkle Proof)**이라 한다.

```python
import hashlib

def sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

def merkle_root(txs: list[str]) -> str:
    if len(txs) == 1:
        return sha256(txs[0])
    if len(txs) % 2 == 1:
        txs.append(txs[-1])  # 홀수면 마지막 거래 복제
    hashes = [sha256(tx) for tx in txs]
    while len(hashes) > 1:
        next_level = []
        for i in range(0, len(hashes), 2):
            next_level.append(sha256(hashes[i] + hashes[i+1]))
        hashes = next_level
    return hashes[0]

txs = ["Alice→Bob 5", "Bob→Carol 3", "Carol→Dave 1", "Dave→Eve 2"]
print(merkle_root(txs))
```

## 공개 키 암호와 거래 서명

블록체인 거래는 디지털 서명으로 보호된다. "Alice가 Bob에게 5를 보낸다"는 거래는 Alice의 개인 키로 서명해야만 유효하다.

```text
거래 데이터: {from: Alice_주소, to: Bob_주소, amount: 5}
서명: Sign(개인키_Alice, SHA256(거래 데이터))
```

네트워크 노드는 Alice의 공개 키로 서명을 검증한다. 개인 키를 모르는 사람은 Alice 명의의 거래를 만들 수 없다.

**주소**는 공개 키의 해시다. 이더리움은 secp256k1 곡선의 ECDSA 공개 키를 Keccak-256으로 해시한 뒤 마지막 20바이트를 주소로 쓴다. 공개 키 전체보다 짧고, 그 주소에서 첫 거래를 보내기 전까지는 공개 키 자체가 드러나지 않는다는 장점도 있다.

## 합의 알고리즘

분산된 노드가 어떤 블록을 올바른 체인으로 받아들일지 결정하는 규칙이다. 대표적인 두 방식을 비교한다.

### PoW (Proof of Work)

정해진 조건(예: 해시 앞 n자리가 0)을 만족하는 `nonce`를 찾아야 한다. 무작위 대입이므로 막대한 계산이 필요하다.

```python
import hashlib

def mine(prev_hash: str, data: str, difficulty: int) -> tuple[int, str]:
    target = "0" * difficulty
    nonce = 0
    while True:
        raw = f"{prev_hash}{data}{nonce}"
        h = hashlib.sha256(raw.encode()).hexdigest()
        if h.startswith(target):
            return nonce, h
        nonce += 1

nonce, block_hash = mine("0" * 64, "Alice→Bob 5", difficulty=4)
print(f"nonce: {nonce}, hash: {block_hash}")
```

```text
nonce: 93174, hash: 0000a3f8c2d1...
```

difficulty=4이면 앞 네 자리가 0인 해시를 찾는다. 평균 65536번(16⁴)의 시도가 필요하다. Bitcoin은 이 값을 10분에 하나씩 블록이 생성되도록 조정한다.

- **장점**: 51% 이상의 계산력을 확보하지 않으면 체인을 조작하기 어렵다.
- **단점**: 전력 소비가 크다. 계산 경쟁이 중앙화를 유발한다(채굴 풀).

### PoS (Proof of Stake)

코인을 예치(stake)한 양에 비례해 블록 생성자로 선택될 확률이 높아진다. 이더리움은 2022년 PoW에서 PoS로 전환했다(The Merge).

- **장점**: 전력 소비가 PoW 대비 99% 이상 감소한다.
- **단점**: 많이 가진 자가 더 많이 가질 수 있다. 초기 분배 공정성 문제가 있다.

| 항목 | PoW | PoS |
| --- | --- | --- |
| 블록 생성자 선택 | 계산력 경쟁 | 예치량 비례 무작위 선택 |
| 51% 공격 비용 | 전체 계산력의 51% | 전체 예치량의 51% |
| 전력 소비 | 매우 높음 | 낮음 |
| 대표 체인 | Bitcoin | Ethereum (The Merge 이후) |

## 퍼블릭 vs 프라이빗 블록체인

| 구분 | 퍼블릭 | 프라이빗 / 컨소시엄 |
| --- | --- | --- |
| 참여 | 누구나 | 허가받은 노드만 |
| 합의 | PoW / PoS | PBFT, Raft 등 (참여자를 아는 상태에서 투표로 합의하는 방식) |
| 투명성 | 완전 공개 | 참여자에게만 공개 |
| 처리 속도 (TPS: 초당 거래 수) | 느림 (Bitcoin: ~7 TPS) | 빠름 (수천 TPS) |
| 예시 | Bitcoin, Ethereum | Hyperledger Fabric, Quorum |

기업 내부 정산, 공급망 추적, 금융 기관 간 청산처럼 참여자가 제한된 환경에서는 프라이빗 블록체인이 더 현실적인 선택일 수 있다.

## 블록체인이 해결하지 못하는 것

**온체인 데이터의 진실성은 보장하지 않는다.**  
"Alice가 Bob에게 5를 보냈다"는 기록이 변조되지 않았음을 보장한다. 하지만 그 거래가 현실 세계에서 올바른 행위였는지는 블록체인이 판단하지 않는다.

**오라클 문제.**  
현실 데이터(날씨, 주가, 배송 완료 여부)를 체인에 올리려면 외부 데이터 공급자(오라클)가 필요하다. 오라클이 거짓 데이터를 올리면 스마트 컨트랙트도 그 데이터를 기반으로 실행된다.

**확장성.**  
Bitcoin은 초당 약 7건, Ethereum은 약 15건을 처리한다. 비자 카드는 초당 수만 건을 처리한다. 레이어 2(메인 체인 밖에서 거래를 모아 처리하고 결과만 메인 체인에 기록하는 방식. Lightning Network, Rollup 등)가 이 격차를 줄이기 위해 개발되고 있다.

## 정리

블록체인은 해시 체인으로 과거를 고정하고, 머클 트리로 거래를 효율적으로 검증하며, 디지털 서명으로 거래 주체를 증명하고, 합의 알고리즘으로 분산 노드가 하나의 원장을 유지한다. 이 네 가지 암호 기술의 조합이 중앙 관리자 없이 신뢰할 수 있는 원장을 만드는 핵심이다.

스마트 컨트랙트와 탈중앙 애플리케이션으로 블록체인을 확장하는 개념은 [Web3]({{ "/pki/web3/" | relative_url }})에서 이어서 살펴본다.

## 참고

- [Bitcoin Whitepaper — Satoshi Nakamoto](https://bitcoin.org/bitcoin.pdf)
- [Ethereum 공식 문서: Intro to Ethereum](https://ethereum.org/en/developers/docs/intro-to-ethereum/)
- [Merkle Tree — Wikipedia](https://en.wikipedia.org/wiki/Merkle_tree)
- [Proof of Stake — Ethereum 공식 문서](https://ethereum.org/en/developers/docs/consensus-mechanisms/pos/)
