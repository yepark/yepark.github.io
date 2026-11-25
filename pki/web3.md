---
title: "Web3"
description: "스마트 컨트랙트, DApp, DeFi, NFT의 동작 원리와 한계, Web2와의 차이를 개발자 관점에서 설명합니다."
parent: "PKI & 암호"
nav_order: 10
permalink: /pki/web3/
last_modified_at: 2026-11-25
seo:
  type: BlogPosting
date: 2026-11-25
first_written: 2026-11-25
last_modified_date: 2026-11-25
tags: [PKI, Web3, 블록체인, 스마트컨트랙트, DeFi, NFT, Ethereum]
---

# Web3
{: .no_toc }

{% include article-toc.md %}

Web1은 읽기만 되는 정적 웹이었고, Web2는 플랫폼이 콘텐츠와 데이터를 소유하는 쌍방향 웹이다. **Web3**는 소유권과 제어권을 중앙 플랫폼에서 사용자에게 돌려주는 것을 목표로 하는 패러다임이다. 그 기반 기술이 블록체인과 스마트 컨트랙트다.

{: .note }
Web3는 하나의 확정된 표준이 아니다. 비전과 기술 접근 방법에 대한 논쟁이 여전히 진행 중이다. 이 글은 현재 주류 기술 스택을 중심으로 개발자 관점에서 살펴본다.

## Web2와 Web3의 차이

| 항목 | Web2 | Web3 |
| --- | --- | --- |
| 데이터 소유 | 플랫폼 (Google, Meta 등) | 사용자 (지갑 키로 제어) |
| 인증 | 아이디·비밀번호, OAuth | 개인 키 서명 (지갑) |
| 애플리케이션 로직 | 중앙 서버 | 블록체인 위 스마트 컨트랙트 |
| 결제 | 은행·카드사 중개 | 토큰 직접 전송 |
| 중단 위험 | 서버 장애, 서비스 종료 | 네트워크가 살아 있으면 계속 실행 |
| 감사 가능성 | 내부에서만 가능 | 누구나 블록체인에서 확인 가능 |

Web3의 핵심은 플랫폼 없이도 신뢰할 수 있는 거래와 애플리케이션 실행이 가능하다는 것이다. 단, 이 신뢰는 블록체인 프로토콜 자체에 대한 신뢰다.

## 스마트 컨트랙트

스마트 컨트랙트는 블록체인 위에 배포된 프로그램이다. 조건이 충족되면 중개자 없이 자동으로 실행된다.

```text
"에스크로"를 예로 들면

기존: Alice가 돈을 에스크로 회사에 맡기고, 서비스 완료 확인 후 Bob에게 지급
스마트 컨트랙트: Alice가 컨트랙트에 토큰을 잠근다.
                 Bob이 완료 조건을 충족하면 컨트랙트가 자동으로 토큰을 Bob에게 전송
                 Alice도 Bob도 에스크로 회사도 개입하지 않는다
```

### Solidity 맛보기

