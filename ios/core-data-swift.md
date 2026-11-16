---
title: "Swift Core Data 사용법과 핵심 클래스"
description: "Swift Core Data의 핵심 클래스와 CRUD, 관계, 백그라운드 컨텍스트, batch 작업, migration을 자세히 설명합니다."
parent: "iOS"
nav_order: 5
permalink: /ios/core-data-swift/
first_written: 2026-11-16
last_modified_date: 2026-11-16
tags: [iOS, Swift, Core-Data]
---

# Swift Core Data 사용법과 핵심 클래스
{: .no_toc }

<details open markdown="block">
  <summary>목차</summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

Core Data는 앱의 객체와 객체 사이 관계를 관리하고, 변경 내용을 추적해 저장소에 보관하는 Apple 프레임워크다. SQLite를 사용할 수 있지만 **SQLite를 Swift 객체로 바꿔 주는 단순 ORM**으로만 이해하면 중요한 기능을 놓친다.

Core Data가 제공하는 대표 기능은 다음과 같다.

- 객체 생성·조회·수정·삭제
- 객체 사이의 일대일·일대다 관계 관리
- 변경 추적과 저장
- Undo/Redo
- 메모리를 아끼기 위한 faulting
- 검증과 제약 조건
- 백그라운드 컨텍스트
- 데이터 모델 버전과 마이그레이션
- CloudKit 연동을 위한 컨테이너

## 가장 먼저 이해할 그림

```text
앱 화면과 비즈니스 로직
          ↓
NSManagedObjectContext  ← 객체를 올려 두고 편집하는 작업 공간
          ↓
NSPersistentStoreCoordinator ← 모델과 저장소를 연결하는 조정자
          ↓
SQLite / In-Memory / Binary 등의 저장소

NSManagedObjectModel ← 엔티티·속성·관계 설계도
NSPersistentContainer ← 위 구성 요소를 편리하게 만들어 주는 상자
```

처음에는 `NSPersistentContainer`, `viewContext`, `NSManagedObject` 세 가지부터 이해하면 된다.

## 핵심 클래스 한눈에 보기

| 클래스 | 쉬운 설명 | 주로 하는 일 |
| --- | --- | --- |
| `NSPersistentContainer` | Core Data 스택 조립 상자 | 모델·컨텍스트·저장소 연결 |
| `NSManagedObjectModel` | 데이터 설계도 | 엔티티·속성·관계 정의 |
| `NSPersistentStoreDescription` | 저장소 설정서 | 위치, 타입, 마이그레이션 옵션 |
| `NSPersistentStoreCoordinator` | 저장소 조정자 | 모델과 실제 저장소 연결 |
| `NSManagedObjectContext` | 객체 작업 공간 | 조회, 변경 추적, 저장, 취소 |
| `NSManagedObject` | 관리되는 데이터 객체 | 엔티티의 실제 인스턴스 |
| `NSEntityDescription` | 엔티티 메타데이터 | 새 객체 생성, 엔티티 정보 조회 |
| `NSFetchRequest` | 조회 요청서 | 필터, 정렬, 개수, 가져올 범위 정의 |
| `NSFetchedResultsController` | 목록 변경 관찰자 | 조회 결과와 UIKit 목록 연결 |
| `NSManagedObjectID` | 객체의 안전한 식별자 | 컨텍스트·큐 사이에서 객체 식별 |

## 데이터 모델 만들기

Xcode에서 `.xcdatamodeld` 파일을 열고 Entity를 추가한다. 예제로 `TaskItem`을 만든다.

| 이름 | 타입 | Optional | 설명 |
| --- | --- | --- | --- |
| `id` | UUID | No | 앱에서 사용하는 식별자 |
| `title` | String | No | 할 일 제목 |
| `isDone` | Boolean | No | 완료 여부 |
| `createdAt` | Date | No | 생성 시각 |

Entity의 Codegen을 `Class Definition`으로 두면 Xcode가 `NSManagedObject` 하위 클래스를 자동 생성한다. 직접 파일을 생성할 때는 Codegen을 `Manual/None`으로 맞춰 중복 클래스가 생기지 않게 한다.

자동 생성 클래스를 Swift에서 다음처럼 사용한다고 가정한다.

