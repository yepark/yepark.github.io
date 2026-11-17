---
title: "Siri AI와 App Intents: 앱의 기능을 Siri에 연결하기"
description: "Apple Intelligence와 Siri AI의 App Intent, App Entity, 검색, 스키마와 화면 문맥을 초보자용 Swift 예제로 설명합니다."
parent: iOS
nav_order: 21
permalink: /ios/siri-ai-app-intents/
last_modified_date: 2026-11-17
---

# Siri AI와 App Intents: 앱의 기능을 Siri에 연결하기
{: .no_toc }

{% include article-toc.md %}

사용자가 Siri에게 ‘내 메모 앱에서 미완료 메모 개수 알려 줘’라고 말했다고 하자. 시스템이 요청을 이해하더라도 앱이 데이터를 읽는 기능을 공개하지 않았다면 원하는 결과를 얻기 어렵다. App Intents는 앱의 행동과 데이터를 시스템이 사용할 수 있는 형태로 설명하는 프레임워크다.

이 글의 기본 코드는 iOS 16부터 제공되는 App Intents의 개념을 사용한다. Apple의 최신 문서에 포함된 Siri AI Developer Preview와 추가 시스템 연동 기능은 별도의 배포 상태·SDK·지원 조건을 확인해야 한다. 기본 Intent 구현만으로 모든 자연어 요청이 모든 OS에서 실행되는 것은 아니다.

## Foundation Models와 역할 구분하기

| 원하는 기능 | 주로 사용하는 API |
| --- | --- |
| 앱 안의 문장을 요약한다 | Foundation Models |
| 앱의 검색·생성·완료 처리를 Siri나 단축어에 공개한다 | App Intents |
| 특정 메모를 시스템이 식별하게 한다 | AppEntity와 Query |
| 앱 콘텐츠를 검색할 수 있게 한다 | Spotlight 연동 |

둘은 함께 사용할 수 있다. Intent가 사용자의 메모를 찾고, 앱의 서비스가 Foundation Models로 요약한 뒤 결과를 돌려주는 식이다. 시스템 진입점과 모델 생성 로직을 구분하면 테스트하기 쉽다.

## 핵심 용어 먼저 익히기

- `AppIntent`: ‘메모 추가’, ‘운동 시작’ 같은 행동
- `@Parameter`: 행동에 필요한 입력값
- `perform()`: 실제 앱 코드를 실행하는 메서드
- `AppEntity`: 메모·사진·프로젝트처럼 시스템에 설명할 데이터
- `EntityQuery`: ID나 검색어를 실제 앱 데이터로 바꾸는 조회 규칙
- `AppShortcutsProvider`: 미리 구성한 단축어와 호출 표현을 제공하는 타입

Core Data의 `NSManagedObject`를 그대로 Siri에 공개하는 대신 안정적인 ID와 표시 이름을 가진 `AppEntity`로 표현하는 것이 이해하기 쉽다. 저장 방식은 앱 내부 책임으로 유지한다.

## 가장 작은 Intent 만들기

처음에는 DB 없이 결과를 반환하는 행동부터 연결해 보자.

```swift
import AppIntents

struct ExplainAppIntent: AppIntent {
    static var title: LocalizedStringResource = "앱 사용법 안내"
    static var description = IntentDescription("메모 앱의 기본 사용법을 알려 줍니다.")

    func perform() async throws -> some IntentResult & ProvidesDialog {
        .result(dialog: "새 메모를 만들고 완료 상태를 관리할 수 있어요.")
    }
}
```

이 예제는 시스템에 행동 이름을 알려 주고, 실행되면 안내문을 반환한다. `ProvidesDialog`는 시스템이 사용자에게 보여 주거나 말할 수 있는 응답을 제공한다는 뜻이다. 앱 데이터 변경은 포함하지 않는다.

## 입력값이 있는 행동

```swift
struct EchoMemoTitleIntent: AppIntent {
    static var title: LocalizedStringResource = "메모 제목 확인"

    @Parameter(title: "제목")
    var memoTitle: String

    func perform() async throws -> some IntentResult & ProvidesDialog {
        let title = memoTitle.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !title.isEmpty else {
            return .result(dialog: "빈 제목은 사용할 수 없어요.")
        }
        return .result(dialog: "입력한 제목은 \(title)입니다.")
    }
}
```

`@Parameter`는 시스템이 사용자 입력을 받아 채울 값이다. 실제 저장 기능을 만들려면 검증 이후 앱의 저장 서비스를 호출한다. Intent에 DB 구현을 전부 넣으면 화면과 Siri가 서로 다른 저장 규칙을 갖게 될 수 있다. 두 진입점 모두 같은 서비스를 사용하도록 구성한다.

## App Shortcut으로 호출 경로 제공하기

