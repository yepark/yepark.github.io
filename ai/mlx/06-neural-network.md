---
title: "MLX로 작은 신경망 만들기"
description: "직선 하나로 풀 수 없는 XOR 문제를 mlx.nn의 Linear·Module·value_and_grad와 mlx.optimizers의 SGD로 직접 학습하며 신경망의 구성 요소를 설명합니다."
parent: MLX
grand_parent: iOS
nav_order: 6
permalink: /ai/mlx/neural-network/
date: 2026-11-20
first_written: 2026-11-20
last_modified_at: 2026-11-21
last_modified_date: 2026-11-21
seo:
  type: BlogPosting
tags: [MLX, Python, Neural-Network, mlx.nn]
---

# MLX로 작은 신경망 만들기
{: .no_toc }

{% include article-toc.md %}

입력 두 개가 서로 다르면 1, 같으면 0을 답하는 문제가 있다. 이 규칙을 XOR이라고 부른다.

| 입력 a | 입력 b | 정답 |
| ---: | ---: | ---: |
| 0 | 0 | 0 |
| 0 | 1 | 1 |
| 1 | 0 | 1 |
| 1 | 1 | 0 |

[앞 글]({{ '/ai/mlx/training-loop/' | relative_url }})에서는 `w × x + b` 하나로 직선 관계를 학습했다. 같은 방식의 모델을 XOR에 그대로 쓰면 어떻게 될까. 이번 글에서는 실제로 실패하는 모습을 먼저 보고, 층을 하나 더 쌓아 문제를 푼다. 이때 파라미터를 직접 관리하던 코드를 `mlx.nn`과 `mlx.optimizers`로 바꾼다.

{: .tip }
쉽게 말하면, 앞 글에서 숫자 두 개(w, b)를 손으로 들고 다녔다면 이번에는 숫자 33개가 든 상자를 MLX가 대신 들어 준다.

## 실행 환경

이 글의 출력은 **Linux x86_64 클라우드 머신의 CPU**에서 직접 실행한 결과다. Mac에서 실행한 결과가 아니다.

| 항목 | 값 |
| --- | --- |
| 운영체제 | Linux, x86_64 |
| Python | 3.13.18 |
| MLX | 0.32.4 (`pip install 'mlx[cpu]'`) |
| 기본 장치 | `Device(cpu, 0)` |

`mlx[cpu]`는 Linux에서 CPU만 쓰는 설치 방법이다. Mac에서는 앞 글들처럼 `mlx` 패키지를 설치한다. 아래 코드는 장치를 지정하지 않으므로 두 환경에서 그대로 실행된다. 다만 난수로 만든 초기값과 손실 숫자가 이 글과 같다고 보장할 수는 없다.

## 레이어 하나: nn.Linear

신경망에서 **레이어**는 입력을 받아 정해진 계산을 하고 결과를 넘기는 한 단계다. 공장의 작업대 하나를 떠올리면 된다. 물건이 작업대를 차례로 지나며 모양이 바뀐다.

가장 기본 레이어는 `nn.Linear`다. 공식 문서는 계산을 다음처럼 적는다.

```text
y = x Wᵀ + b
W의 shape: [output_dims, input_dims]
b의 shape: [output_dims]
```

앞 글의 `w × x + b`를 여러 입력, 여러 출력으로 넓힌 것이다. 직접 만들어 확인해 보자.

```python
import mlx.core as mx
import mlx.nn as nn

mx.random.seed(0)
layer = nn.Linear(2, 3)
print(layer)
print(layer.weight.shape, layer.bias.shape)

x = mx.array([[0.0, 1.0]])
y = layer(x)
print(y.shape)
manual = x @ layer.weight.T + layer.bias
print(mx.allclose(y, manual).item())
```

```text
Linear(input_dims=2, output_dims=3, bias=True)
(3, 2) (3,)
(1, 3)
True
```

입력 2개를 받아 3개를 내놓는 레이어의 가중치는 `(3, 2)`다. 문서의 `[output_dims, input_dims]` 순서와 같다. 마지막 줄의 `True`는 레이어의 결과가 `x @ W.T + b`를 손으로 계산한 값과 같다는 뜻이다.

{: .note }
`nn.Linear`는 새로운 마법이 아니다. 행렬곱 한 번과 덧셈 한 번을 묶어 둔 부품이다.

