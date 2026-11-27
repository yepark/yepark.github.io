---
title: "SwiftData로 데이터 저장하기"
description: "iOS 17부터 쓸 수 있는 SwiftData로 앱 데이터를 저장하는 방법을 설명합니다. @Model, ModelContainer, ModelContext, @Query와 #Predicate, 관계와 삭제 규칙, 백그라운드 작업, 스키마 마이그레이션, Core Data와의 관계를 할 일 앱 예제로 다룹니다."
parent: SwiftUI
nav_order: 8
permalink: /swiftui/swiftdata/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [SwiftUI, SwiftData, Persistence, iOS17]
---

# SwiftData로 데이터 저장하기
{: .no_toc }

{% include article-toc.md %}

할 일 앱을 껐다 켜도 목록이 남아 있어야 한다. iOS에서 앱 데이터를 저장하는 전통적인 방법은 [Core Data]({{ '/ios/core-data-swift/' | relative_url }})였지만, 모델 편집기와 `NSManagedObject`, 컨텍스트 설정이 SwiftUI와 어울리지 않는 부분이 많았다.

**SwiftData**는 iOS 17·macOS 14부터 제공되는 데이터 저장 프레임워크다. Swift 클래스에 `@Model`만 붙이면 저장할 수 있는 모델이 되고, SwiftUI 뷰에서 `@Query`로 바로 읽는다. 내부적으로 Core Data의 저장 기술을 쓰지만, API는 Swift 매크로와 SwiftUI에 맞게 새로 만들어졌다.

이 글을 쓴 환경에는 Xcode가 없어 예제를 직접 빌드하지 못했다. API 이름은 Apple의 SwiftData 문서를 기준으로 했다.

## 모델 정의: @Model

```swift
import SwiftData
import Foundation

@Model
final class TodoItem {
    var title: String
    var isDone: Bool
    var createdAt: Date

    init(title: String) {
        self.title = title
        self.isDone = false
        self.createdAt = .now
    }
}
```

`@Model` 매크로가 저장에 필요한 코드를 대신 만든다. Core Data처럼 별도의 모델 파일(`.xcdatamodeld`)이 필요 없고, Swift 클래스가 곧 스키마다. `@Model`은 클래스에만 붙일 수 있다. SwiftData가 객체의 변경을 추적해야 하므로 참조 타입이어야 하기 때문이다([값 타입과 참조 타입]({{ '/swift/struct-class/' | relative_url }})).

`@Model` 클래스는 `@Observable`처럼 동작해서, 뷰가 읽은 프로퍼티가 바뀌면 그 뷰만 다시 그려진다([상태와 데이터 흐름]({{ '/swiftui/state/' | relative_url }})).

## 컨테이너와 컨텍스트

| 타입 | 역할 | Core Data의 대응 |
| --- | --- | --- |
| `ModelContainer` | 저장소를 열고 스키마를 관리 | `NSPersistentContainer` |
| `ModelContext` | 객체를 추가·삭제하고 변경을 추적·저장하는 작업 공간 | `NSManagedObjectContext` |
| `@Model` 객체 | 저장되는 데이터 하나 | `NSManagedObject` |

앱 진입점에서 컨테이너를 만들어 뷰 계층에 넣는다.

```swift
import SwiftUI
import SwiftData

@main
struct TodoApp: App {
    var body: some Scene {
        WindowGroup {
            TodoListView()
        }
        .modelContainer(for: TodoItem.self)
    }
}
```

`.modelContainer(for:)`는 컨테이너를 만들고, 메인 스레드용 컨텍스트를 환경(`@Environment(\.modelContext)`)에 넣어 준다.

## 읽기: @Query

