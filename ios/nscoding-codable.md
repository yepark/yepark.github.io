---
title: "NSCoding과 Codable의 직렬화 모델"
parent: "iOS"
nav_order: 3
permalink: /ios/nscoding-codable/
last_modified_at: 2026-11-17
seo:
  type: BlogPosting
date: 2021-04-28
description: "NSCoding 객체 아카이빙과 Codable 직렬화의 차이, 보안 디코딩과 모델 호환성을 설명합니다."
first_written: 2021-04-28
last_modified_date: 2026-11-17
tags: [iOS, Swift, Objective-C, NSCoding, Codable]
---

# NSCoding과 Codable의 직렬화 모델
{: .no_toc }

{% include article-toc.md %}

Objective-C와 Swift를 함께 사용하다 보면 `NSCoding`과 `Codable`을 비슷한 기능으로 오해하기 쉽다. 둘 다 값을 인코딩하고 복원하지만 목적과 데이터 형식이 다르다.

## 인코딩과 저장 구분하기

인코딩은 메모리의 값을 `Data` 같은 바이트 표현으로 바꾸는 과정이고, 저장은 그 바이트를 파일 등에 기록하는 과정이다. 디코딩은 반대로 바이트를 앱의 값으로 복원한다.

아래에는 같은 `Person` 이름을 쓰는 서로 독립적인 예제가 있다. `Codable` 구조체 예제와 `NSSecureCoding` 클래스 예제를 한 타입처럼 섞으면 안 된다. `NSKeyedUnarchiver` 예제의 `Person`은 보안 코딩을 채택한 클래스라고 가정한다.

## NSCoding: 객체 그래프 아카이빙

`NSCoding`은 객체를 `NSCoder`로 인코딩하고 디코딩하기 위한 Foundation 프로토콜이다. 일반적으로 `NSKeyedArchiver`와 함께 객체 그래프를 파일이나 `Data`로 보관할 때 사용한다.

```objc
@interface Person : NSObject <NSSecureCoding>
@property (nonatomic, copy) NSString *name;
@end

@implementation Person
+ (BOOL)supportsSecureCoding { return YES; }

- (void)encodeWithCoder:(NSCoder *)coder {
    [coder encodeObject:self.name forKey:@"name"];
}

- (instancetype)initWithCoder:(NSCoder *)coder {
    self = [super init];
    if (self) {
        _name = [coder decodeObjectOfClass:NSString.class forKey:@"name"];
    }
    return self;
}
@end
```

새 코드에서는 허용할 클래스를 검증하는 `NSSecureCoding`과 보안 디코딩 API를 우선한다. 신뢰할 수 없는 아카이브를 아무 클래스로나 복원하면 객체 치환 문제가 생길 수 있다.

## Codable: 외부 표현과의 변환

Swift의 `Codable`은 `Encodable`과 `Decodable`을 합친 별칭이다. JSON 전용 프로토콜은 아니며, 선택한 Encoder와 Decoder에 따라 JSON, Property List 등으로 변환할 수 있다.

```swift
struct Person: Codable {
    let name: String
}

let person = Person(name: "yep")
let data = try JSONEncoder().encode(person)
let decoded = try JSONDecoder().decode(Person.self, from: data)
```

컴파일러가 저장 프로퍼티에 대한 구현을 합성할 수 있어 Swift 값 타입과 잘 맞는다.

## 무엇을 선택할까

| 요구 사항 | 적합한 선택 |
| --- | --- |
| 서버 JSON API와 통신 | `Codable` + `JSONEncoder/JSONDecoder` |
| Swift 구조체를 명시적 형식으로 저장 | `Codable` |
| 기존 Objective-C 객체 그래프 아카이브 | `NSSecureCoding` |
| Cocoa 프레임워크가 `NSCoder`를 요구 | `NSCoding` 또는 `NSSecureCoding` |

`NSCoding` 결과를 JSON으로 바꾸는 것은 프로토콜의 목적이 아니다. JSON이 필요하면 각 필드를 JSON 모델로 명시적으로 매핑하거나 Swift 모델에 `Codable`을 적용해야 한다. 반대로 오래 보관할 데이터는 어느 방식을 사용하든 스키마 변경과 마이그레이션 전략이 필요하다.

## 안전한 아카이브 복원

`NSSecureCoding`을 채택해도 디코딩할 때 허용 클래스를 지정하지 않으면 장점을 살릴 수 없다. Objective-C에서는 `decodeObjectOfClass:forKey:`, 컬렉션은 `decodeObjectOfClasses:forKey:`처럼 복원 가능한 타입을 제한한다.

Swift에서 아카이브를 해제할 때도 최상위 타입을 명시한다.

아래 `Person`은 앞의 `Codable` 구조체가 아니라 `NSSecureCoding`을 채택한 클래스다. `archivedData`는 그 클래스의 인스턴스를 보안 아카이빙한 `Data`라고 가정한다. 두 예제는 같은 파일에 그대로 이어 붙이는 코드가 아니다.

```swift
let person = try NSKeyedUnarchiver.unarchivedObject(
    ofClass: Person.self,
    from: archivedData
)
```

외부에서 받은 아카이브는 신뢰하지 않는다. 디코딩 실패를 정상적인 오류 경로로 처리하고, 예상하지 못한 클래스나 지나치게 큰 데이터가 들어왔을 때 작업을 중단해야 한다.

## 모델이 바뀌면 어떻게 할까

저장된 데이터는 앱 업데이트 후에도 남는다. 프로퍼티를 추가할 때는 키가 없을 수 있음을 고려하고, 이름을 변경할 때는 이전 키를 함께 읽는 마이그레이션 기간을 둔다. `Codable`에서도 같은 문제가 생긴다.

```swift
struct Person: Codable {
    let name: String
    let nickname: String?

    private enum CodingKeys: String, CodingKey {
        case name
        case nickname
    }
}
```

서버 JSON처럼 독립적으로 진화하는 형식이라면 `CodingKeys`, 사용자 정의 `init(from:)`, 버전 필드를 사용해 호환 범위를 명시한다. 장기 보관 데이터에는 “현재 모델이 자동으로 합성되니 계속 읽힐 것”이라고 가정하지 않는 것이 중요하다.

## 참고

- [Apple NSCoding](https://developer.apple.com/documentation/foundation/nscoding)
- [Apple Encoding and Decoding Custom Types](https://developer.apple.com/documentation/foundation/archives_and_serialization/encoding_and_decoding_custom_types)