가중치의 처음 값은 난수다. 문서에 따르면 `-k`부터 `k` 사이에서 고르게 뽑고, `k = 1 / √input_dims`다. 그래서 `mx.random.seed(0)`으로 난수 시작점을 고정해야 같은 머신에서 같은 결과를 다시 얻는다.

## 직선 하나로 XOR을 학습하면

먼저 데이터와 학습 함수를 만든다. 학습 함수의 내용은 다음 절에서 하나씩 설명한다.

```python
import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
from mlx.utils import tree_flatten

X = mx.array([[0, 0], [0, 1], [1, 0], [1, 1]],
             dtype=mx.float32)
Y = mx.array([[0], [1], [1], [0]], dtype=mx.float32)


def loss_fn(model, x, y):
    return nn.losses.mse_loss(model(x), y)


def train(model, steps=500, lr=0.1):
    mx.eval(model.parameters())
    loss_and_grad = nn.value_and_grad(model, loss_fn)
    opt = optim.SGD(learning_rate=lr)
    for step in range(1, steps + 1):
        loss, grads = loss_and_grad(model, X, Y)
        opt.update(model, grads)
        mx.eval(model.parameters(), opt.state)
        if step in (1, 100, 500):
            print(f"step {step:3d} loss {loss.item():.4f}")
    return model
```

`X`는 4개 샘플, 샘플마다 입력 2개라서 shape가 `(4, 2)`다. `Y`는 샘플마다 정답 1개라서 `(4, 1)`이다. 손실은 앞 글과 같은 평균제곱오차를 쓴다. `nn.losses.mse_loss`의 기본 `reduction`은 `'mean'`이다.

이제 `nn.Linear(2, 1)` 하나, 즉 직선(평면) 하나로 학습한다.

```python
mx.random.seed(0)
line = train(nn.Linear(2, 1))
print(mx.round(line(X), 2).tolist())
```

```text
step   1 loss 1.0846
step 100 loss 0.2501
step 500 loss 0.2500
[[0.5], [0.5], [0.5], [0.5]]
```

손실이 0.25에서 더 내려가지 않는다. 네 입력 모두에 0.5라고 답한다. 정답 0과 1의 한가운데다.

왜 그럴까. `w1×a + w2×b + c` 꼴의 식은 a나 b가 커질 때 결과가 한쪽으로만 움직인다. XOR은 (0,0)에서 0, 한 칸 가면 1, 두 칸 가면 다시 0이다. 올라갔다 내려오는 모양을 한 번의 `x Wᵀ + b`로는 만들 수 없다. 그래서 오차가 가장 작아지는 타협안인 "모두 0.5"에 머문다.

{: .note }
학습이 실패한 이유는 학습률이나 반복 횟수가 아니다. 모델이 표현할 수 있는 모양에 XOR이 없다.

## 층을 쌓고 사이에 ReLU를 넣는다

해결 방법은 레이어를 두 개 이어 붙이고, 그 사이에 **활성화 함수**를 넣는 것이다. 활성화 함수는 레이어 결과를 한 번 구부리는 함수다. 여기서는 ReLU를 쓴다. MLX 문서는 `nn.relu`를 `mx.maximum(x, 0)`이라고 설명한다. 음수는 0으로 바꾸고 양수는 그대로 둔다.

{: .warning }
`Linear` 두 개를 활성화 함수 없이 바로 이으면 행렬곱 두 번이 행렬곱 한 번으로 합쳐진다. 결국 직선 하나와 같은 모양만 만들 수 있다. 꺾는 단계가 있어야 층을 쌓은 의미가 생긴다.

이 구조를 `nn.Module`로 묶는다.

```python
class MLP(nn.Module):
    def __init__(self, hidden):
        super().__init__()
        self.l1 = nn.Linear(2, hidden)
        self.l2 = nn.Linear(hidden, 1)

    def __call__(self, x):
        x = nn.relu(self.l1(x))
        return self.l2(x)
```

`__init__`에서 부품을 만들고, `__call__`에서 입력이 부품을 지나는 순서를 적는다. `model(X)`처럼 부르면 `__call__`이 실행된다.

## Module은 파라미터를 담는 상자다

공식 문서는 `Module`을 "배열이나 다른 Module을 담는 상자"라고 설명한다. 주된 역할은 안에 든 파라미터를 끝까지 찾아 꺼내고, 한꺼번에 바꾸는 것이다. 이름이 `_`로 시작하지 않는 공개 배열 속성이 파라미터가 된다.