```swift
struct TodoListView: View {
    @Environment(\.modelContext) private var context
    @Query(sort: \TodoItem.createdAt, order: .reverse) private var todos: [TodoItem]
    @State private var newTitle = ""

    var body: some View {
        NavigationStack {
            List {
                ForEach(todos) { todo in
                    Toggle(todo.title, isOn: Binding(
                        get: { todo.isDone },
                        set: { todo.isDone = $0 }
                    ))
                }
                .onDelete { offsets in
                    for index in offsets {
                        context.delete(todos[index])
                    }
                }
            }
            .safeAreaInset(edge: .bottom) {
                HStack {
                    TextField("할 일", text: $newTitle)
                    Button("추가") {
                        context.insert(TodoItem(title: newTitle))
                        newTitle = ""
                    }
                    .disabled(newTitle.trimmingCharacters(in: .whitespaces).isEmpty)
                }
                .padding()
            }
            .navigationTitle("할 일")
        }
    }
}
```

- `@Query`는 저장소를 조회해 배열로 주고, 데이터가 바뀌면 자동으로 다시 조회해 화면을 갱신한다. 정렬은 키 경로(`\TodoItem.createdAt`)로 지정한다.
- 추가는 `context.insert`, 삭제는 `context.delete`다.
- 토글로 `todo.isDone`을 바꾸면 그것만으로 변경이 추적된다.
- **`save()`를 부르지 않았다.** 메인 컨텍스트는 기본적으로 자동 저장(`autosaveEnabled`)이 켜져 있어, UI 이벤트나 앱이 백그라운드로 갈 때 저장한다. 바로 저장해야 하는 경우에는 `try context.save()`를 직접 부른다.

## 조건으로 거르기: #Predicate

```swift
@Query(filter: #Predicate<TodoItem> { !$0.isDone },
       sort: \TodoItem.createdAt)
private var remaining: [TodoItem]
```

`#Predicate`는 Swift 클로저처럼 조건을 쓰면 컴파일 시점에 검사하고 저장소 쿼리로 바꿔 준다. Core Data의 `NSPredicate(format: "isDone == NO")`처럼 문자열로 쓰지 않으므로, 프로퍼티 이름을 틀리면 컴파일 오류가 난다. 다만 클로저 안에서 쓸 수 있는 연산은 저장소 쿼리로 바꿀 수 있는 것으로 제한된다.

뷰 밖(서비스, 테스트)에서 조회할 때는 `FetchDescriptor`를 쓴다.

```swift
let descriptor = FetchDescriptor<TodoItem>(
    predicate: #Predicate { $0.title.contains("장보기") },
    sortBy: [SortDescriptor(\.createdAt)]
)
let found = try context.fetch(descriptor)
let count = try context.fetchCount(FetchDescriptor<TodoItem>())
```

## 관계와 삭제 규칙

할 일을 프로젝트로 묶어 보자.

```swift
@Model
final class Project {
    var name: String
    @Relationship(deleteRule: .cascade, inverse: \TodoItem.project)
    var items: [TodoItem] = []

    init(name: String) { self.name = name }
}

// TodoItem에 추가
// var project: Project?
```

`deleteRule: .cascade`는 프로젝트를 지우면 그 안의 할 일도 함께 지운다. 기본값 `.nullify`는 할 일을 남기고 `project`만 `nil`로 만든다. Core Data의 Delete Rule과 같은 개념이다. 관계 하나를 바꾸면 반대쪽(`inverse`)도 SwiftData가 맞춰 준다.

## 무거운 작업은 백그라운드에서

수천 건을 가져와 저장하는 작업을 메인 컨텍스트에서 하면 화면이 멈춘다. `@ModelActor`로 자기만의 컨텍스트를 가진 actor를 만든다.

```swift
@ModelActor
actor TodoImporter {
    func importTitles(_ titles: [String]) throws {
        for title in titles {
            modelContext.insert(TodoItem(title: title))
        }
        try modelContext.save()
    }
}

// 사용
let importer = TodoImporter(modelContainer: container)
try await importer.importTitles(titles)
```

`@Model` 객체는 자신이 속한 컨텍스트의 actor에 묶여 있어 다른 actor로 넘기면 안 된다. 대신 `PersistentIdentifier`(`todo.persistentModelID`)를 넘기고 받은 쪽 컨텍스트에서 다시 조회한다. Core Data에서 `NSManagedObjectID`를 넘기던 것과 같은 원칙이다. 백그라운드에서 저장한 변경은 메인 컨텍스트의 `@Query`에 자동으로 반영된다.

