---
layout: single
title: "[iOS] NSCoding과 Codable은 무엇이 다른가"
date: 2021-04-28
last_modified_at: 2026-11-01
comments: true
categories:
  - ios
tags: [iOS, Swift, Objective-C, NSCoding, Codable]
toc: true
toc_sticky: true
toc_label: "목차"
---

Objective-C와 Swift를 함께 사용하다 보면 `NSCoding`과 `Codable`을 비슷한 기능으로 오해하기 쉽다. 둘 다 값을 인코딩하고 복원하지만 목적과 데이터 형식이 다르다.

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

## 참고

- [Apple NSCoding](https://developer.apple.com/documentation/foundation/nscoding)
- [Apple Encoding and Decoding Custom Types](https://developer.apple.com/documentation/foundation/archives_and_serialization/encoding_and_decoding_custom_types)
