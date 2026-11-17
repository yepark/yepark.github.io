---
title: "3. 게으른 계산: MLX는 왜 계산을 미룰까"
parent: MLX
grand_parent: iOS
nav_order: 3
permalink: /ai/mlx/lazy-evaluation/
first_written: 2026-11-16
last_modified_date: 2026-11-17
tags: [MLX, Python, Lazy-Evaluation]
---

# 게으른 계산: MLX는 왜 계산을 미룰까
{: .no_toc }

{% include article-toc.md %}

## 계산식 생성과 결과 관찰 구분하기

일반 Python 숫자의 `1 + 2`와 MLX 배열의 덧셈은 실행 모델이 다르다. MLX는 결과를 어떻게 만들지 기록하고, 실제 값이 필요한 경계에서 평가한다.

시간을 비교할 때 입력 생성 비용과 결과를 기다리는 비용을 분리해야 한다. 본문 측정값은 해당 환경의 예시다. 같은 숫자가 나오지 않아도 ‘그래프를 만드는 시간’과 ‘계산을 완료하는 시간’의 차이를 관찰하면 학습 목적을 달성한 것이다.

MLX에서 `c = a @ b`라고 쓰면, 그 줄에서는 **곱셈을 하지 않는다.** 공식 문서는 이렇게 말한다.

> MLX에서 연산을 해도 실제 계산은 일어나지 않는다. 대신 계산 그래프가 기록된다. 실제 계산은 `eval`을 할 때만 일어난다.

이것을 **게으른 계산(lazy evaluation)**이라고 한다.

{: .tip }
식당 주문서를 떠올리면 쉽다. 손님이 주문할 때마다 바로 요리하지 않고, 주문서에 적어 두었다가 "이제 내 주세요" 하는 순간 한꺼번에 요리한다. `c = a @ b`는 주문서에 적는 것이고, `mx.eval(c)`가 "내 주세요"다.

이 글의 결과는 모두 M4 Mac, MLX 0.32.4에서 실행한 것이다. 걸린 시간은 실행할 때마다 조금씩 달라진다.

## 정말 계산을 안 할까: 시간 재 보기

4000 × 4000 크기 표 두 개를 곱해 보자. 숫자가 1600만 개씩 들어 있는 큰 계산이다.

```python
import time
import mlx.core as mx

a = mx.random.normal((4000, 4000))
b = mx.random.normal((4000, 4000))
mx.eval(a, b)

t0 = time.perf_counter()
c = a @ b
t1 = time.perf_counter()
mx.eval(c)
t2 = time.perf_counter()
mx.eval(c)
t3 = time.perf_counter()

print(f"c = a @ b  : {(t1 - t0) * 1000:.3f} ms")
print(f"mx.eval(c) : {(t2 - t1) * 1000:.3f} ms")
print(f"한 번 더   : {(t3 - t2) * 1000:.3f} ms")
```

```text
c = a @ b  : 0.049 ms
mx.eval(c) : 146.062 ms
한 번 더   : 0.024 ms
```

같은 코드를 한 번 더 실행했을 때는 `mx.eval(c)`가 42.791 ms였다. 숫자는 달라도 모양은 같다.

- `c = a @ b` 줄은 **거의 0초**다. 곱셈을 하지 않고 "곱하기로 했다"고 적어만 뒀기 때문이다.
- 시간이 걸리는 곳은 **`mx.eval(c)`**다. 여기서 진짜 곱셈을 한다.
- 이미 계산한 `c`에 `mx.eval`을 또 부르면 **아무 일도 하지 않는다.** 공식 문서도 같은 배열에 `eval`을 여러 번 불러도 괜찮고, 사실상 아무 일도 안 한다고 설명한다.

{: .note }
앞에서 `mx.eval(a, b)`를 먼저 부른 이유도 같다. `mx.random.normal`도 바로 숫자를 만들지 않는다. 미리 만들어 두지 않으면 곱셈 시간에 무작위 숫자 만드는 시간까지 섞인다.

### 메모리로도 확인할 수 있다

`mx.get_active_memory()`는 MLX가 **지금 쓰고 있는 메모리(바이트)**를 알려 준다.

```python
import mlx.core as mx

def mb():
    return mx.get_active_memory() / 1e6

x = mx.ones((1000, 1000))
print(f"만든 직후 : {mb():.1f} MB")
mx.eval(x)
print(f"eval 후   : {mb():.1f} MB")
```

```text
만든 직후 : 0.0 MB
eval 후   : 4.0 MB
```

`float32` 숫자 하나는 4바이트다. 100만 개면 4 MB다. `mx.ones`를 부른 직후에는 **메모리를 하나도 쓰지 않았다.** `eval`을 해야 비로소 숫자를 담을 자리가 생긴다.