```swift
@objc(TaskItem)
public class TaskItem: NSManagedObject {}

extension TaskItem {
    @NSManaged public var id: UUID
    @NSManaged public var title: String
    @NSManaged public var isDone: Bool
    @NSManaged public var createdAt: Date
}
```

`@NSManaged` 프로퍼티의 실제 저장과 변경 추적은 Core Data 런타임이 담당한다.

## NSPersistentContainer: 스택 만들기

모델 파일 이름이 `AppData.xcdatamodeld`라면 컨테이너 이름도 `AppData`로 맞춘다.

```swift
import CoreData

final class CoreDataStack {
    static let shared = CoreDataStack()

    let container: NSPersistentContainer

    init(inMemory: Bool = false) {
        container = NSPersistentContainer(name: "AppData")

        if inMemory {
            let description = NSPersistentStoreDescription()
            description.type = NSInMemoryStoreType
            container.persistentStoreDescriptions = [description]
        }

        container.loadPersistentStores { description, error in
            if let error {
                assertionFailure("Core Data 저장소 로드 실패: \(error)")
            }
        }

        container.viewContext.automaticallyMergesChangesFromParent = true
        container.viewContext.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy
    }
}
```

### `loadPersistentStores`는 무엇을 할까

데이터 모델과 실제 저장소를 연결한다. SQLite 파일이 필요하면 만들고, 기존 저장소가 현재 모델과 호환되는지도 확인한다. 이 작업이 끝나기 전에 컨텍스트를 사용해 앱의 초기 데이터를 읽지 않도록 초기화 순서를 관리한다.

실제 앱에서 오류를 무조건 무시하거나 저장소 파일을 삭제해 다시 만드는 것은 사용자 데이터 손실로 이어질 수 있다. 개발 중 오류와 운영 복구 정책을 구분한다.

## NSManagedObjectContext: 가장 중요한 작업 공간

컨텍스트는 단순한 DB 연결이 아니다. 불러온 객체를 기억하고, 변경을 추적하고, 저장 전 검증하며, Undo와 충돌 해결을 담당하는 **객체 그래프 작업 공간**이다.

```swift
let context = CoreDataStack.shared.container.viewContext
```

`viewContext`는 메인 큐용 컨텍스트다. 화면에 표시할 객체를 다룰 때 사용한다.

### 저장 전과 저장 후

```swift
task.title = "Core Data 공부"

print(context.hasChanges) // true

try context.save()

print(context.hasChanges) // false
```

프로퍼티를 바꾸는 순간 SQLite에 바로 쓰는 것이 아니다. 컨텍스트 안에서 변경을 추적하고 `save()`할 때 영구 저장소로 보낸다.

## Create: 새 객체 저장하기

```swift
func createTask(title: String, in context: NSManagedObjectContext) throws {
    let task = TaskItem(context: context)
    task.id = UUID()
    task.title = title
    task.isDone = false
    task.createdAt = Date()

    try context.save()
}
```

`TaskItem(context:)`를 호출하면 객체가 해당 컨텍스트에 삽입된 상태가 된다. 필수 속성을 채우지 않으면 저장 시 검증 오류가 날 수 있다.

여러 객체를 한 번에 만들 때마다 `save()`하지 말고 의미 있는 작업 단위가 끝났을 때 저장한다. 하지만 너무 많은 변경을 한 컨텍스트에 오래 쌓으면 메모리가 커질 수 있다.

## Read: 조회하기

```swift
func fetchTasks(in context: NSManagedObjectContext) throws -> [TaskItem] {
    let request = TaskItem.fetchRequest()

    request.predicate = NSPredicate(format: "isDone == NO")
    request.sortDescriptors = [
        NSSortDescriptor(keyPath: \TaskItem.createdAt, ascending: false)
    ]
    request.fetchLimit = 100

    return try context.fetch(request)
}
```

### NSFetchRequest의 주요 설정

- `predicate`: 어떤 객체를 가져올지 필터
- `sortDescriptors`: 결과 순서
- `fetchLimit`: 최대 개수
- `fetchOffset`: 건너뛸 개수
- `fetchBatchSize`: 한꺼번에 메모리에 실체화할 묶음 크기
- `propertiesToFetch`: 사전 결과 등 특정 속성만 가져올 때 사용
- `resultType`: 관리 객체, object ID, dictionary, count 등 결과 형태

