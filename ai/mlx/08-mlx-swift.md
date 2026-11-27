---
title: "MLX Swift로 배열과 신경망 다루기"
description: "Python MLX에서 다룬 배열, 지연 평가, 자동 미분, 신경망 학습을 MLX Swift(mlx-swift)로 옮겨 Swift Package 설정, MLXArray 연산, grad·valueAndGrad, Module과 옵티마이저를 Python API와 대조해 설명합니다."
parent: MLX
grand_parent: iOS
nav_order: 8
permalink: /ai/mlx/mlx-swift/
date: 2026-11-27
first_written: 2026-11-27
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [MLX, Swift, mlx-swift, Apple-Silicon, Machine-Learning]
---

# MLX Swift로 배열과 신경망 다루기
{: .no_toc }

{% include article-toc.md %}

앞 글들은 Python으로 MLX를 다뤘다. 그런데 학습한 모델을 iPhone이나 Mac 앱 안에서 돌리려면 Python을 앱에 넣을 수 없다. 이때 쓰는 것이 MLX Swift다.

**MLX Swift(mlx-swift)**는 MLX의 C++ 코어를 Swift에서 쓸 수 있게 감싼 공식 Swift 패키지다. Python MLX와 같은 배열 연산, 지연 평가, 자동 미분, 신경망 층과 옵티마이저를 Swift API로 제공하고, macOS와 iOS 앱에 Swift Package로 넣을 수 있다.

이 글에서는 앞 글에서 Python으로 해 본 것을 같은 순서로 Swift로 옮긴다.

1. Swift Package로 프로젝트 만들기
2. `MLXArray` 만들기와 연산
3. 지연 평가와 `eval`
4. `grad`로 기울기 구하기
5. `Module`로 XOR 신경망 학습하기