## 모델이 바뀌면: 마이그레이션

출시 후 모델에 프로퍼티를 추가하면, 기존 사용자의 저장소는 옛 모양이다. 기본값이 있는 프로퍼티 추가나 이름 변경(`@Attribute(originalName: "oldName")`) 같은 간단한 변경은 SwiftData가 자동으로 옮긴다(가벼운 마이그레이션). 데이터 변환이 필요한 변경은 버전별 스키마(`VersionedSchema`)와 단계(`SchemaMigrationPlan`)를 정의해 직접 옮긴다.

```swift
enum SchemaV1: VersionedSchema {
    static let versionIdentifier = Schema.Version(1, 0, 0)
    static var models: [any PersistentModel.Type] { [TodoItem.self] }
    // ...
}
```

출시 후에는 "앱을 지우고 다시 설치"로 해결할 수 없으므로, 모델을 바꿀 때마다 이전 버전 데이터로 업데이트를 시험한다.

## 테스트와 미리보기: 메모리 저장소

```swift
let container = try ModelContainer(
    for: TodoItem.self,
    configurations: ModelConfiguration(isStoredInMemoryOnly: true)
)
let context = ModelContext(container)
context.insert(TodoItem(title: "테스트"))
```

메모리에만 저장하는 컨테이너를 쓰면 테스트끼리 데이터가 섞이지 않고, `#Preview`에서도 예시 데이터를 넣어 화면을 확인할 수 있다.

## Core Data와 무엇을 고를까

| | SwiftData | Core Data |
| --- | --- | --- |
| 최소 OS | iOS 17 | iOS 3부터 |
| 모델 정의 | Swift 클래스 + `@Model` | 모델 편집기 + `NSManagedObject` |
| SwiftUI 연동 | `@Query`, 자동 관찰 | `@FetchRequest` |
| 조건 | `#Predicate` (컴파일 검사) | `NSPredicate` (문자열) |
| 성숙도 | 새로움. 고급 기능 일부 부족 | 오래 검증됨. 세밀한 제어 가능 |

iOS 17 이상만 지원하는 새 SwiftUI 앱이라면 SwiftData로 시작할 만하다. iOS 16 이하를 지원해야 하거나, 이미 Core Data를 쓰고 있거나, 복잡한 마이그레이션·대량 일괄 처리처럼 세밀한 제어가 필요하면 Core Data가 낫다. 둘은 같은 저장소 파일을 함께 쓸 수도 있어 단계적으로 옮기는 것도 가능하다.

## 정리

- SwiftData는 iOS 17부터 쓰는 Swift 중심의 저장 프레임워크로, `@Model` 클래스가 곧 스키마다.
- `ModelContainer`가 저장소를, `ModelContext`가 변경 추적과 저장을 맡는다. 메인 컨텍스트는 자동 저장된다.
- SwiftUI에서는 `@Query`로 조회하고 데이터가 바뀌면 화면이 자동 갱신된다. 조건은 `#Predicate`로 컴파일 시점에 검사한다.
- 관계는 `@Relationship`과 삭제 규칙으로, 백그라운드 작업은 `@ModelActor`와 `PersistentIdentifier`로 다룬다.
- 모델 변경은 가벼운 마이그레이션이나 `VersionedSchema`로 옮긴다.

## 이어서 읽기

- 이전 글: [UIKit 연동과 미리보기]({{ '/swiftui/uikit-preview/' | relative_url }})
- [Core Data 아키텍처와 Swift 구현]({{ '/ios/core-data-swift/' | relative_url }})
- [SwiftUI 연재 목차]({{ '/swiftui/' | relative_url }})

## 참고

- [Apple: SwiftData](https://developer.apple.com/documentation/swiftdata)
- [Apple: Preserving your app's model data across launches](https://developer.apple.com/documentation/swiftdata/preserving-your-apps-model-data-across-launches)
- [WWDC23: Meet SwiftData](https://developer.apple.com/videos/play/wwdc2023/10187/)
- [WWDC23: Model your schema with SwiftData](https://developer.apple.com/videos/play/wwdc2023/10195/)
