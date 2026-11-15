---
title: "2. 배열: MLX에서 숫자를 담는 그릇"
parent: MLX
grand_parent: AI
nav_order: 2
permalink: /ai/mlx/array/
first_written: 2026-11-15
last_modified_date: 2026-11-15
tags: [MLX, Python, Array]
---

# 배열: MLX에서 숫자를 담는 그릇
{: .no_toc }

<details open markdown="block">
  <summary>목차</summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

MLX로 하는 계산은 **배열(array)**에 숫자를 담아서 한다. 1편에서 `mx.array([1, 2, 3])`으로 만든 것이 바로 배열이다. 그래서 MLX를 쓰려면 배열부터 편하게 다룰 수 있어야 한다.

배열은 **같은 종류의 숫자를 줄과 칸에 맞춰 담은 그릇**이다. 엑셀 표를 떠올리면 된다.

이 글의 결과는 모두 M4 Mac, MLX 0.32.4에서 실행한 것이다.

## 배열의 두 가지 정보: 모양과 종류

배열을 만들면 MLX는 두 가지를 기억한다.

```python
import mlx.core as mx

a = mx.array([1, 2, 3])
b = mx.array([1.5, 2.5, 3.5])

print(a.shape, a.dtype)
print(b.shape, b.dtype)
```

```text
(3,) mlx.core.int32
(3,) mlx.core.float32
```

- **`shape`(모양)**: 숫자가 어떻게 놓여 있는지. `(3,)`은 "한 줄에 3개"라는 뜻이다.
- **`dtype`(종류)**: 어떤 숫자가 들어 있는지. `int32`는 정수, `float32`는 소수점이 있는 숫자다.

표 모양(2차원)으로 만들면 이렇다.

```python
m = mx.array([[1, 2, 3],
              [4, 5, 6]])

print(m.shape, m.ndim, m.size)
```

```text
(2, 3) 2 6
```

- `shape`가 `(2, 3)`이면 **2줄 3칸**이다. 순서는 항상 (줄, 칸)이다.
- `ndim`은 **몇 차원인지**다. 한 줄이면 1, 표면 2.
- `size`는 **숫자가 모두 몇 개인지**다. 2 × 3 = 6.

{: .tip }
`shape`를 읽는 법: 괄호 안 숫자 개수가 차원 수이고, 각 숫자가 그 방향의 길이다. `(2, 3)`은 "2줄짜리, 한 줄에 3칸".

### NumPy와 다른 점: 소수는 float32

NumPy를 써 봤다면 하나 주의할 점이 있다.

```python
import numpy as np
print(np.array([1.5]).dtype)
```

```text
float64
```

NumPy는 소수를 기본으로 `float64`에 담는다. **MLX는 `float32`에 담는다.** 위에서 `b`의 `dtype`이 `float32`였던 것을 확인할 수 있다.

## 배열 만드는 방법

매번 숫자를 손으로 적을 필요는 없다. 자주 쓰는 방법들이다.

```python
print(mx.zeros((2, 3)))
print(mx.ones((2, 2), dtype=mx.int32))
print(mx.full((2, 2), 7))
```

```text
array([[0, 0, 0],
       [0, 0, 0]], dtype=float32)
array([[1, 1],
       [1, 1]], dtype=int32)
array([[7, 7],
       [7, 7]], dtype=int32)
```

- `mx.zeros(모양)`: 0으로 채운 배열. 따로 말하지 않으면 `float32`다.
- `mx.ones(모양, dtype=...)`: 1로 채운 배열. `dtype`으로 종류를 정할 수 있다.
- `mx.full(모양, 값)`: 원하는 값으로 채운 배열.

연속된 숫자는 `mx.arange`로 만든다. Python의 `range`와 같은 방식이다.

```python
print(mx.arange(5))
print(mx.arange(0, 1, 0.25))
```

```text
array([0, 1, 2, 3, 4], dtype=int32)
array([0, 0.25, 0.5, 0.75], dtype=float32)
```

`mx.arange(시작, 끝, 간격)`이고, **끝 값은 들어가지 않는다.** 그래서 `0, 0.25, 0.5, 0.75`까지만 나오고 1은 없다.

무작위 숫자로 채운 배열도 만들 수 있다.

```python
mx.random.seed(0)
r = mx.random.normal((2, 3))
print(r.shape, r.dtype)
```

```text
(2, 3) mlx.core.float32
```

`mx.random.seed(0)`은 **무작위 결과를 매번 같게 만드는 스위치**다. 같은 seed를 쓰면 다시 실행해도 같은 숫자가 나온다.

## 종류 바꾸기

`astype`으로 배열의 종류를 바꾼다.