```swift
struct MemoShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: ExplainAppIntent(),
            phrases: ["\(.applicationName) 사용법 알려 줘"],
            shortTitle: "사용법 안내",
            systemImageName: "note.text"
        )
    }
}
```

`applicationName` 자리에는 시스템이 앱 이름을 연결한다. 예제 문구를 출발점으로 삼아 실제 앱의 표시 이름과 지역화에 맞는 표현을 제공한다. 앱을 설치한 뒤 단축어 앱에서 행동을 먼저 실행해 보고, Siri 호출을 시험하면 코드 실행 문제와 음성 인식 문제를 나눠 확인할 수 있다.

## App Entity와 Query는 왜 필요할까

‘어제 쓴 여행 메모를 열어 줘’라는 요청에는 행동뿐 아니라 특정 메모를 고르는 과정도 필요하다.

```text
사용자 표현
  → 후보 메모 검색
  → 후보가 여러 개면 선택
  → 안정적인 메모 ID 확정
  → 해당 메모를 열거나 처리
```

Entity에는 ‘여행 메모’라는 이름과 고유 ID를 표현한다. Query는 그 ID를 현재 저장소의 레코드로 바꾼다. 메모가 삭제됐거나 접근 권한이 바뀌었다면 조회 실패로 처리해야 한다. 사용자의 자연어 제목만으로 다른 메모를 임의 선택하지 않는다.

## 최신 Siri AI 연동에서 추가되는 요소

Apple의 안내는 행동과 데이터 공개를 바탕으로 다음 요소를 함께 설명한다.

| 요소 | 필요한 이유 | 메모 앱의 예 |
| --- | --- | --- |
| Spotlight 인덱싱 | 콘텐츠를 검색할 수 있게 함 | ‘여행 관련 메모’ 찾기 |
| Transferable 표현 | 앱 사이에 콘텐츠 전달 | 메모 텍스트를 다른 작업에 넘기기 |
| 시스템 스키마 | 행동의 의미를 공통 구조로 표현 | 알려진 생성·열기 동작에 맞추기 |
| 화면 문맥 연결 | 화면의 대상을 Entity와 연결 | ‘이 메모’가 가리키는 항목 확인 |
| Donation | 사용 행동을 시스템에 알림 | 자주 실행하는 작업의 발견 보조 |

화면 문맥은 스크린샷을 보고 DB 내용을 모두 알아내는 기능으로 이해하면 안 된다. 앱이 화면에 보이는 항목과 Entity의 관계를 제공해야 한다. Donation도 임의의 개인정보 전체를 업로드하라는 뜻으로 해석하지 말고 각 API의 데이터 범위를 확인한다.

## Core Data와 연결하는 순서

먼저 화면에서 호출하는 메모 조회 서비스를 만든다. Intent에서도 같은 서비스를 사용하고, Query는 메모 ID로 조회한다. 실제 `NSManagedObject` 접근은 해당 context의 큐 규칙을 따른다. Intent는 앱 화면과 별도 실행 환경에서 호출될 수 있으므로 전역 화면 객체가 이미 만들어져 있다고 가정하지 않는다.

외부에 전달할 값은 ID, 제목, 필요한 텍스트처럼 범위가 분명한 형태로 변환한다. 잠금 상태에서 민감한 내용을 읽을 수 있는지도 인증 정책과 함께 검토한다.

## 구현 후 어떻게 확인할까

1. Intent를 포함한 앱 타깃이 빌드되는지 확인한다.
2. 설치 후 단축어에서 행동이 보이는지 확인한다.
3. 입력값이 없는 경우와 빈 문자열을 각각 시험한다.
4. 존재하지 않는 Entity ID를 전달했을 때 실패 처리를 확인한다.
5. Siri의 언어와 앱 지역화에 맞는 호출 문구를 시험한다.
6. 최신 Siri AI 기능은 해당 Developer Preview의 조건과 기기에서 별도로 검증한다.

이 글의 예제는 기본 연결 구조를 설명한다. 최신 Siri AI의 전체 기능을 구현한 샘플은 아니며, 기기에서 음성 실행을 검증한 것으로 간주하면 안 된다.

## 이어서 읽기

- [Foundation Models로 앱 안에서 AI 응답 생성하기]({{ '/ios/foundation-models/' | relative_url }})
- [Core Data의 객체와 context 이해하기]({{ '/ios/core-data-swift/' | relative_url }})

## 참고

- [Apple: Apple Intelligence and Siri AI](https://developer.apple.com/documentation/appintents/apple-intelligence-and-siri-ai)
- [Apple: AppIntent](https://developer.apple.com/documentation/appintents/appintent)
- [Apple: AppShortcutsProvider](https://developer.apple.com/documentation/appintents/appshortcutsprovider)
