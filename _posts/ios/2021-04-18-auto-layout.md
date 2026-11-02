---
layout: single
title: "[iOS] Auto Layout 우선순위와 Baseline 이해하기"
date: 2021-04-18
last_modified_at: 2026-11-01
comments: true
categories:
  - ios
tags: [iOS, UIKit, Auto-Layout, Xcode]
toc: true
toc_sticky: true
toc_label: "목차"
---

Auto Layout을 사용할 때 제약 조건만큼 중요한 것이 우선순위다. 특히 텍스트를 표시하는 뷰는 고유 콘텐츠 크기(intrinsic content size), Content Hugging, Compression Resistance를 함께 이해해야 예상하지 못한 늘어남과 잘림을 막을 수 있다.

## 고유 콘텐츠 크기

`UILabel`, `UIButton`, `UITextField` 같은 뷰는 콘텐츠에 알맞은 자연스러운 크기를 제공한다. 예를 들어 레이블의 고유 크기는 텍스트와 글꼴에 따라 달라진다. 반면 일반 `UIView`에는 고유 콘텐츠 크기가 없다.

고유 크기가 있는 뷰에는 너비와 높이를 항상 직접 지정할 필요가 없다. 대신 시스템이 그 크기를 얼마나 지켜야 하는지를 두 우선순위로 결정한다.

## Content Hugging과 Compression Resistance

- **Content Hugging**: 고유 크기보다 커지지 않으려는 힘이다. 값이 큰 뷰가 덜 늘어난다.
- **Compression Resistance**: 고유 크기보다 작아지지 않으려는 힘이다. 값이 큰 뷰가 덜 줄어든다.

레이블과 텍스트 필드를 한 줄에 놓고 남는 공간을 텍스트 필드가 채우게 하려면, 텍스트 필드의 가로 Hugging을 레이블보다 낮게 둔다. 공간이 부족할 때 레이블의 텍스트를 보존해야 한다면 레이블의 가로 Compression Resistance를 더 높게 둔다.

```swift
label.setContentHuggingPriority(.defaultHigh, for: .horizontal)
textField.setContentHuggingPriority(.defaultLow, for: .horizontal)

label.setContentCompressionResistancePriority(
    .required,
    for: .horizontal
)
```

`required`인 1000을 남용하면 충돌 시 레이아웃 전체가 깨질 수 있다. 반드시 지켜야 하는 제약이 아니라면 999 같은 높은 선택 우선순위를 실패 지점으로 두는 편이 안전하다.

## Baseline 정렬

서로 글꼴이나 높이가 다른 텍스트 뷰를 중앙 정렬하면 글자가 미묘하게 어긋나 보일 수 있다. 이때 뷰의 프레임이 아니라 문자의 기준선인 `firstBaselineAnchor`나 `lastBaselineAnchor`를 맞춘다.

```swift
label.firstBaselineAnchor.constraint(
    equalTo: textField.firstBaselineAnchor
).isActive = true
```

Baseline 제약은 뷰가 고유 콘텐츠 높이로 표시될 때 올바르게 동작한다. 텍스트 뷰를 세로로 강제 확장하거나 압축하면 기준선이 기대와 다르게 보일 수 있다.

## 우선순위는 어떻게 계산될까

Auto Layout은 우선순위가 1000인 필수 제약을 먼저 만족시키고, 그다음 낮은 우선순위 제약을 가능한 범위에서 만족시킨다. 우선순위 751과 750은 단순히 1만큼 다른 숫자가 아니라, 충돌 시 어느 제약을 먼저 포기할지 결정하는 순서다.

예를 들어 제목과 가격 레이블이 한 줄에 있을 때 가격을 반드시 보존하고 제목은 말줄임할 수 있다면 가격의 Compression Resistance를 더 높게 둔다.

```swift
priceLabel.setContentCompressionResistancePriority(
    .required,
    for: .horizontal
)
titleLabel.setContentCompressionResistancePriority(
    .defaultHigh,
    for: .horizontal
)
titleLabel.numberOfLines = 1
titleLabel.lineBreakMode = .byTruncatingTail
```

## 레이아웃 문제를 찾는 순서

콘솔에 `Unable to simultaneously satisfy constraints`가 나타나면 로그에 표시된 제약을 무작정 삭제하지 말고 다음 순서로 본다.

1. 필수 제약끼리 같은 축에서 서로 모순되는지 확인한다.
2. `translatesAutoresizingMaskIntoConstraints`가 의도치 않게 `true`인지 확인한다.
3. 고유 콘텐츠 크기가 있는 뷰의 CHCR 우선순위를 비교한다.
4. 다국어의 긴 문자열과 Dynamic Type의 가장 큰 글자 크기로 시험한다.
5. `UIView.alertForUnsatisfiableConstraints`에 symbolic breakpoint를 걸어 충돌 시점의 호출 스택을 확인한다.

제약이 모호한지 확인할 때는 `hasAmbiguousLayout`과 디버거의 `exerciseAmbiguityInLayout()`도 활용할 수 있다. 후자는 가능한 레이아웃 사이를 바꿔 보여 주므로 빠진 제약을 시각적으로 찾는 데 도움이 된다.

## Interface Builder에서 코드로 연결하기

스토리보드의 제약을 코드에서 변경하려면 해당 제약을 `IBOutlet`으로 연결할 수 있다. 다만 런타임에 단순히 상수만 바꿀 목적이라면 새 제약을 계속 추가하기보다 기존 제약의 `constant`를 변경한다.

```swift
@IBOutlet private weak var topConstraint: NSLayoutConstraint!

func setExpanded(_ expanded: Bool) {
    topConstraint.constant = expanded ? 32 : 12
    UIView.animate(withDuration: 0.25) {
        self.view.layoutIfNeeded()
    }
}
```

## 참고

- [Apple Auto Layout Guide: Intrinsic Content Size](https://developer.apple.com/library/archive/documentation/UserExperience/Conceptual/AutolayoutPG/AnatomyofaConstraint.html)
- [Apple Auto Layout Guide: Interface Builder](https://developer.apple.com/library/archive/documentation/UserExperience/Conceptual/AutolayoutPG/WorkingwithConstraintsinInterfaceBuidler.html)