`fetchBatchSize`와 페이지 번호 방식은 같은 개념이 아니다. 배치 크기는 조회 결과 컬렉션을 다루면서 필요한 객체를 묶음으로 실체화해 메모리를 관리하는 힌트다.

## Update: 객체 수정하기

```swift
func complete(_ task: TaskItem, in context: NSManagedObjectContext) throws {
    task.isDone = true
    try context.save()
}
```

객체는 자신을 가져온 컨텍스트에 속한다. 함수 인자의 `context`와 `task.managedObjectContext`가 다르지 않은지 확인한다.

저장하지 않고 변경을 되돌리려면 개별 객체에는 `refresh(_:mergeChanges:)`, 컨텍스트 전체에는 `rollback()`을 사용할 수 있다. `reset()`은 등록된 모든 객체를 무효화하므로 기존 참조 사용에 주의한다.

## Delete: 객체 삭제하기

```swift
func delete(_ task: TaskItem, in context: NSManagedObjectContext) throws {
    context.delete(task)
    try context.save()
}
```

`delete`만 호출하면 컨텍스트에서 삭제 예정 상태가 되고, 저장해야 영구 저장소에 반영된다.

관계가 있다면 Data Model의 Delete Rule을 먼저 설계한다.

| Delete Rule | 의미 |
| --- | --- |
| No Action | 관련 객체를 자동 변경하지 않음 |
| Nullify | 상대 관계를 `nil`로 끊음 |
| Cascade | 관련 객체도 함께 삭제 |
| Deny | 관련 객체가 있으면 삭제 거부 |

Cascade는 편리하지만 범위를 잘못 설계하면 많은 사용자 데이터를 한 번에 지울 수 있다.

## 관계 설정하기

`Project`와 여러 `TaskItem`이 있다고 하자.

```text
Project.tasks       to-many
TaskItem.project    to-one
```

두 관계를 inverse로 연결한다. Core Data는 한쪽 변경을 바탕으로 반대쪽 관계도 일관되게 관리한다.

```swift
let project = Project(context: context)
project.name = "블로그"

let task = TaskItem(context: context)
task.title = "Core Data 글 쓰기"
task.project = project

try context.save()
```

관계가 꼭 존재해야 한다면 optional을 끄고 최소 개수를 설정할 수 있다. 앱 코드의 기대와 모델 제약을 맞춘다.

## NSManagedObjectID: 큐 사이에서 객체 전달하기

`NSManagedObject`는 자신이 속한 컨텍스트의 큐에 묶인다. 백그라운드 컨텍스트의 객체를 메인 큐로 직접 넘기면 안 된다. 대신 `NSManagedObjectID`를 넘긴다.

```swift
let objectID = task.objectID

let viewContext = container.viewContext
let taskOnMain = try viewContext.existingObject(with: objectID) as! TaskItem
```

새 객체는 저장 전까지 임시 object ID를 가질 수 있다. 컨텍스트 사이에 전달하기 전에 저장하거나 `obtainPermanentIDs(for:)`로 영구 ID를 얻는다.

## 백그라운드에서 대량 작업하기

```swift
let container = CoreDataStack.shared.container

try await container.performBackgroundTask { context in
    context.mergePolicy = NSMergeByPropertyObjectTrumpMergePolicy

    for index in 0..<1_000 {
        let task = TaskItem(context: context)
        task.id = UUID()
        task.title = "가져온 작업 \(index)"
        task.createdAt = Date()
        task.isDone = false
    }

    try context.save()
}
```

`performBackgroundTask`가 제공한 컨텍스트와 객체는 그 블록의 실행 문맥 안에서 사용한다. 메인 화면 컨텍스트가 변경을 받도록 `automaticallyMergesChangesFromParent`를 설정할 수 있다.

{: .warning }
Swift의 `Task.detached` 안으로 `NSManagedObject`를 캡처한다고 안전해지는 것이 아니다. Core Data의 컨텍스트 `perform` 계열 API와 object ID를 사용한다.

## 충돌과 Merge Policy

메인 컨텍스트와 백그라운드 컨텍스트가 같은 객체를 바꾸면 충돌할 수 있다.