{: .warning }
이 글을 쓴 환경에는 Swift 툴체인과 Apple 실리콘 Mac이 없어서 아래 Swift 코드를 직접 빌드하지 못했다. API 이름과 사용법은 [mlx-swift 저장소](https://github.com/ml-explore/mlx-swift)와 [문서](https://swiftpackageindex.com/ml-explore/mlx-swift/main/documentation/mlx)를 기준으로 썼다. 버전에 따라 이름이 다를 수 있으니 빌드 오류가 나면 사용 중인 버전의 문서를 확인한다. 주석과 본문에 적은 결과값은 같은 계산을 Python MLX 0.32.4로 실행해 확인한 값이다.

## 준비

### 필요한 것

- Apple 실리콘 Mac
- Xcode 16 이상

### Swift Package 만들기

```bash
mkdir MLXSwiftPractice && cd MLXSwiftPractice
swift package init --type executable
```

`Package.swift`를 다음처럼 바꾼다.

```swift
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MLXSwiftPractice",
    platforms: [.macOS(.v14)],
    dependencies: [
        .package(url: "https://github.com/ml-explore/mlx-swift", from: "0.21.0"),
    ],
    targets: [
        .executableTarget(
            name: "MLXSwiftPractice",
            dependencies: [
                .product(name: "MLX", package: "mlx-swift"),
                .product(name: "MLXNN", package: "mlx-swift"),
                .product(name: "MLXOptimizers", package: "mlx-swift"),
            ]
        ),
    ]
)
```

`from: "0.21.0"`은 0.21.0 이상 1.0 미만에서 가장 최신 버전을 받는다는 뜻이다.

mlx-swift는 여러 모듈로 나뉘어 있다.

| 모듈 | 내용 | Python 대응 |
| --- | --- | --- |
| `MLX` | 배열, 연산, 자동 미분, 장치 | `mlx.core` |
| `MLXNN` | 층, 활성화 함수, 손실 함수 | `mlx.nn` |
| `MLXOptimizers` | SGD, Adam 등 | `mlx.optimizers` |
| `MLXRandom` | 난수 | `mlx.core.random` |
| `MLXFFT`, `MLXLinalg` | 푸리에 변환, 선형대수 | `mlx.core.fft`, `mlx.core.linalg` |

### 빌드는 Xcode로

MLX는 GPU 연산에 Metal 셰이더를 쓴다. mlx-swift README에 따르면 명령줄의 `swift build`는 이 Metal 셰이더를 빌드하지 못한다. 그래서 `Package.swift`를 Xcode로 열어 실행하거나 `xcodebuild`를 쓴다.

```bash
open Package.swift          # Xcode에서 열고 ⌘R로 실행
# 또는
xcodebuild build -scheme MLXSwiftPractice -destination 'platform=macOS'
```

## MLXArray 만들기와 연산

`Sources/MLXSwiftPractice/main.swift`에 쓴다.

```swift
import MLX

let a = MLXArray([1, 2, 3, 4] as [Float], [2, 2])
let b = MLXArray([1, 1] as [Float], [2, 1])

print(a.shape, a.dtype)      // [2, 2] float32
print(matmul(a, b))          // [[3], [7]]
print(a * 10)                // 원소별 곱
print(a.sum(axis: 1))        // 행마다 합: [3, 7]
print(a.mean(axis: 0))       // 열마다 평균: [2, 3]
```

Python과 비교하면 이렇다.

| Python | Swift |
| --- | --- |
| `mx.array([[1, 2], [3, 4]], dtype=mx.float32)` | `MLXArray([1, 2, 3, 4] as [Float], [2, 2])` |
| `a @ b` 또는 `mx.matmul(a, b)` | `matmul(a, b)` 또는 `a.matmul(b)` |
| `mx.sum(a, axis=1)` | `a.sum(axis: 1)` 또는 `sum(a, axis: 1)` |
| `a.shape` → `(2, 2)` | `a.shape` → `[2, 2]` |
| `a.item()` | `a.item(Float.self)` |
| `a.tolist()` | `a.asArray(Float.self)` |

Swift 쪽에서 주의할 점은 두 가지다.

- **데이터는 1차원 배열로 주고 shape를 따로 준다.** `MLXArray([1, 2, 3, 4] as [Float], [2, 2])`는 값 4개를 2×2로 배치한다.
- **원소 타입을 명시한다.** Swift의 정수 리터럴은 기본이 `Int`라서, `as [Float]`가 없으면 정수 배열이 된다. 학습에 쓰는 배열은 보통 `Float`(float32)로 만든다.

## 지연 평가와 eval

[지연 평가]({{ '/ai/mlx/lazy-evaluation/' | relative_url }})는 Swift에서도 같다. 연산식을 쓴 줄에서는 계산 그래프만 만들어지고, 값이 필요할 때 계산된다.

```swift
let x = MLXArray(0 ..< 1_000_000).asType(.float32)
let y = (x * 2 + 1).sum()   // 아직 계산하지 않음

eval(y)                      // 여기서 계산
print(y.item(Float.self))    // 값을 꺼낼 때도 계산이 일어난다
```

`print`, `item`, `asArray`처럼 값을 꺼내는 호출은 필요한 계산을 먼저 실행한다. 학습 루프에서는 매 스텝 끝에 `eval`을 불러 그래프가 계속 커지지 않게 한다. 이 점도 Python과 같다.

실행 장치는 연산마다 `stream:`으로 고를 수 있다.

```swift
let onCPU = matmul(a, a, stream: .cpu)
let onGPU = matmul(a, a, stream: .gpu)
```

## grad로 기울기 구하기

`grad`는 함수를 받아 그 함수의 기울기를 계산하는 새 함수를 돌려준다. Python의 `mx.grad`와 같다.

```swift
import MLX

// f(x) = x² 의 합, 기울기는 2x
let f: (MLXArray) -> MLXArray = { x in (x * x).sum() }
let df = grad(f)

let x = MLXArray([1, 2, 3] as [Float])
print(df(x))   // [2, 4, 6]
```

[학습 루프 글]({{ '/ai/mlx/training-loop/' | relative_url }})의 직선 학습을 Swift로 옮기면 다음과 같다. 파라미터 `w`, `b`를 배열 하나로 묶어 기울기를 한 번에 구한다.

```swift
import MLX

let xs = MLXArray([0, 1, 2] as [Float])
let ys = MLXArray([1, 3, 5] as [Float])   // y = 2x + 1

func loss(_ p: MLXArray) -> MLXArray {
    let w = p[0], b = p[1]
    return square(w * xs + b - ys).mean()
}

let lossAndGrad = valueAndGrad(loss)
var p = MLXArray([0, 0] as [Float])

for step in 1 ... 500 {
    let (l, g) = lossAndGrad(p)
    p = p - 0.1 * g
    eval(p)
    if step == 1 || step == 500 {
        print("step \(step) loss \(l.item(Float.self)) w \(p[0].item(Float.self)) b \(p[1].item(Float.self))")
    }
}
```

같은 계산을 Python MLX로 실행하면 첫 스텝 손실은 11.67, 500 스텝 뒤에는 `w`=2.000, `b`=1.000, 손실은 거의 0이 된다.

## Module로 XOR 신경망 학습하기

[신경망 글]({{ '/ai/mlx/neural-network/' | relative_url }})의 XOR 문제를 Swift로 푼다. 층은 `MLXNN`의 `Linear`를, 학습은 `MLXOptimizers`의 `SGD`를 쓴다.

```swift
import MLX
import MLXNN
import MLXOptimizers

class MLP: Module, UnaryLayer {
    @ModuleInfo var l1: Linear
    @ModuleInfo var l2: Linear

    init(hidden: Int) {
        self.l1 = Linear(2, hidden)
        self.l2 = Linear(hidden, 1)
        super.init()
    }

    func callAsFunction(_ x: MLXArray) -> MLXArray {
        l2(relu(l1(x)))
    }
}

let x = MLXArray([0, 0, 0, 1, 1, 0, 1, 1] as [Float], [4, 2])
let y = MLXArray([0, 1, 1, 0] as [Float], [4, 1])

MLXRandom.seed(0)
let model = MLP(hidden: 8)
eval(model)   // 지연된 파라미터 초기화를 미리 실행

func loss(model: MLP, x: MLXArray, y: MLXArray) -> MLXArray {
    mseLoss(predictions: model(x), targets: y, reduction: .mean)
}

let lossAndGrad = valueAndGrad(model: model, loss)
let optimizer = SGD(learningRate: 0.5)

for step in 1 ... 500 {
    let (l, grads) = lossAndGrad(model, x, y)
    optimizer.update(model: model, gradients: grads)
    eval(model, optimizer)
    if step % 100 == 0 {
        print("step \(step) loss \(l.item(Float.self))")
    }
}

print(round(model(x)))   // 기대값: [[0], [1], [1], [0]]
```

Python 코드와 줄 단위로 대응한다.

| 역할 | Python | Swift |
| --- | --- | --- |
| 모델 정의 | `class MLP(nn.Module)` + `__call__` | `class MLP: Module, UnaryLayer` + `callAsFunction` |
| 하위 층 등록 | 속성에 대입 | `@ModuleInfo var` 속성 |
| 손실 | `nn.losses.mse_loss(pred, y)` | `mseLoss(predictions:targets:reduction:)` |
| 손실과 기울기 | `nn.value_and_grad(model, fn)` | `valueAndGrad(model: model, fn)` |
| 갱신 | `optimizer.update(model, grads)` | `optimizer.update(model: model, gradients: grads)` |
| 평가 | `mx.eval(model.parameters(), optimizer.state)` | `eval(model, optimizer)` |

`@ModuleInfo`는 하위 층을 `Module`의 파라미터 트리에 등록하고, 나중에 양자화처럼 층을 다른 층으로 바꿔 끼울 수 있게 해 준다. 은닉 크기 8, 학습률 0.5는 Python 글과 다르다. 초기값에 따라 학습이 덜 될 수 있으니, 손실이 줄지 않으면 시드나 은닉 크기를 바꿔 본다.

## 언어 모델은 별도 패키지로

Python의 `mlx-lm`에 해당하는 언어 모델 실행 코드는 mlx-swift 본체가 아니라 별도 저장소에 있다. [mlx-swift-examples](https://github.com/ml-explore/mlx-swift-examples)에서 LLM 실행 예제와 `MLXLLM`, `MLXLMCommon` 라이브러리를 제공하며, 최근에는 언어 모델 라이브러리를 별도 저장소로 분리하는 작업이 진행됐다. 앱에 붙일 때는 해당 저장소의 README에서 현재 패키지 위치와 사용법을 확인한다.

## iOS 앱에서 쓸 때

- 같은 Swift Package를 iOS 앱 타깃에 추가하면 된다. MLX는 Metal GPU를 쓰므로 Apple 실리콘이 들어간 기기에서 실행한다. 시뮬레이터에서는 제약이 있을 수 있으니 실기기로 확인한다.
- 모델 가중치는 앱 번들에 넣거나 처음 실행할 때 내려받는다. 큰 모델은 메모리를 많이 쓰므로 기기별 메모리 한도를 고려한다.
- 시스템이 제공하는 언어 모델로 충분하면 [Foundation Models]({{ '/ios/foundation-models/' | relative_url }})가 더 간단하다. MLX Swift는 직접 고른 모델을 돌리거나, 앱 안에서 학습·미세 조정까지 해야 할 때 쓴다.

## 주요 API

| API | 역할 |
| --- | --- |
| `MLXArray(_ values: [T], _ shape: [Int])` | 1차원 값과 shape로 배열 생성 |
| `MLXArray(0 ..< n)` | 연속 정수 배열 |
| `.shape`, `.dtype`, `.asType(.float32)` | 모양, 원소 타입, 타입 변환 |
| `matmul(a, b)`, `a * b`, `a + b`, `square(a)` | 행렬곱과 원소별 연산 |
| `a.sum(axis:)`, `a.mean(axis:)` | 축을 따라 합·평균 |
| `a[0]`, `a[1 ..< 3]` | 인덱싱과 슬라이싱 |
| `eval(_:)` | 지연된 계산 실행. 배열, `Module`, 옵티마이저를 받는다 |
| `a.item(Float.self)`, `a.asArray(Float.self)` | Swift 값·배열로 꺼내기 |
| `stream: .cpu` / `.gpu` | 연산별 실행 장치 지정 |
| `grad(fn)`, `valueAndGrad(fn)` | 기울기 함수, 값과 기울기 함수 |
| `Module`, `UnaryLayer`, `@ModuleInfo` | `MLXNN`. 모델 기본 클래스, 입력 하나 받는 층, 하위 층 등록 |
| `Linear(in, out)`, `relu(x)` | 선형 층, 활성화 함수 |
| `mseLoss(predictions:targets:reduction:)`, `crossEntropy(logits:targets:)` | 손실 함수 |
| `valueAndGrad(model:_:)` | 모델 파라미터에 대한 손실과 기울기 |
| `SGD(learningRate:)`, `Adam(learningRate:)` | `MLXOptimizers`. 옵티마이저 |
| `optimizer.update(model:gradients:)` | 기울기로 파라미터 갱신 |
| `MLXRandom.seed(_:)` | 난수 시드 고정 |

## 실습 소스

본문의 코드를 Swift Package 형태로 받을 수 있다. 이 글을 쓴 환경에서는 빌드하지 못했으므로, Xcode에서 빌드하며 사용 중인 mlx-swift 버전에 맞게 고친다.

- [Package.swift]({{ '/assets/examples/mlx/mlx-swift/Package.swift' | relative_url }})
- [main.swift]({{ '/assets/examples/mlx/mlx-swift/Sources/MLXSwiftPractice/main.swift' | relative_url }})

## 이어서 읽기

- [MLX 개요와 실행 환경]({{ '/ai/mlx/what-is-mlx/' | relative_url }})
- [MLX로 작은 신경망 만들기]({{ '/ai/mlx/neural-network/' | relative_url }})
- [Foundation Models]({{ '/ios/foundation-models/' | relative_url }})

## 참고

- [ml-explore/mlx-swift](https://github.com/ml-explore/mlx-swift)
- [MLX Swift 문서](https://swiftpackageindex.com/ml-explore/mlx-swift/main/documentation/mlx)
- [ml-explore/mlx-swift-examples](https://github.com/ml-explore/mlx-swift-examples)
