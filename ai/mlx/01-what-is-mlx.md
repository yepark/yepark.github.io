---
title: "1. MLX가 뭐고, 내 Mac에서 처음 돌려 보기"
parent: MLX
grand_parent: AI
nav_order: 1
permalink: /ai/mlx/what-is-mlx/
redirect_from:
  - /mlx/what-is-mlx/
first_written: 2026-11-15
last_modified_date: 2026-11-15
tags: [MLX, Python, Apple-Silicon]
---

# MLX가 뭐고, 내 Mac에서 처음 돌려 보기
{: .no_toc }

{% include article-toc.md %}

## MLX를 한 문장으로

> **MLX는 Apple 실리콘 Mac에서 숫자 계산을 빠르게 해 주는 Python 도구다.**

Apple의 머신러닝 연구팀이 만들었고, 누구나 무료로 쓸 수 있다.

"머신러닝 도구"라고 하면 어렵게 들린다. 그런데 머신러닝의 속을 열어 보면 대부분 **엄청나게 많은 숫자 계산**이다.

- 사진은 픽셀마다 색깔 숫자가 적힌 큰 표다.
- 문장도 단어마다 번호를 붙이면 숫자 목록이 된다.
- 모델을 학습시킨다는 것은 이 숫자들을 곱하고 더하는 일을 아주 많이 반복하는 것이다.

그래서 머신러닝 도구의 핵심 일은 **"큰 숫자 묶음을 빨리 계산하기"**다. MLX는 이 일을 Mac에서 잘하도록 만든 도구다.

{: .tip }
NumPy를 써 봤다면 "Mac GPU에서 돌아가는 NumPy"라고 생각해도 처음에는 충분하다. 사용법이 많이 닮았다.

## 왜 하필 MLX일까

머신러닝 도구는 PyTorch처럼 유명한 것이 이미 많다. 그래도 Mac에서 MLX를 쓰는 이유는 **처음부터 Apple 실리콘(M1, M2, M3, M4 칩)에 맞춰 만들었기 때문**이다.

특징을 세 가지만 기억하면 된다. 하나씩 이 시리즈에서 자세히 다룬다.

| 특징 | 쉽게 말하면 | 자세히 |
| --- | --- | --- |
| NumPy와 비슷한 사용법 | 이미 아는 방식으로 쓸 수 있다 | 2편 |
| 계산을 미뤘다가 한 번에 한다 | 필요할 때까지 계산하지 않는다 | 3편 |
| CPU와 GPU가 같은 메모리를 쓴다 | 데이터를 옮기느라 기다리지 않는다 | 4편 |

세 번째가 특히 중요하다. 그래픽카드가 따로 달린 컴퓨터에서는 CPU용 메모리와 GPU용 메모리가 따로 있어서, GPU로 계산하려면 데이터를 복사해서 옮겨야 한다. Apple 실리콘은 CPU와 GPU가 **같은 메모리를 함께 쓴다.** 두 사람이 각자 책상을 쓰면서 서류를 주고받는 대신, 큰 책상 하나를 같이 쓰는 것과 같다. MLX는 이 구조를 그대로 활용한다.

## 준비물 확인

MLX를 쓰려면 세 가지가 필요하다.

1. **Apple 실리콘 Mac** (M1 이상)
2. **macOS 14 이상**
3. **Python 3.10 이상** (Apple 실리콘용으로 설치된 Python)

터미널에서 하나씩 확인해 보자.

```bash
# 1. 칩 확인: "Apple M1" 같은 글자가 나오면 된다
sysctl -n machdep.cpu.brand_string

# 2. macOS 버전 확인: 14 이상이면 된다
sw_vers -productVersion

# 3. Python 버전 확인: 3.10 이상이어야 한다
python3 --version
```

{: .warning }
이 글을 쓴 Mac(macOS 15.6)에 기본으로 들어 있는 `python3`는 **3.9.6**이었다. 이 Python으로 `pip install mlx`를 하자 **오류 없이 예전 버전(0.29.3)이 설치됐다.** 최신 버전은 0.32.4다. 버전이 3.10보다 낮다면 아래 방법으로 새 Python을 쓰자.

## 설치하기

여기서는 `uv`라는 도구를 쓴다. `uv`는 **Python 버전과 패키지를 대신 챙겨 주는 도구**다. Mac에 깔린 Python 버전을 신경 쓰지 않아도 된다.

