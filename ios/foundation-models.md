---
title: "Foundation Models"
description: "Apple Foundation Models의 모델 가용성, LanguageModelSession, 구조화 생성과 스트리밍을 Swift 입문 예제로 설명합니다."
parent: iOS
nav_order: 20
permalink: /ios/foundation-models/
date: 2026-11-17
last_modified_at: 2026-11-17
seo:
  type: BlogPosting
last_modified_date: 2026-11-17
---

# Foundation Models
{: .no_toc }

{% include article-toc.md %}

메모 앱에 ‘세 문장으로 요약하기’ 버튼을 만든다고 생각해 보자. 사용자가 쓴 글을 읽고 짧은 설명을 만드는 부분에 언어 모델을 사용할 수 있다. Apple의 Foundation Models 프레임워크는 Apple Intelligence의 온디바이스 모델을 Swift 코드에서 호출하는 통로다.

이 글은 iOS 26에서 도입된 기본 텍스트 생성 API를 기준으로 설명한다. 새 SDK에는 추가 기능이 있을 수 있으므로, 사용하는 Xcode의 심벌 가용성도 함께 확인한다.

## 예제의 준비 범위

Swift의 함수와 `Task`, `try await` 문법을 먼저 알고 있으면 모델 호출 부분을 읽기 쉽다. Foundation Models는 시스템 SDK이므로 앱 타깃에서 `import FoundationModels`로 사용한다.

AI가 반환하는 요약은 매번 문장이 달라질 수 있다. 예제를 확인할 때는 특정 문장과 완전히 일치하는지보다, 원문 사실을 보존하는지와 요청한 구조를 지키는지를 먼저 살펴보자.

## Foundation과 Foundation Models 구분하기

| 이름 | 역할 | 예 |
| --- | --- | --- |
| Foundation | 날짜·문자열·파일·네트워크 같은 기본 기능 | `Date`, `URL`, `URLSession` |
| Foundation Models | 시스템 생성형 모델 사용 | `LanguageModelSession` |
| Core ML | 준비한 ML 모델을 앱에서 실행 | 이미지 분류 모델 |
| MLX | 배열 연산과 모델 계산을 직접 구성 | 모델 학습·추론 코드 |
| App Intents | 앱 기능을 시스템에 공개 | Siri로 메모 검색 |

서버로 직접 요청하는 API와 달리 시스템 온디바이스 모델의 추론은 기기에서 수행된다. 다만 앱이 별도로 실행하는 네트워크 요청이나 Tool의 서버 호출까지 자동으로 오프라인이 되는 것은 아니다.

## 실행하기 전에 확인할 조건

OS 버전만으로 실행 가능 여부를 판단하지 않는다. Apple Intelligence 지원 기기인지, 기능이 활성화돼 있는지, 모델 준비가 끝났는지, 지원 지역과 언어 조건을 만족하는지 확인해야 한다.

```swift
import FoundationModels

@available(iOS 26.0, *)
func modelStatus() -> String {
    switch SystemLanguageModel.default.availability {
    case .available:
        return "요약 기능을 사용할 수 있어요."
    case .unavailable(.deviceNotEligible):
        return "이 기기에서는 요약 기능을 지원하지 않아요."
    case .unavailable(.appleIntelligenceNotEnabled):
        return "설정에서 Apple Intelligence를 활성화해 주세요."
    case .unavailable(.modelNotReady):
        return "모델을 준비 중이에요. 잠시 후 다시 시도해 주세요."
    case .unavailable:
        return "현재 AI 기능을 사용할 수 없어요."
    }
}
```

`SystemLanguageModel.default`는 시스템이 제공하는 기본 모델을 뜻한다. `availability`는 지금 사용할 수 있는지 나타내는 상태다. 사용할 수 없다면 AI 버튼을 비활성화하고 기존 메모 읽기·편집 기능은 계속 제공한다.

## 첫 번째 응답 만들기

```swift
@available(iOS 26.0, *)
func summarize(_ text: String) async throws -> String {
    let session = LanguageModelSession(
        instructions: "제공된 글만 근거로 한국어 세 문장으로 요약하세요."
    )

    let response = try await session.respond(to: text)
    return response.content
}
```

실행 흐름은 ‘대화 세션 생성 → 원문 전달 → 응답 기다리기 → 문자열 꺼내기’다.

- `instructions`: 이 세션에서 지킬 역할과 출력 기준
- `respond(to:)`: 이번에 처리할 입력을 전달하는 메서드
- `await`: 생성이 끝날 때까지 현재 비동기 함수가 중단될 수 있다는 표시
- `try`: 생성 과정에서 오류가 발생할 수 있다는 표시
- `content`: 실제 응답 내용

이 함수는 호출 전에 모델 가용성을 확인했다고 가정한다. 가용성 확인 뒤에도 상태가 변하거나 생성이 실패할 수 있으므로 호출부에서는 `do`/`catch`로 오류를 처리해야 한다.

## SwiftUI 버튼에 연결하기