- `NSErrorMergePolicy`: 충돌을 오류로 보고 직접 처리
- `NSMergeByPropertyStoreTrumpMergePolicy`: 저장소 값을 우선
- `NSMergeByPropertyObjectTrumpMergePolicy`: 현재 컨텍스트의 변경 값을 우선
- `NSOverwriteMergePolicy`: 객체 상태로 저장소를 덮음
- `NSRollbackMergePolicy`: 충돌 객체 변경을 되돌림

이름만 보고 전역으로 선택하지 않는다. 오프라인 편집, 서버 동기화, 사용자 입력 중 무엇을 우선할지 도메인 정책을 먼저 정한다.

## NSFetchedResultsController: UIKit 목록과 연결하기

`NSFetchedResultsController`는 fetch 결과를 섹션과 행으로 제공하고, 컨텍스트의 insert·delete·update·move를 delegate에 알려 준다.

```swift
let request = TaskItem.fetchRequest()
request.sortDescriptors = [
    NSSortDescriptor(keyPath: \TaskItem.createdAt, ascending: false)
]

let controller = NSFetchedResultsController(
    fetchRequest: request,
    managedObjectContext: container.viewContext,
    sectionNameKeyPath: nil,
    cacheName: nil
)

controller.delegate = self
try controller.performFetch()
```

최소 하나의 sort descriptor가 필요하다. fetch request의 predicate나 정렬을 바꿀 때 캐시를 사용 중이면 캐시 정책도 함께 처리한다.

SwiftUI에서는 `@FetchRequest`와 `@SectionedFetchRequest`를 사용할 수 있지만, 기반 개념은 fetch request와 context다.

## Fault란 무엇인가

Core Data는 조회한 모든 객체의 속성과 관계를 즉시 메모리에 펼치지 않을 수 있다. 식별 정보만 가진 가벼운 fault 상태로 두고 실제 값에 접근할 때 불러온다.

```text
조회 직후: 객체 ID 중심의 fault
task.title 접근: 필요한 데이터 실체화
```

이 기능이 큰 객체 그래프의 메모리를 줄인다. 디버거에서 객체를 펼치는 것만으로 fault가 발화할 수 있고, 반복문 안에서 관계를 계속 접근하면 많은 추가 조회가 생길 수 있다. 필요하면 prefetch와 fetch batch를 측정 후 사용한다.

## Batch Insert·Update·Delete

수만 건을 일반 `NSManagedObject`로 하나씩 만들면 메모리와 변경 추적 비용이 커진다. Core Data는 저장소에 직접 적용하는 batch request를 제공한다.

- `NSBatchInsertRequest`
- `NSBatchUpdateRequest`
- `NSBatchDeleteRequest`

저장소에 직접 적용된 변경은 현재 컨텍스트의 등록 객체에 자동 반영되지 않을 수 있다. 결과로 object ID를 받고 `NSManagedObjectContext.mergeChanges(fromRemoteContextSave:into:)`로 병합하거나 persistent history를 사용하는 전략이 필요하다.

## Persistent History Tracking

앱 확장, CloudKit, background import처럼 여러 작성자가 같은 저장소를 바꾸면 “마지막으로 본 이후 무엇이 바뀌었는지” 추적할 필요가 있다.

```swift
let description = container.persistentStoreDescriptions.first
description?.setOption(
    true as NSNumber,
    forKey: NSPersistentHistoryTrackingKey
)
description?.setOption(
    true as NSNumber,
    forKey: NSPersistentStoreRemoteChangeNotificationPostOptionKey
)
```

이 설정은 `loadPersistentStores` 전에 해야 한다. 이후 history token을 저장하고 새 transaction만 읽어 관련 변경을 병합한다. 기록은 계속 쌓이므로 모든 소비자가 처리한 범위를 고려해 정리 정책도 만든다.

## 모델 변경과 마이그레이션

출시 후 속성이나 관계를 바꾸면 기존 사용자의 저장소는 이전 모델로 만들어져 있다.

### Lightweight Migration에 잘 맞는 변경

- optional 속성 추가
- 기본값이 있는 속성 추가
- 단순 속성 이름 변경과 renaming identifier 설정
- 일부 단순 관계 변경

`.xcdatamodeld`에서 새 Model Version을 만들고 현재 버전으로 지정한다. 저장소 description에서 자동 마이그레이션과 mapping model 추론을 사용하도록 구성할 수 있다.