```python
x = mx.array([1, 2, 3])
y = x.astype(mx.float32)
print(y, y.dtype)
```

```text
array([1, 2, 3], dtype=float32) mlx.core.float32
```

나눗셈은 결과 종류가 바뀌니 주의한다.

```python
print(mx.array([1, 2, 3]) / 2)
print(mx.array([1, 2, 3]) // 2)
```

```text
array([0.5, 1, 1.5], dtype=float32)
array([0, 1, 1], dtype=int32)
```

- `/`는 정수 배열이어도 **소수(`float32`) 결과**를 낸다.
- `//`는 **몫만 남긴 정수** 결과를 낸다.

### float64는 GPU에서 안 된다

```python
f = mx.array([1.0], dtype=mx.float64)
print(f + 1)
```

```text
ValueError: float64 is not supported on the GPU
```

MLX의 기본 장치는 GPU인데, **GPU에서는 `float64`를 쓸 수 없다.** CPU에서 계산하라고 지정하면 된다.

```python
f = mx.array([1.0], dtype=mx.float64)
print(mx.add(f, 1, stream=mx.cpu))
```

```text
array([2], dtype=float64)
```

{: .note }
이 시리즈의 예제는 `float32`로 계산한다. CPU와 GPU를 고르는 방법은 4편에서 자세히 다룬다.

## 원하는 부분만 꺼내기

Python 리스트처럼 `[]`로 꺼낸다. 2차원 배열은 `[줄, 칸]` 순서다.

```python
m = mx.array([[1, 2, 3],
              [4, 5, 6]])

print(m[0])      # 0번 줄
print(m[1, 2])   # 1번 줄, 2번 칸
print(m[:, 1])   # 모든 줄의 1번 칸
print(m[0, 1:])  # 0번 줄, 1번 칸부터 끝까지
print(m[-1])     # 마지막 줄
```

```text
array([1, 2, 3], dtype=int32)
array(6, dtype=int32)
array([2, 5], dtype=int32)
array([2, 3], dtype=int32)
array([4, 5, 6], dtype=int32)
```

헷갈리는 것은 `:` 하나다. **`:`는 "그 방향 전부"**라는 뜻이다. `m[:, 1]`은 "줄은 전부, 칸은 1번"이니 세로 한 줄을 꺼낸다.

| 코드 | 읽는 법 | 결과 |
| --- | --- | --- |
| `m[0]` | 0번 줄 | `[1, 2, 3]` |
| `m[1, 2]` | 1번 줄 2번 칸 | `6` |
| `m[:, 1]` | 모든 줄의 1번 칸 | `[2, 5]` |
| `m[0, 1:]` | 0번 줄의 1번 칸부터 | `[2, 3]` |

## 모양 바꾸기

숫자는 그대로 두고 **줄과 칸만 다시 나누는 것**이 `reshape`다.

```python
v = mx.arange(6)

print(v.reshape(2, 3))
print(v.reshape(3, -1))
```

```text
array([[0, 1, 2],
       [3, 4, 5]], dtype=int32)
array([[0, 1],
       [2, 3],
       [4, 5]], dtype=int32)
```

`-1`은 **"나머지는 알아서 계산해 줘"**다. 숫자가 6개이고 3줄이니 칸은 2로 정해진다.

줄과 칸을 서로 바꾸는 것은 `.T`(transpose)다.

```python
print(m.T)
print(m.T.shape)
```

```text
array([[1, 4],
       [2, 5],
       [3, 6]], dtype=int32)
(3, 2)
```

{: .tip }
`.T`는 표를 대각선으로 뒤집는 것이다. 2줄 3칸이 3줄 2칸이 된다.

## 모양이 달라도 계산되는 경우: 브로드캐스팅

모양이 다른 배열끼리 더하면 어떻게 될까?

```python
print(m + 10)
print(m + mx.array([100, 200, 300]))
```

```text
array([[11, 12, 13],
       [14, 15, 16]], dtype=int32)
array([[101, 202, 303],
       [104, 205, 306]], dtype=int32)
```

- `m + 10`: 숫자 하나가 **모든 칸에** 더해졌다.
- `m + [100, 200, 300]`: 한 줄짜리가 **각 줄마다** 더해졌다.

작은 쪽을 큰 쪽 모양에 맞게 **복사해서 늘린 것처럼** 계산해 준다. 이것을 **브로드캐스팅**이라고 한다. 방송(broadcast)처럼 하나를 여러 곳에 퍼뜨린다는 뜻이다.

하지만 아무 모양이나 되는 것은 아니다.

```python
print(m + mx.array([1, 2]))
```

```text
ValueError: [broadcast_shapes] Shapes (2,3) and (2) cannot be broadcast.
```