## 계산 그래프: 주문서의 정체

MLX가 "적어 둔다"는 것은 **계산 그래프(compute graph)**를 만든다는 뜻이다. 계산 그래프는 **"어떤 값에 어떤 계산을 해서 무엇을 만드는지" 이어 놓은 순서도**다.

```python
d = (a + b) * 2
```

이 한 줄은 이런 순서도가 된다.

```text
a ─┐
   ├─ 더하기 ─┐
b ─┘          ├─ 곱하기 → d
         2 ───┘
```

`eval`을 하면 MLX는 이 순서도를 따라가며 계산한다. 공식 문서는 게으른 계산의 좋은 점을 두 가지 든다.

1. **계산 그래프를 바꿀 수 있다.** 계산하기 전에 순서도가 있으니, 5편에서 배울 `mx.grad`(자동 미분) 같은 기능이 이 순서도를 보고 일한다.
2. **쓰는 것만 계산한다.** 다음 절에서 직접 확인한다.

## 쓰지 않는 결과는 계산하지 않는다

결과를 두 개 돌려주는 함수가 있다. 하나는 가볍고, 하나는 무겁다.

```python
import time
import mlx.core as mx

x = mx.random.normal((4000, 4000))
mx.eval(x)

def fun(x):
    small = x.sum()
    big = x @ x @ x @ x
    return small, big

t0 = time.perf_counter()
small, _ = fun(x)
mx.eval(small)
t1 = time.perf_counter()
small, big = fun(x)
mx.eval(small, big)
t2 = time.perf_counter()
print(f"small만  : {(t1 - t0) * 1000:.1f} ms")
print(f"둘 다    : {(t2 - t1) * 1000:.1f} ms")
```

```text
small만  : 2.1 ms
둘 다    : 125.7 ms
```

첫 번째는 `big`을 `_`로 버리고 `small`만 `eval`했다. 그러자 **무거운 곱셈 세 번을 아예 하지 않았다.** 그래서 60배쯤 빠르다.

{: .warning }
공식 문서는 이 방법을 조심해서 쓰라고 한다. `big`은 계산되지 않지만, **`big`의 계산 그래프는 여전히 만들어지고**, 그것에도 비용이 든다.

## 계산이 저절로 일어나는 순간

지금까지 1편과 2편에서는 `mx.eval` 없이도 결과가 잘 나왔다. **`print`가 계산을 시켰기 때문이다.** 공식 문서에 따르면 아래 경우에 계산이 저절로 일어난다.

| 하는 일 | 예 |
| --- | --- |
| 배열을 출력할 때 | `print(x)` |
| NumPy 배열로 바꿀 때 | `np.array(x)` |
| `memoryview`로 메모리에 접근할 때 | `memoryview(x)` |
| 파일로 저장할 때 | `mx.save("x.npy", x)` |
| 숫자 하나를 꺼낼 때 | `x.item()` |
| 숫자 하나짜리 배열을 조건문에 쓸 때 | `if x > 0:` |

`print`가 계산을 시키는지 메모리로 확인해 보자. `print`는 안에서 `str(x)`로 글자를 만든다.

```python
import mlx.core as mx

def mb():
    return mx.get_active_memory() / 1e6

x = mx.ones((1000, 1000))
print(f"만든 직후  : {mb():.1f} MB")
s = str(x)  # print가 하는 일과 같다
print(f"str(x) 후  : {mb():.1f} MB")
```

```text
만든 직후  : 0.0 MB
str(x) 후  : 4.0 MB
```

`mx.eval`을 부르지 않았는데도 메모리가 4 MB가 됐다. 글자로 바꾸려면 숫자가 있어야 하니 계산을 한 것이다.

조건문과 `.item()`도 해 보자.

```python
import mlx.core as mx

y = mx.array([1, 2, 3]) * 2
print(type(y.sum() > 5))
if y.sum() > 5:
    print("5보다 크다")

v = y.sum().item()
print(v, type(v))
```

```text
<class 'mlx.core.array'>
5보다 크다
12 <class 'int'>
```

`y.sum() > 5`는 `True`가 아니라 **MLX 배열**이다. `if`는 참인지 거짓인지 알아야 하니, 그 자리에서 계산을 한다.

{: .warning }
공식 문서는 **숫자 하나짜리 배열을 조건문에 쓰면 계산이 일어난다**고 경고한다. 코드는 맞게 돌아가지만, 이런 계산이 너무 자주 일어나면 아주 느려질 수 있다.

## `mx.eval`은 언제 불러야 할까

공식 문서는 이것을 **저울질**이라고 설명한다.

- **너무 자주 부르면** 손해다. `eval`을 한 번 할 때마다 정해진 준비 비용이 든다.
- **너무 안 부르면** 그래프가 아주 커진다. 그래프 크기에 따라 늘어나는 작은 비용이 있어서, 아주 큰 그래프도 비용이 크다.