이더리움의 스마트 컨트랙트 언어는 주로 **Solidity**다.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SimpleEscrow {
    address public buyer;
    address public seller;
    uint256 public amount;
    bool public released;

    constructor(address _seller) payable {
        buyer  = msg.sender;    // 컨트랙트 배포자가 구매자
        seller = _seller;
        amount = msg.value;     // 함께 보낸 이더가 잠긴다
    }

    // 구매자가 완료를 확인하면 판매자에게 이더 전송
    function release() external {
        require(msg.sender == buyer, "구매자만 실행 가능");
        require(!released, "이미 처리됨");
        released = true;
        payable(seller).transfer(amount);
    }
}
```

한 번 배포된 컨트랙트 코드는 블록체인에 영구 기록된다. 누구나 코드를 볼 수 있고, 아무도 임의로 바꿀 수 없다. 버그가 있어도 같은 주소의 컨트랙트를 수정할 수 없으므로 배포 전 감사(audit)가 중요하다.

### EVM (Ethereum Virtual Machine)

스마트 컨트랙트는 EVM 위에서 실행된다. EVM은 모든 이더리움 노드가 동일하게 구현한 가상 머신이다. 같은 입력에 대해 항상 같은 결과를 내야 하므로 결정론적(deterministic)으로 동작한다.

외부 API 호출, 현재 시각, 난수 같은 비결정적 요소는 직접 사용할 수 없다. 대신 오라클이나 블록 해시를 활용하는데, 이 한계가 스마트 컨트랙트 설계의 핵심 제약 중 하나다.

## 가스 (Gas)

스마트 컨트랙트 실행에는 계산 비용이 든다. 이더리움에서는 이를 **가스**로 측정한다. 덧셈 하나, 저장소 쓰기 하나마다 가스가 소모된다.

```text
가스 비용 = 가스 사용량 × 가스 단가 (Gwei)
실제 이더 비용 = 가스 비용 × 이더 가격
```

가스는 두 가지 역할을 한다.

- **DDoS 방어**: 무한 루프 컨트랙트가 네트워크를 마비시키지 못하도록 실행 비용에 상한을 둔다.
- **자원 배분**: 네트워크가 혼잡할 때 더 높은 가스비를 제시한 거래가 먼저 처리된다.

가스비가 높을 때는 단순한 토큰 전송도 수천 원이 넘는다. 이것이 소액 거래에서 Web3 사용성을 떨어뜨리는 주요 원인이다.

## 지갑과 개인 키

Web3에서 사용자 인증은 지갑의 개인 키 서명으로 이루어진다. 아이디·비밀번호가 없다.

```text
[로그인 대신 서명]
서비스: "다음 메시지에 서명해 주세요: Login to example.com at 2026-11-25T12:00:00Z"
사용자: 개인 키로 서명
서비스: 공개 키(= 주소)로 서명 검증 → 이 주소의 소유자임을 확인
```

지갑 소프트웨어(MetaMask, Phantom 등)가 이 서명 과정을 대신한다. 사용자는 니모닉 구문(12~24개 단어)으로 개인 키를 복구할 수 있다.

**개인 키를 잃으면 자산을 영구히 잃는다.** 은행처럼 비밀번호 초기화를 요청할 곳이 없다. 니모닉 구문 보관이 Web3 보안의 가장 기초다.

## DApp (분산 애플리케이션)

DApp은 프론트엔드는 일반 웹과 같지만 백엔드 로직이 스마트 컨트랙트 위에서 실행된다.

```text
[일반 Web2 앱]
브라우저 → 프론트엔드 → 중앙 서버 → DB

[DApp]
브라우저 → 프론트엔드 → 블록체인 노드 → 스마트 컨트랙트
                 ↑
            지갑(MetaMask)으로 서명
```

프론트엔드는 여전히 중앙 서버에서 호스팅할 수 있다. 완전한 탈중앙화를 위해 IPFS(InterPlanetary File System) 같은 분산 스토리지를 쓰기도 하지만, 대부분의 DApp은 프론트엔드만큼은 중앙 서버를 쓴다.

### ethers.js로 컨트랙트 호출

```javascript
import { ethers } from "ethers";

// MetaMask 지갑에 연결
const provider = new ethers.BrowserProvider(window.ethereum);
const signer   = await provider.getSigner();

const contractAddress = "0xAbc123...";
const abi = [
  "function release() external",
  "function amount() view returns (uint256)"
];

const contract = new ethers.Contract(contractAddress, abi, signer);

// 읽기 (가스 없음)
const amount = await contract.amount();
console.log("잠긴 금액:", ethers.formatEther(amount), "ETH");

// 쓰기 (지갑에서 서명 요청 → 가스 발생)
const tx = await contract.release();
await tx.wait();  // 블록에 포함될 때까지 대기
console.log("완료:", tx.hash);
```

## DeFi (탈중앙 금융)

DeFi는 스마트 컨트랙트로 금융 서비스를 구현한다. 은행·증권사·보험사 없이 대출, 예금, 거래소 기능을 제공한다.

### AMM (자동화 시장 메이커)

전통 거래소는 매수·매도 주문을 매칭한다. AMM은 수식으로 가격을 결정한다.

```text
유동성 풀: ETH 100개, USDC 200,000개
상수 k = 100 × 200,000 = 20,000,000

ETH 1개를 사려면:
  새 ETH 수량 = 100 - 1 = 99
  새 USDC 수량 = 20,000,000 / 99 ≈ 202,020
  지불할 USDC = 202,020 - 200,000 = 2,020 USDC
```

`x * y = k` 공식으로 거래 상대방 없이도 가격이 결정된다. Uniswap이 이 모델을 대중화했다.

### 주요 DeFi 카테고리

| 카테고리 | 설명 | 예시 |
| --- | --- | --- |
| DEX | 탈중앙 거래소, 토큰 교환 | Uniswap, Curve |
| 대출 | 담보 예치 후 다른 토큰 대출 | Aave, Compound |
| 스테이블코인 | 달러 가치에 연동된 토큰 | DAI, USDC |
| 수익 농사 | 유동성 제공 대가로 보상 수령 | Yearn Finance |

## NFT (대체 불가 토큰)

일반 토큰은 대체 가능하다(1 ETH = 1 ETH). NFT는 각 토큰이 고유한 ID를 가져 대체 불가능하다.

이더리움 ERC-721 표준에서 NFT의 핵심은 소유권 기록이다.

```text
tokenId 42 → owner: 0xAlice...