```python
from mlx.utils import tree_map

mx.random.seed(0)
mlp = MLP(8)
print(mlp)
shapes = tree_map(lambda p: p.shape, mlp.parameters())
print(shapes)
n = sum(v.size for _, v in tree_flatten(mlp.parameters()))
print("params", n)
```

```text
MLP(
  (l1): Linear(input_dims=2, output_dims=8, bias=True)
  (l2): Linear(input_dims=8, output_dims=1, bias=True)
)
{'l1': {'weight': (8, 2), 'bias': (8,)}, 'l2': {'weight': (1, 8), 'bias': (1,)}}
params 33
```

`parameters()`는 중첩된 딕셔너리를 돌려준다. 속성 이름 `l1`, `l2`가 그대로 키가 된다. 이렇게 딕셔너리와 리스트가 겹겹이 들어 있는 구조를 MLX 문서는 **트리**라고 부른다. `tree_map`은 트리의 모든 배열에 같은 함수를 적용하고, `tree_flatten`은 트리를 `("l1.weight", 배열)` 같은 목록으로 펼친다.

파라미터 수는 `8×2 + 8 + 1×8 + 1 = 33`이다. 앞 글에서는 숫자 두 개를 배열 하나에 넣고 `parameters[0]`, `parameters[1]`로 직접 꺼냈다. 이제는 Module이 이름으로 정리해 준다.

## 학습 루프의 세 부품

위의 `train` 함수를 다시 보자. 앞 글의 루프와 같은 일을 하지만 부품 세 개가 바뀌었다.

### nn.value_and_grad

`mx.value_and_grad`는 함수의 **인자**에 대한 기울기를 구한다. 그런데 Module의 파라미터는 인자가 아니라 객체 안에 들어 있다. 공식 문서는 `nn.value_and_grad`가 이 문제를 다음 순서로 처리한다고 설명한다.

1. 넘겨받은 파라미터를 `Module.update`로 모델에 넣는 함수로 감싼다.
2. 그 함수를 `mx.value_and_grad`로 변환한다.
3. 모델의 학습 가능한 파라미터를 첫 인자로 넘겨 호출한다.

그래서 돌려받는 `grads`는 `parameters()`와 같은 모양의 트리다. `grads["l1"]["weight"]`의 shape는 `(8, 2)`다.

### optimizer.update

**옵티마이저**는 기울기를 보고 파라미터를 고치는 규칙이다. 앞 글에서 직접 쓴 `파라미터 - 학습률 × 기울기`를 대신 해 준다. `optim.SGD`의 기본값(`momentum=0`)에서는 이 식과 같다.

`opt.update(model, grads)`는 트리의 같은 위치끼리 짝지어 모든 파라미터를 고친 뒤 모델에 넣는다.

### mx.eval(model.parameters(), opt.state)

MLX는 계산을 미룬다. 공식 예제 주석도 `update` 직후에는 "아직 계산이 일어나지 않았다"고 적는다. 그래서 매 단계 끝에 새 파라미터와 **옵티마이저 상태**를 함께 평가한다.

옵티마이저 상태는 옵티마이저가 단계 사이에 기억하는 값이다. 이 머신에서 확인하니 `SGD`의 `state`에는 처음에 `step`, `learning_rate`가 있고, 한 번 `update`한 뒤 파라미터 이름(`weight`, `bias`)의 항목이 추가됐다.

{: .warning }
`opt.state`를 빼고 `model.parameters()`만 평가하면, 공식 예제가 함께 평가하라고 한 값 하나를 빠뜨리는 것이다. 공식 예제의 형태를 그대로 따르자.

학습 시작 전의 `mx.eval(model.parameters())`도 공식 예제에 있다. 문서는 모델을 만든 직후에는 지연 평가 때문에 파라미터가 아직 초기화되지 않은 상태라고 설명한다. 이 호출로 초기값을 미리 계산한다.

## 두 층 신경망의 결과

```python
mlp = train(mlp)
print(mx.round(mlp(X), 2).tolist())
```

```text
step   1 loss 0.3311
step 100 loss 0.1593
step 500 loss 0.0000
[[0.0], [1.0], [1.0], [0.0]]
```

출력된 손실은 그 단계에서 **업데이트하기 전** 파라미터로 잰 값이다. 500단계 손실은 소수점 넷째 자리까지 0으로 반올림됐다. 예측도 소수점 둘째 자리 반올림으로 `0, 1, 1, 0`이 됐다. 직선 하나는 0.25에서 멈췄지만, 같은 학습률과 같은 반복 횟수로 두 층 신경망은 XOR을 맞혔다.