덧셈 1000번을 하는 반복문으로 비교해 보자. 한쪽은 매번 `eval`하고, 다른 쪽은 마지막에 한 번만 한다.

```python
import time
import mlx.core as mx

def run(every_step):
    a = mx.zeros((100,))
    b = mx.ones((100,))
    t0 = time.perf_counter()
    for _ in range(1000):
        a = a + b
        if every_step:
            mx.eval(a)
    mx.eval(a)
    ms = (time.perf_counter() - t0) * 1000
    return f"{ms:.1f} ms, a[0] = {a[0].item()}"

run(True)  # 첫 실행 준비
for _ in range(3):
    print("매번 eval :", run(True))
    print("마지막만  :", run(False))
```

```text
매번 eval : 177.8 ms, a[0] = 1000.0
마지막만  : 2.5 ms, a[0] = 1000.0
매번 eval : 181.3 ms, a[0] = 1000.0
마지막만  : 2.2 ms, a[0] = 1000.0
매번 eval : 168.3 ms, a[0] = 1000.0
마지막만  : 2.1 ms, a[0] = 1000.0
```

결과(`a[0] = 1000.0`)는 똑같다. 그런데 매번 `eval`한 쪽이 **70배쯤 느리다.** 덧셈 하나는 아주 작은 일이라, 일보다 `eval`의 준비 비용이 훨씬 컸다.

그렇다고 끝없이 미루면 안 된다. 공식 문서가 주는 기준은 이렇다.

- `eval` 한 번에 **수십 개에서 수천 개 연산**까지는 잘 동작한다.
- 숫자 계산에는 **바깥 반복문**이 있다. 모델 학습이라면 "데이터 한 묶음마다 한 번" 도는 반복문이다. 이 **바깥 반복문 한 바퀴마다 `eval`을 한 번** 부르는 것이 자연스럽다.

{: .question }
위 반복문에서 덧셈을 100만 번 하면서 마지막에만 `eval`하면 어떻게 될까? 그래프에 연산이 100만 개 쌓인다. 공식 문서가 말한 "수천 개"를 훨씬 넘는다.

### 여러 배열을 한 번에 `eval`하기

`mx.eval`에는 배열 여러 개를 한꺼번에 넘길 수 있다. 딕셔너리나 리스트로 묶어서 넘겨도 된다. 배열이 아닌 값은 그냥 건너뛴다.

```python
y = mx.array([1, 2, 3]) * 2
params = {"w": y + 1, "b": [y * 10, "메모"]}
mx.eval(params)
print(params)
```

```text
{'w': array([3, 5, 7], dtype=int32), 'b': [array([20, 40, 60], dtype=int32), '메모']}
```

`mlx.nn` 모델의 `parameters()`도 딕셔너리를 돌려준다. 그래서 공식 문서의 학습 예제는 반복문 한 바퀴마다 `mx.eval(loss, model.parameters())`로 손실과 가중치를 한 번에 계산한다.

## 정리

- MLX는 연산을 하면 **바로 계산하지 않고 계산 그래프에 적어 둔다.**
- 실제 계산은 **`mx.eval`을 할 때** 일어난다. 계산 전에는 메모리도 쓰지 않는다.
- **쓰지 않는 결과는 계산하지 않는다.** 다만 그래프를 만드는 비용은 든다.
- `print`, NumPy 변환, 저장, `.item()`, **조건문**은 계산을 저절로 시킨다.
- `eval`을 **너무 자주 부르면 느리다.** 바깥 반복문 한 바퀴마다 한 번이 기준이다.
- 같은 배열에 `eval`을 여러 번 불러도 괜찮다. 두 번째부터는 아무 일도 안 한다.

## 다음 편

다음 편에서는 이 계산 그래프가 실제 소스에서 어떻게 만들어지는지 살펴본다. Python의 덧셈이 C++ 배열 노드와 Metal 실행 경로로 이어지는 순서를 따라간다.

→ [4. MLX 소스 해설: Python의 덧셈이 GPU에서 실행되기까지]({{ '/ai/mlx/source-walkthrough/' | relative_url }})

## 참고

- [MLX: Lazy Evaluation](https://ml-explore.github.io/mlx/build/html/usage/lazy_evaluation.html)
- [MLX: Quick Start Guide](https://ml-explore.github.io/mlx/build/html/usage/quick_start.html)
- [MLX: mlx.core.eval](https://ml-explore.github.io/mlx/build/html/python/_autosummary/mlx.core.eval.html)
- [MLX: mlx.core.get_active_memory](https://ml-explore.github.io/mlx/build/html/python/_autosummary/mlx.core.get_active_memory.html)