```swift
import SwiftUI
import FoundationModels

@available(iOS 26.0, *)
struct SummaryView: View {
    @State private var source = "오늘 배운 내용을 입력하세요."
    @State private var answer = ""
    @State private var isLoading = false

    var body: some View {
        VStack(spacing: 16) {
            TextEditor(text: $source)
                .frame(height: 160)
            Button(isLoading ? "요약 중…" : "요약하기") {
                Task { @MainActor in
                    isLoading = true
                    defer { isLoading = false }
                    do {
                        answer = try await summarize(source)
                    } catch {
                        answer = "요약에 실패했어요. 입력을 줄여 다시 시도해 주세요."
                    }
                }
            }
            .disabled(isLoading || source.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
                || SystemLanguageModel.default.availability != .available)
            Text(answer)
        }
        .padding()
    }
}
```

`isLoading`은 중복 요청을 막는 상태다. `defer`는 성공과 실패 어느 경로로 끝나도 로딩 상태를 해제한다. 이 예제는 버튼 연결에 집중한 것이므로, 화면을 닫았을 때 Task를 취소하는 처리와 가용성에 따른 상세 안내는 앱에서 추가한다.

## 세션을 언제 재사용할까

서로 관련된 후속 질문에는 같은 세션을 사용한다. 앞 응답을 바탕으로 ‘더 짧게 바꿔 줘’라고 요청할 수 있다. 서로 다른 메모를 독립적으로 요약한다면 매번 새 세션을 만드는 편이 문맥 혼입을 줄인다.

세션에는 입력과 응답 이력이 쌓인다. 무한한 기억 공간으로 생각하면 안 된다. 대화가 길어지면 필요한 사실을 정리해 새 세션으로 넘기는 방식이 필요하다. 같은 세션에 여러 생성 요청을 겹치지 않도록 화면이나 서비스 계층에서 요청을 직렬화한다.

## 문자열 대신 Swift 타입으로 받기

제목과 요약을 따로 표시해야 한다면 긴 문자열을 직접 쪼개기보다 생성할 타입을 선언할 수 있다.

```swift
@available(iOS 26.0, *)
@Generable
struct NoteSummary {
    @Guide(description: "메모 내용을 나타내는 짧은 제목")
    var title: String

    @Guide(description: "원문에 근거한 두 문장 요약")
    var summary: String
}

@available(iOS 26.0, *)
func summarizeAsData(_ text: String) async throws -> NoteSummary {
    let session = LanguageModelSession()
    let response = try await session.respond(
        to: "다음 메모를 정리하세요: \(text)",
        generating: NoteSummary.self
    )
    return response.content
}
```

`@Generable`은 모델이 생성할 데이터 구조를 프레임워크에 알린다. `@Guide`는 각 필드의 의미를 설명한다. 반환값은 `NoteSummary`이므로 `result.title`처럼 바로 접근할 수 있다. 구조를 지킨다는 보장과 내용이 사실이라는 보장은 다르다. 원문에 없는 날짜나 이름을 만들었는지도 검토해야 한다.

## 스트리밍으로 기다림 줄이기

```swift
let session = LanguageModelSession()
let stream = session.streamResponse(to: "직렬 큐를 두 문장으로 설명하세요.")

for try await snapshot in stream {
    print(snapshot.content)
}
```

스트리밍은 응답 전체가 끝나기 전에 중간 결과를 받는 방식이다. Foundation Models는 누적된 상태를 나타내는 snapshot을 전달한다. 화면에서는 새 snapshot의 내용으로 교체한다. 매번 뒤에 붙이면 앞서 생성한 문장이 중복될 수 있다.

## Tool은 어떤 일을 할까

모델이 앱의 실제 데이터가 필요할 때 호출하도록 개발자가 제공하는 기능이다. 예를 들어 ‘내 미완료 메모를 찾아서 요약하기’에는 메모 조회 Tool이 필요하다. 모델이 Core Data나 서버 DB를 스스로 알고 있는 것은 아니다.

Tool은 입력을 검증하고 앱의 데이터 계층을 통해 작업한 뒤 결과를 반환한다. 조회에는 읽기 기능만 제공하고, 수정·발송처럼 사용자의 데이터가 바뀌는 작업에는 확인 절차를 붙인다. 구체적인 Tool 구현은 사용하는 SDK의 `Tool` 프로토콜 정의를 따른다.

## 앱에 넣을 때 확인할 것

긴 원문은 구간별로 요약한 뒤 합치는 방법을 고려한다. 오류를 무조건 같은 입력으로 반복 호출하지 말고 모델 미준비, 입력 길이, 생성 거절 등을 구분한다. 로그에는 사용자의 메모 원문을 그대로 남기지 않는다.

이 환경의 Xcode는 Swift 6.0.3이라 Foundation Models 예제를 컴파일하지 못했다. 예제는 Apple 문서의 기본 API 구조를 기준으로 작성했으며, Xcode 26 이상과 지원 기기에서 생성 결과·한국어 품질·취소 동작을 검증해야 한다.

## 이어서 읽기

- [Siri AI와 App Intents]({{ '/ios/siri-ai-app-intents/' | relative_url }})
- [Core Data 아키텍처와 Swift 구현]({{ '/ios/core-data-swift/' | relative_url }})

## 참고

- [Apple: Generating content and performing tasks](https://developer.apple.com/documentation/foundationmodels/generating-content-and-performing-tasks-with-foundation-models)
- [Apple: Guided generation](https://developer.apple.com/documentation/foundationmodels/generating-swift-data-structures-with-guided-generation)
- [Apple: Meet the Foundation Models framework](https://developer.apple.com/videos/play/wwdc2025/286/)