복잡한 데이터 변환은 staged migration이나 custom mapping이 필요할 수 있다. 실제 사용자 데이터의 이전 버전 복사본으로 마이그레이션 테스트를 해야 한다.

{: .warning }
개발 중 `앱 삭제 후 재설치하면 된다`는 방식은 출시 후 마이그레이션 검증을 대신하지 못한다.

## 단위 테스트는 메모리 저장소로

```swift
final class CoreDataStackTests: XCTestCase {
    var stack: CoreDataStack!

    override func setUp() {
        super.setUp()
        stack = CoreDataStack(inMemory: true)
    }

    func testCreateTask() throws {
        let context = stack.container.viewContext

        try createTask(title: "테스트", in: context)

        let request = TaskItem.fetchRequest()
        let result = try context.fetch(request)

        XCTAssertEqual(result.count, 1)
        XCTAssertEqual(result.first?.title, "테스트")
    }
}
```

각 테스트마다 새 컨테이너를 만들어 상태가 섞이지 않게 한다. 마이그레이션과 실제 SQLite 특성을 시험할 때는 별도의 임시 디렉터리 저장소가 필요하다.

## 자주 하는 실수

### Core Data를 SQLite 테이블처럼만 생각한다

객체 ID, context, 관계, 변경 추적과 faulting을 무시하면 큐 문제와 오래된 객체 상태를 만나기 쉽다.

### 저장을 한 번만 하면 모든 것이 자동 저장된다고 생각한다

부모·자식 컨텍스트를 사용하면 자식 save가 부모 컨텍스트까지만 전달될 수 있다. 최종 persistent store까지 저장 경로를 확인한다.

### NSManagedObject를 다른 큐로 넘긴다

object ID를 전달하고 대상 context에서 다시 가져온다.

### 대량 삭제 후 UI가 자동 갱신될 것으로 기대한다

batch request는 context를 우회하므로 변경 병합이나 history 처리가 필요하다.

### 모든 오류에서 저장소를 삭제한다

일시 오류나 마이그레이션 오류 때문에 사용자 데이터를 삭제하면 복구가 불가능할 수 있다. 오류 종류와 복구 정책을 설계한다.

## 초보자를 위한 사용 순서

1. 데이터 모델에 엔티티와 속성을 만든다.
2. `NSPersistentContainer`로 저장소를 로드한다.
3. 화면에서는 `viewContext`를 사용한다.
4. `NSManagedObject`를 만들고 속성을 채운다.
5. `context.save()`로 저장한다.
6. `NSFetchRequest`와 predicate·sort로 조회한다.
7. 수정·삭제 후 다시 저장한다.
8. 대량 작업이 필요할 때 background context를 추가한다.
9. 큐 사이에는 object ID만 전달한다.
10. 출시 전 마이그레이션과 오류 복구를 테스트한다.

## 정리

- `NSPersistentContainer`는 Core Data 스택을 조립한다.
- `NSManagedObjectModel`은 데이터의 설계도다.
- `NSManagedObjectContext`는 객체를 편집하고 변경을 추적하는 작업 공간이다.
- `NSManagedObject`는 context에 속한 실제 데이터 객체다.
- `NSFetchRequest`는 조회 조건과 정렬을 표현한다.
- 객체를 다른 큐로 직접 넘기지 말고 `NSManagedObjectID`를 사용한다.
- batch 작업, history, migration은 기본 CRUD를 이해한 뒤 추가한다.

Objective-C 예제가 필요하면 [Objective-C로 Core Data 시작하기]({{ '/ios/core-data/' | relative_url }})도 함께 볼 수 있다.

## 참고

- [Apple Developer Documentation: Core Data](https://developer.apple.com/documentation/coredata)
- [Apple: Core Data stack](https://developer.apple.com/documentation/coredata/core-data-stack)
- [Apple: Using Core Data in the background](https://developer.apple.com/documentation/coredata/using-core-data-in-the-background)
- [Apple: NSFetchedResultsController](https://developer.apple.com/documentation/coredata/nsfetchedresultscontroller)
- [Apple: Batch processing](https://developer.apple.com/documentation/coredata/batch-processing)
- [Apple: Persistent history](https://developer.apple.com/documentation/coredata/persistent-history)
