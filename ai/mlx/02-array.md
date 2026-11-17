---
title: "MLX 배열과 수치 연산"
description: "MLX 배열의 shape, dtype, stride, broadcasting, reduction과 행렬곱을 수식·실행 결과·실패 사례로 분석합니다."
parent: MLX
grand_parent: iOS
nav_order: 2
permalink: /ai/mlx/array/
last_modified_at: 2026-11-17
seo:
  type: BlogPosting
date: 2026-11-15
redirect_from:
  - /mlx/array/
first_written: 2026-11-15
last_modified_date: 2026-11-17
tags: [MLX, Python, Array]
---

# MLX 배열과 수치 연산
{: .no_toc }

{% include article-toc.md %}

배열 코드를 읽을 때 숫자만 보면 연산의 의미를 놓치기 쉽다. 입력의 shape, 각 축의 의미, dtype과 출력 shape를 함께 추적해야 한다. 특히 broadcasting이나 reduction이 끼어들면 코드가 실행돼도 의도와 다른 결과를 만들 수 있다.

이 글은 2차원 예제로 시작해 모델 입력에 자주 쓰는 배치 연산까지 확장한다. 예제는 MLX 0.32.4에서 확인했으며 Python의 리스트와 함수 문법을 알고 있다고 가정한다.

## shape와 축의 의미

```python
import mlx.core as mx

x = mx.array([[1, 2, 3], [4, 5, 6]], dtype=mx.float32)
print(x.shape)
print(x.ndim)
print(x.size)
print(x.dtype)
```

```text
(2, 3)
2
6
mlx.core.float32
```

shape는 축마다 원소가 몇 개 있는지 나타내는 튜플이다. 위 배열은 축이 2개이고, 각 길이는 2와 3이다. 축 번호는 0부터 시작한다.

2차원 예제에서는 행·열로 읽어도 되지만 고차원에서는 데이터의 의미를 따로 정의해야 한다. `(N, D)`를 샘플 N개와 특성 D개로 정했다면, 같은 shape의 다른 데이터에도 이 의미가 유지돼야 한다.

## dtype와 메모리 크기

dtype은 원소를 어떤 방식으로 표현할지 결정한다. `float32`는 원소당 4바이트, `float16`은 2바이트다. 크기가 같은 배열이라도 dtype에 따라 논리적 데이터 크기가 달라진다.

```text
논리적 데이터 크기 = 원소 수 × 원소당 바이트 수
1024 × 1024 × 4 = 4,194,304 bytes = 4 MiB
```

이 값은 배열의 논리적 원소 크기다. 실행 중 임시 버퍼, allocator 캐시, 그래프 메타데이터와 프로세스 전체 메모리까지 뜻하지 않는다.

정수 연산은 범위를 넘으면 문제가 생길 수 있고, 부동소수점은 모든 실수를 정확히 표현하지 못한다. 메모리를 줄이려고 dtype만 낮추기 전에 필요한 표현 범위와 오차를 확인한다. 특히 CPU에서 지원되는 dtype이 Apple GPU에서도 동일하게 지원된다고 가정하지 않는다.

## 배열 생성과 인덱싱

```python
zeros = mx.zeros((2, 3), dtype=mx.float32)
sequence = mx.arange(6).reshape(2, 3)

print(sequence[0].tolist())
print(sequence[:, 1].tolist())
print(sequence[1, 2].item())
```

```text
[0, 1, 2]
[1, 4]
5
```

`sequence[0]`은 첫 행, `[:, 1]`은 모든 행의 두 번째 열, `[1, 2]`는 두 번째 행의 세 번째 원소다. `:`는 해당 축의 범위를 선택하는 슬라이스 표기다.

`item()`은 원소 하나를 Python 스칼라로 꺼낸다. 원소가 여러 개인 배열에는 적용할 수 없다. 반복문마다 호출하면 장치 계산 완료를 자주 기다리게 될 수 있어 성능 경계로도 봐야 한다.

## reshape와 transpose

```python
x = mx.arange(6).reshape(2, 3)
reshaped = x.reshape(3, 2)
transposed = x.T

print(reshaped.tolist())
print(transposed.tolist())
```

```text
[[0, 1], [2, 3], [4, 5]]
[[0, 3], [1, 4], [2, 5]]
```

두 결과의 shape는 모두 `(3, 2)`지만 값의 배치는 다르다. reshape는 논리적 원소 순서를 유지하며 축 길이를 바꾸고, transpose는 축의 순서를 바꾼다. 따라서 모델의 샘플 축과 특성 축을 바꾸려는 작업에 reshape를 대신 사용하면 의미가 달라질 수 있다.

reshape는 전체 원소 수가 맞아야 한다. `(2, 3)`의 여섯 원소를 `(4, 2)`의 여덟 칸으로 바꾸는 요청은 성립하지 않는다. `-1`은 나머지 축 길이와 총 원소 수로 한 축을 추론하라는 표시다.

## stride와 데이터 배치

stride는 각 축에서 한 칸 움직일 때 실제 데이터 위치가 얼마나 바뀌는지 표현한다. 행 우선으로 연속한 2×3 배열이라면 원소 단위 stride는 보통 `(3, 1)`로 이해할 수 있다.

전치한 배열은 논리적 축과 접근 순서가 달라진다. 이처럼 shape와 메모리의 연속성은 별개의 속성이다. 모든 reshape나 transpose가 언제나 복사 없이 끝난다는 보장은 없으며, 후속 연산이 요구하는 배치에 따라 추가 처리가 필요할 수 있다.