```bash
# uv 설치 (한 번만 하면 된다)
brew install uv

# 공부용 폴더 만들기
mkdir mlx-study && cd mlx-study

# Python 3.12로 가상환경 만들기
uv venv -p 3.12

# 가상환경 켜기
source .venv/bin/activate

# MLX 설치
uv pip install mlx
```

"가상환경"이라는 말이 나왔다. **가상환경은 이 폴더 전용 Python 상자**다. 여기에 설치한 패키지는 이 상자 안에만 있어서, 다른 프로젝트를 망가뜨리지 않는다. 터미널을 새로 열면 `source .venv/bin/activate`를 다시 해야 상자 안으로 들어간다.

설치가 잘 됐는지 확인하자.

```bash
python -c "import mlx.core as mx; print(mx.__version__)"
```

`0.32.4`처럼 버전 숫자가 나오면 성공이다.

## 첫 계산 해 보기

`first.py` 파일을 만들고 아래 코드를 붙여 넣는다.

```python
import mlx.core as mx

a = mx.array([1, 2, 3])
b = mx.array([10, 20, 30])

print(a + b)
print(a * 2)
```

실행하면 이렇게 나온다.

```bash
python first.py
```

```text
array([11, 22, 33], dtype=int32)
array([2, 4, 6], dtype=int32)
```

한 줄씩 보자.

- `import mlx.core as mx`: MLX의 핵심 기능을 `mx`라는 짧은 이름으로 불러온다. 앞으로 거의 모든 코드가 이 줄로 시작한다.
- `mx.array([1, 2, 3])`: 숫자 세 개를 MLX **배열**에 담는다. 배열은 숫자를 줄 세워 담은 그릇이다.
- `a + b`: 같은 자리에 있는 숫자끼리 더한다. 1+10, 2+20, 3+30.
- `a * 2`: 모든 숫자에 2를 곱한다. `for` 문을 쓰지 않아도 된다.

결과 끝에 붙은 `dtype=int32`는 **"이 배열에는 정수가 들어 있다"**는 표시다. 2편에서 자세히 본다.

{: .note }
Python 리스트로 `[1, 2, 3] + [10, 20, 30]`을 하면 더해지지 않고 `[1, 2, 3, 10, 20, 30]`처럼 이어 붙여진다. MLX 배열은 **같은 자리끼리 계산**한다. 이 차이가 숫자 계산 도구를 쓰는 첫 번째 이유다.

## 조금 더: 표 모양 숫자 계산

머신러닝에서는 숫자 한 줄보다 **표 모양(행렬)**을 훨씬 많이 쓴다. 표 두 개를 곱하는 것도 한 줄이면 된다.

```python
import mlx.core as mx

m = mx.array([[1.0, 2.0],
              [3.0, 4.0]])

print(m @ m)
```

```text
array([[7, 10],
       [15, 22]], dtype=float32)
```

`@`는 **행렬 곱**이다. 지금은 계산 방법을 몰라도 된다. "머신러닝 모델 안에서 아주 자주 쓰이는 계산"이라는 것만 기억하자.

## 지금 GPU에서 돌고 있을까?

```python
import mlx.core as mx
print(mx.default_device())
```

```text
Device(gpu, 0)
```

`gpu`라고 나오면 MLX가 **따로 설정하지 않아도 기본으로 GPU를 쓰고 있다**는 뜻이다.

## 정리

- MLX는 **Apple 실리콘 Mac에서 숫자 계산을 빠르게 해 주는 Python 도구**다.
- 머신러닝은 결국 큰 숫자 묶음의 계산이고, MLX는 그 계산을 Mac GPU에서 한다.
- Python **3.10 이상**이 필요하다. Python 3.9로 설치했더니 오류 없이 예전 버전이 깔렸다.
- `mx.array`로 숫자를 담고, `+`, `*`, `@`로 계산한다.
- 기본 계산 장치는 GPU다.

## 다음 편

다음 편에서는 오늘 잠깐 본 **배열**을 제대로 다룬다. 배열의 모양(`shape`)과 숫자 종류(`dtype`), 원하는 부분만 꺼내는 방법을 배운다.

→ [2. 배열: MLX에서 숫자를 담는 그릇]({{ '/ai/mlx/array/' | relative_url }})

## 참고

- [MLX 공식 문서](https://ml-explore.github.io/mlx/build/html/index.html)
- [MLX 설치 안내](https://ml-explore.github.io/mlx/build/html/install.html)
- [MLX 빠른 시작](https://ml-explore.github.io/mlx/build/html/usage/quick_start.html)
- [MLX GitHub](https://github.com/ml-explore/mlx)