Alice가 Bob에게 전송:
tokenId 42 → owner: 0xBob...
```

이 소유권 기록은 블록체인에 있어 조작할 수 없다. 단, **NFT가 가리키는 실제 파일**(이미지, 영상)은 대부분 IPFS나 중앙 서버에 있다. 중앙 서버가 사라지면 NFT는 존재하지만 가리키는 콘텐츠는 사라질 수 있다.

```solidity
// ERC-721 핵심 함수 (인터페이스)
function ownerOf(uint256 tokenId) external view returns (address);
function transferFrom(address from, address to, uint256 tokenId) external;
function tokenURI(uint256 tokenId) external view returns (string memory);
// tokenURI가 반환하는 URL에 실제 메타데이터(이미지 경로 등)가 있다
```

## 레이어 2: 확장성 문제 해결

메인 체인(레이어 1) 위에 추가 처리 계층을 올리는 방식이다. 거래를 오프체인에서 처리하고 결과만 메인 체인에 기록한다.

| 방식 | 원리 | 대표 사례 |
| --- | --- | --- |
| Optimistic Rollup | 거래를 묶어 올리고, 이의 제기 기간 동안 검증 | Optimism, Arbitrum |
| ZK Rollup | 영지식 증명으로 거래 묶음의 유효성 증명 | zkSync, StarkNet |
| State Channel | 채널 열기·닫기만 온체인, 중간 거래는 오프체인 | Lightning Network |

Optimistic Rollup은 이더리움 대비 10~100배 빠르고 가스비가 낮다. ZK Rollup은 증명 생성 비용이 크지만 즉시 확정성이 있다.

## 개발자 관점에서의 현실적 한계

**스마트 컨트랙트 버그는 돌이킬 수 없다.**  
코드를 수정할 수 없는 구조에서 버그는 자산 손실로 직결된다. 2016년 The DAO 해킹(약 6천만 달러)이 대표적인 사례다. 프록시 패턴, 멀티시그 거버넌스 등 업그레이드 가능한 구조를 쓰기도 하지만 그 자체가 중앙화 요소가 된다.

**사용자 경험이 복잡하다.**  
지갑 설치, 니모닉 보관, 가스비 개념, 트랜잭션 대기 시간은 일반 사용자에게 높은 진입 장벽이다.

**프론트엔드는 여전히 중앙화되어 있다.**  
Uniswap의 프론트엔드 도메인이 미국 규제로 특정 토큰 접근을 차단한 사례처럼, DApp의 UI 레이어는 검열에서 자유롭지 않다.

**오라클 의존성.**  
현실 데이터를 체인에 가져오는 오라클 계층은 탈중앙화의 약한 고리다. Chainlink 같은 탈중앙 오라클도 최종적으로는 외부 데이터 공급자에 의존한다.

## DID와 Web3의 연결

[DID]({{ "/pki/did/" | relative_url }})는 Web3의 신원 계층으로 쓰인다. 이더리움 주소가 기본 식별자가 되고, DID Document가 그 주소에 연결된 공개 키와 서비스를 정의한다. VC는 오프체인에서 발급되고 보관되지만, 폐기 상태는 체인에 기록할 수 있다.

Web3 애플리케이션에서 "지갑 연결"은 단순히 결제 수단을 연결하는 것이 아니라 사용자의 DID를 연결하는 행위로 발전하고 있다.

## 정리

Web3는 스마트 컨트랙트로 중개자 없이 신뢰할 수 있는 애플리케이션 로직을 실행하고, 개인 키 서명으로 소유권을 증명하는 패러다임이다. DeFi, NFT, DApp은 이 위에서 동작하는 대표적인 응용이다. 확장성, 사용성, 스마트 컨트랙트 불변성이라는 근본적인 한계가 있고, 레이어 2와 DID 같은 기술이 이를 보완하고 있다.

## 참고

- [Ethereum 공식 문서: Web3 개요](https://ethereum.org/en/web3/)
- [ethers.js 공식 문서](https://docs.ethers.org/)
- [Solidity 공식 문서](https://docs.soliditylang.org/)
- [Uniswap: AMM 설명](https://docs.uniswap.org/concepts/protocol/swaps)
- [ERC-721 표준](https://eips.ethereum.org/EIPS/eip-721)
- [L2Beat: 레이어 2 현황](https://l2beat.com/)