이 차이는 소스의 일반 stride 커널과 연속 메모리 최적화 경로를 읽을 때 중요하다.

## broadcasting의 정확한 규칙

broadcasting은 shape가 다른 입력의 원소를 일정한 규칙으로 대응시킨다. 오른쪽 축부터 비교하며 두 길이가 같거나 한쪽이 1이면 호환된다. 부족한 앞쪽 축은 길이 1처럼 취급한다.

| 입력 shape | 비교 | 결과 |
| --- | --- | --- |
| `(2, 3)`와 `(3,)` | `(2, 3)`와 `(1, 3)` | `(2, 3)` |
| `(2, 1)`과 `(1, 3)` | 두 축 모두 확장 가능 | `(2, 3)` |
| `(2, 3)`와 `(2,)` | 마지막 축 3과 2 충돌 | 오류 |

```python
x = mx.array([[1, 2, 3], [4, 5, 6]], dtype=mx.float32)
offset = mx.array([10, 20, 30], dtype=mx.float32)
print((x + offset).tolist())
```

결과는 `[[11, 22, 33], [14, 25, 36]]`이다. 같은 세 원소가 두 행에 대응하지만 큰 입력 배열을 실제로 복사했다는 뜻은 아니다. backend가 shape와 stride를 활용해 접근할 수 있다.

### 실행되지만 잘못된 broadcasting

shape `(N, 1)`인 예측과 `(N,)`인 정답을 빼면 기대한 `(N,)` 대신 `(N, N)`이 생길 수 있다. N이 2라면 `(2, 1)`과 `(1, 2)`가 대응하기 때문이다.

```python
prediction = mx.array([[1.0], [2.0]])
target = mx.array([1.0, 2.0])
assert (prediction - target).shape == (2, 2)
assert (prediction.squeeze(-1) - target).shape == (2,)
```

학습 코드에서 손실이 예상과 다르면 dtype보다 먼저 이 입력 shape를 검사할 가치가 있다.

## reduction과 keepdims

reduction은 여러 원소를 합·평균·최댓값 등으로 모으는 연산이다. `axis`는 연산으로 줄일 축을 지정한다.

```python
x = mx.array([[1, 2, 3], [4, 5, 6]], dtype=mx.float32)
print(mx.sum(x, axis=0).tolist())
print(mx.sum(x, axis=1).tolist())
print(mx.mean(x, axis=1, keepdims=True).shape)
```

결과는 `[5, 7, 9]`, `[6, 15]`, `(2, 1)`이다. `keepdims=True`는 줄인 축을 길이 1로 남긴다. 이후 원래 배열과 broadcasting으로 연산할 때 의미를 유지하기 좋다.

```python
row_mean = mx.mean(x, axis=1, keepdims=True)
centered = x - row_mean
print(centered.tolist())
```

결과는 `[[-1, 0, 1], [-1, 0, 1]]`이다. 각 행의 평균 2와 5를 해당 행의 모든 원소에서 뺐다.

## 행렬곱과 모델의 shape 계약

샘플 N개, 특성 D개인 입력 `X`와 출력 특성 H개를 만드는 가중치 `W`를 생각하자.

```text
X: (N, D)
W: (D, H)
b: (H,)
Y = X @ W + b: (N, H)
```

행렬곱에서는 안쪽 차원 D가 맞아야 한다. bias b는 각 샘플의 H개 출력에 broadcasting된다. 이것이 기본적인 선형 계층의 구조다.

```python
x = mx.array([[1, 2, 3], [4, 5, 6]], dtype=mx.float32)
print((x @ x.T).tolist())
```

출력은 `[[14, 32], [32, 77]]`이다. 첫 원소 14는 `1² + 2² + 3²`, 비대각 원소 32는 `1×4 + 2×5 + 3×6`이다. shape만 아니라 계산 의미까지 확인한다.

## 수치 결과 검증

부동소수점 결과 비교에는 보통 절대·상대 오차 기준을 함께 사용한다. 개념적으로 `|actual - reference| ≤ atol + rtol × |reference|` 같은 기준이다. 값이 0 근처인 경우 절대 오차가 중요해진다.

`float32`와 `float16`, 서로 다른 장치의 결과가 바이트 단위로 같아야 한다고 요구하면 정상적인 작은 차이도 실패로 볼 수 있다. 반대로 큰 허용 오차는 실제 오류를 숨긴다. 데이터의 단위와 허용 가능한 오차를 먼저 정한다.

[재현 스크립트]({{ '/assets/examples/mlx/reproduce.py' | relative_url }})는 broadcasting, 축 합계, 평균 제거, 행렬곱과 자동 미분의 작은 정답 사례를 assertion으로 검사한다. 여기서 확인한 결과는 큰 모델 전체의 수치 안정성을 대신하지 않는다.

## 참고와 후속 글

- [MLX 지연 평가와 성능 측정]({{ '/ai/mlx/lazy-evaluation/' | relative_url }})
- [MLX Array API](https://ml-explore.github.io/mlx/build/html/python/array.html)
- [MLX Indexing Arrays](https://ml-explore.github.io/mlx/build/html/usage/indexing.html)
- [MLX Numerical Precision](https://ml-explore.github.io/mlx/build/html/usage/numerical_precision.html)