맞추는 규칙은 **오른쪽 끝 숫자부터 비교**하는 것이다. 두 숫자가 같거나, 한쪽이 1이면 늘릴 수 있다.

| 왼쪽 | 오른쪽 | 끝 숫자 비교 | 결과 |
| --- | --- | --- | --- |
| `(2, 3)` | `(3,)` | 3 = 3 | 된다 |
| `(2, 3)` | `(2,)` | 3 ≠ 2 | 안 된다 |
| `(2, 3)` | `(2, 1)` | 3과 1 → 1을 늘림, 2 = 2 | 된다 |

마지막 경우를 실행해 보면 세로 한 줄 `[[10], [20]]`이 각 칸으로 퍼진다.

```python
print(m + mx.array([[10], [20]]))
```

```text
array([[11, 12, 13],
       [24, 25, 26]], dtype=int32)
```

## 모아서 계산하기

합계, 최댓값, 평균처럼 여러 숫자를 하나로 모으는 계산이다.

```python
print(m.sum(), m.sum(axis=0), m.sum(axis=1))
print(m.max(), m.astype(mx.float32).mean())
```

```text
array(21, dtype=int32) array([5, 7, 9], dtype=int32) array([6, 15], dtype=int32)
array(6, dtype=int32) array(3.5, dtype=float32)
```

`axis`가 처음엔 헷갈린다. **`axis`는 "없앨 방향"**이라고 기억하면 쉽다.

- `axis` 없음: 전부 더한다. `1+2+3+4+5+6 = 21`
- `axis=0`: **줄 방향을 없앤다.** 위아래로 더해서 `[1+4, 2+5, 3+6] = [5, 7, 9]`
- `axis=1`: **칸 방향을 없앤다.** 옆으로 더해서 `[1+2+3, 4+5+6] = [6, 15]`

## Python 값이나 NumPy로 꺼내기

계산이 끝나면 결과를 보통의 Python 값으로 꺼내야 할 때가 있다.

```python
print(m.tolist(), type(m.tolist()))

s = m.sum()
print(s.item(), type(s.item()))

print(np.array(m), np.array(m).dtype)
```

```text
[[1, 2, 3], [4, 5, 6]] <class 'list'>
21 <class 'int'>
[[1 2 3]
 [4 5 6]] int32
```

- `.tolist()`: Python 리스트로
- `.item()`: 숫자 **하나**짜리 배열을 Python 숫자로
- `np.array(...)`: NumPy 배열로

## 같은 배열을 가리킨다

```python
c = mx.array([1, 2, 3])
d = c
d[0] = 99
print(c, d)
```

```text
array([99, 2, 3], dtype=int32) array([99, 2, 3], dtype=int32)
```

`d = c`는 배열을 **복사하지 않는다.** `c`와 `d`는 **같은 배열에 붙은 이름표 두 개**다. 그래서 `d`를 바꾸면 `c`도 바뀐다. Python 리스트와 같은 동작이다.

{: .warning }
원본을 지키고 싶다면 `d = c`처럼 이름만 하나 더 붙이지 말고, 계산 결과로 새 배열을 만들어 쓴다.

## 정리

- 배열은 **같은 종류의 숫자를 줄과 칸에 맞춰 담은 그릇**이다.
- `shape`는 모양(줄, 칸), `dtype`은 숫자 종류다.
- MLX는 소수를 기본으로 **`float32`**에 담는다. NumPy는 `float64`다.
- **GPU에서는 `float64`를 쓸 수 없다.** 필요하면 `stream=mx.cpu`로 계산한다.
- `[줄, 칸]`으로 꺼내고, `:`는 "그 방향 전부"다.
- `reshape`로 모양을 바꾸고, `-1`은 "알아서 계산"이다.
- 모양이 달라도 **오른쪽 끝부터 같거나 1이면** 브로드캐스팅으로 계산된다.
- `axis`는 **없앨 방향**이다.

## 다음 편

1편에서 `a + b`를 하면 바로 결과가 나오는 것처럼 보였다. 그런데 사실 MLX는 그 순간 **계산을 하지 않는다.** 다음 편에서는 MLX가 계산을 미뤘다가 필요할 때 한 번에 하는 **게으른 계산**을 다룬다.

## 참고

- [MLX: Quick Start Guide](https://ml-explore.github.io/mlx/build/html/usage/quick_start.html)
- [MLX: Array](https://ml-explore.github.io/mlx/build/html/python/array.html)
- [MLX: Data Types](https://ml-explore.github.io/mlx/build/html/python/data_types.html)
- [MLX: Indexing Arrays](https://ml-explore.github.io/mlx/build/html/usage/indexing.html)