이 결과가 seed 0 하나에서만 나온 우연인지 확인하려고 seed 0~9로 `MLP(8)`을 같은 설정으로 학습했다. 이 머신에서 10번 모두 최종 손실이 소수점 넷째 자리 반올림으로 0.0이었다. 같은 스크립트를 두 번 실행한 출력은 글자 하나까지 같았다.

{: .question }
그렇다면 은닉 크기 8, 학습률 0.1, 500단계가 언제나 정답일까? 그렇지 않다. 이 값들은 4개 샘플짜리 XOR에서 이 머신으로 확인한 실험 설정일 뿐이다. 다른 데이터에는 다시 실험해야 한다.

## 일부 파라미터만 학습하기: freeze

`Module.freeze()`는 파라미터를 얼린다. 문서는 얼린다는 것을 "그 파라미터의 기울기를 계산하지 않는 것"이라고 정의한다. 이미 학습한 부분은 그대로 두고 일부만 다시 학습할 때 쓴다.

```python
mlp.l1.freeze()
names = [k for k, _ in
         tree_flatten(mlp.trainable_parameters())]
print(names)
```

```text
['l2.weight', 'l2.bias']
```

`trainable_parameters()`에서 `l1`이 빠졌다. `nn.value_and_grad`는 이 학습 가능한 파라미터에 대해서만 기울기를 구한다. `parameters()`에는 여전히 `l1`도 들어 있다. 사라진 것이 아니라 학습 대상에서만 빠진 것이다.

## 정리

{: .note }
`nn.Linear`는 `x Wᵀ + b`를 묶은 부품이고, `W`의 shape는 `[출력, 입력]`이다.

- 직선 하나(`nn.Linear(2, 1)`)는 XOR에서 손실 0.25, 모든 예측 0.5에 머물렀다. 모델이 그 모양을 표현할 수 없기 때문이다.
- `Linear → ReLU → Linear`로 쌓으면 같은 학습 설정에서 XOR을 맞혔다. 활성화 함수가 없으면 층을 쌓아도 직선 하나와 같다.
- `nn.Module`은 파라미터를 이름이 붙은 트리로 담는다. `parameters()`, `tree_map`, `tree_flatten`으로 들여다본다.
- 학습 루프는 `nn.value_and_grad` → `optimizer.update` → `mx.eval(model.parameters(), optimizer.state)` 순서다.
- `freeze()`한 파라미터는 `trainable_parameters()`에서 빠지고 기울기를 계산하지 않는다.

## 다음 편

[mlx-lm으로 언어 모델 실행하기]({{ '/ai/mlx/mlx-lm/' | relative_url }})에서는 `mlx-lm`의 모델 코드로 언어 모델을 만들고 실행해 본다. 이번 글의 `Module`과 파라미터 트리가 언어 모델에서 어떻게 쓰이는지 이어서 본다.

함께 읽으면 좋은 글:

- [MLX 자동 미분과 학습 루프]({{ '/ai/mlx/training-loop/' | relative_url }}) — 파라미터를 직접 다루는 학습 루프
- [MLX 지연 평가와 성능 측정]({{ '/ai/mlx/lazy-evaluation/' | relative_url }}) — `mx.eval`이 필요한 이유

## 참고

- [MLX Neural Networks](https://ml-explore.github.io/mlx/build/html/python/nn.html) — `Module`, 파라미터, `nn.value_and_grad`의 동작
- [MLX nn.Linear](https://ml-explore.github.io/mlx/build/html/python/nn/_autosummary/mlx.nn.Linear.html) — 계산식, shape, 초기값 분포
- [MLX Module.freeze](https://ml-explore.github.io/mlx/build/html/python/nn/_autosummary/mlx.nn.Module.freeze.html) — 얼리기의 정의
- [MLX Optimizers](https://ml-explore.github.io/mlx/build/html/python/optimizers.html) — `update`와 `mx.eval(model.parameters(), optimizer.state)` 예제
- [MLX optimizers.SGD](https://ml-explore.github.io/mlx/build/html/python/optimizers/_autosummary/mlx.optimizers.SGD.html) — SGD 업데이트 식과 기본값
- [MLX 설치 문서](https://ml-explore.github.io/mlx/build/html/install.html) — Linux CPU 설치(`mlx[cpu]`)
- [ml-explore/mlx 저장소](https://github.com/ml-explore/mlx) — 위 문서의 원본(`docs/src`)과 `python/mlx/nn` 소스
