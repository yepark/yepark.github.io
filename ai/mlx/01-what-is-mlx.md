---
title: "MLX 개요와 실행 환경"
description: "MLX의 계층 구조, 지연 실행, 통합 메모리, 함수 변환과 Apple 실리콘 환경의 재현 가능한 설치·검증 절차를 설명합니다."
parent: MLX
grand_parent: iOS
nav_order: 1
permalink: /ai/mlx/what-is-mlx/
last_modified_at: 2026-11-20
seo:
  type: BlogPosting
date: 2026-11-15
redirect_from:
  - /mlx/what-is-mlx/
first_written: 2026-11-15
last_modified_date: 2026-11-20
tags: [MLX, Python, Apple-Silicon]
---

# MLX 개요와 실행 환경
{: .no_toc }

{% include article-toc.md %}

숫자 다섯 개에서 규칙을 배우는 모델을 만든다고 하자. 예측값을 계산하는 것만으로는 학습이 되지 않는다. 정답과의 오차를 구하고, 바꿀 파라미터의 기울기를 계산하고, 새 값으로 갱신하는 연산이 필요하다. MLX는 이 계산에 쓰이는 다차원 배열 연산과 함수 변환을 제공하는 머신러닝 프레임워크다. NumPy와 유사한 Python 배열 API를 출발점으로, 자동 미분과 모델 구성·최적화 기능을 연결한다. Apple 실리콘에서는 CPU와 Metal GPU를 함께 활용할 수 있다.

아래에서는 같은 배열에 원소별 곱셈과 행렬곱을 적용하고, 그 차이를 손으로 계산한다. 이어서 자동 미분과 CPU·GPU 실행으로 확장한다. 설명과 명령은 Apple 실리콘 Mac의 Python 환경을 기준으로 한다. iPhone 앱에 Python 패키지를 배포하는 절차는 아니다.

## MLX가 담당하는 계층

머신러닝 앱을 다음처럼 나누면 MLX의 위치가 분명해진다.

| 계층 | 책임 | 예 |
| --- | --- | --- |
| 제품 기능 | 사용자가 수행할 작업 | 문서 요약, 이미지 분류 |
| 모델·학습 코드 | 파라미터와 계산 규칙 | 신경망 레이어, 손실 함수 |
| 배열·변환 | 계산을 표현하고 미분 | `mlx.core`, `mx.grad` |
| 실행 백엔드 | 계산을 장치에서 실행 | CPU, Metal |
| 하드웨어 | 연산과 데이터 접근 | CPU 코어, GPU, 메모리 |

MLX를 설치했다고 특정 언어 모델의 가중치나 토크나이저까지 자동으로 준비되는 것은 아니다. 배열 프레임워크, 모델 코드, 모델 데이터는 구분해야 한다.

Apple의 Foundation Models는 시스템이 제공하는 모델을 앱에서 호출하는 API다. MLX는 연산과 모델 구성을 직접 다루는 쪽에 가깝다. 목적이 시스템 모델 활용인지, 모델 실행 구조 제어인지에 따라 선택이 달라진다.

## 실행 모델을 이해하는 세 가지 관점

### 배열은 값과 계산 관계를 표현한다

`mx.array`는 모양(shape)과 원소 자료형(dtype)을 가진다. 계산이 끝나기 전에는 어떤 입력에 어떤 연산을 적용할지도 함께 표현할 수 있다. 따라서 배열 변수의 생성과 숫자 데이터의 계산 완료는 같은 사건이 아니다.

### 지연 평가는 계산 시점을 분리한다

`c = a + b`는 결과를 만드는 연산 관계를 구성한다. `mx.eval(c)`나 Python 값으로의 변환처럼 실제 값이 필요한 지점에서 평가가 일어난다. 이 구분을 놓치면 연산 준비 시간만 측정하고 GPU가 매우 빠르다는 잘못된 결론을 낼 수 있다.

### 통합 메모리는 복사와 동기화를 다르게 만든다

Apple 실리콘의 공유 메모리 구조는 CPU와 GPU 사이의 명시적인 데이터 이동을 줄이는 데 도움이 된다. 하지만 메모리 대역폭, 캐시, 데이터 배치와 작업 완료를 기다리는 비용은 남는다. ‘통합 메모리이므로 데이터 이동 비용이 전부 0’이라는 설명은 적절하지 않다.

## 설치 환경과 버전 고정

본문 실험을 실행한 환경은 다음과 같다.

| 항목 | 검증 환경 |
| --- | --- |
| 하드웨어 | Apple M4 |
| 운영체제 | macOS 15.6, arm64 |
| Python | 3.12.16 |
| MLX 패키지 | 0.32.4 |
| 기본 장치 | `Device(gpu, 0)` |

이 조합은 재현 기준이며 모든 환경의 최소 요구사항을 뜻하지 않는다. 설치 전 [공식 설치 문서](https://ml-explore.github.io/mlx/build/html/install.html)의 버전별 조건을 확인한다. 저장소에는 CUDA와 Linux CPU 경로도 있지만, 이 글의 명령과 실험 결과는 Apple 실리콘 Mac에 한정한다.

가상 환경은 프로젝트마다 Python 패키지 집합을 분리하는 디렉터리다. 아래에서는 이미 `uv`가 설치돼 있다고 가정한다.

```bash
mkdir mlx-study
cd mlx-study
uv venv --python 3.12
source .venv/bin/activate
uv pip install "mlx==0.32.4"
```

활성화한 가상 환경에 버전을 고정해 설치하면 다른 프로젝트와 패키지를 구분하고 같은 API로 예제를 다시 실행할 수 있다. `uv` 자체는 [공식 설치 안내](https://docs.astral.sh/uv/getting-started/installation/)를 따른다.

## 환경을 코드로 기록하기

```python
import platform
from importlib.metadata import version
import mlx.core as mx

print(platform.machine())
print(platform.mac_ver()[0])
print(platform.python_version())
print(version("mlx"))
print(mx.default_device())
```

같은 코드도 dtype, 백엔드, 패키지 버전에 따라 성능이나 지원 범위가 달라진다. 결과만 공유하지 말고 이 환경 정보도 함께 기록한다. Rosetta로 실행하는 Python과 네이티브 arm64 Python을 혼동하지 않는 것도 중요하다.

## 첫 연산: 원소별 계산과 행렬곱

```python
import mlx.core as mx

x = mx.array([[1.0, 2.0], [3.0, 4.0]], dtype=mx.float32)

elementwise = x * x
matrix_product = x @ x

mx.eval(elementwise, matrix_product)
print(elementwise.tolist())
print(matrix_product.tolist())
```

결과는 다음과 같다.

```text
[[1.0, 4.0], [9.0, 16.0]]
[[7.0, 10.0], [15.0, 22.0]]
```

`*`는 대응하는 위치의 원소를 곱한다. `@`는 행렬곱이다. 행렬곱 결과의 첫 원소 7은 첫 행과 첫 열의 내적 `1×1 + 2×3`으로 계산한다. 두 연산은 출력 shape가 같아도 의미가 다르다.

`tolist()`는 MLX 배열을 일반 Python 리스트로 변환한다. 이 단계에는 결과를 실제로 사용할 수 있어야 하므로 평가와 완료 대기가 개입할 수 있다.

## 자동 미분으로 연결하기

자동 미분은 계산 그래프에 정의된 연산의 미분 규칙을 조합해 도함수를 구하는 기능이다. [공식 함수 변환 문서](https://ml-explore.github.io/mlx/build/html/usage/function_transforms.html)는 함수를 미분 가능한 다른 함수로 바꾸는 API를 설명한다. 단순히 입력을 조금 바꿔 차분을 계산하는 수치 미분과는 다르다.

```python
def loss(w):
    return mx.sum(w * w)

w = mx.array([1.0, -2.0, 3.0])
gradient = mx.grad(loss)(w)
print(gradient.tolist())
```

손실이 각 원소 제곱의 합이면 원소별 도함수는 `2w`다. 출력은 `[2.0, -4.0, 6.0]`이며, 재현 스크립트에서도 이 값을 검증한다. 실제 학습에서는 손실 정의, 파라미터 선택, 업데이트와 평가 경계가 추가된다.

이 기울기로 무엇을 바꾸는지까지 이어 보려면 [MLX 자동 미분과 학습 루프]({{ '/ai/mlx/training-loop/' | relative_url }})를 읽자. `y = 2x + 1`의 계수를 0에서 출발해 찾으며 첫 손실 9와 첫 기울기 `[-8, -2]`를 직접 계산한다. 모델의 예측 함수, 학습 데이터와 수정할 파라미터를 분리해 설명한다.

## CPU와 GPU 결과 비교

```python
cpu_result = mx.matmul(x, x, stream=mx.cpu)
gpu_result = mx.matmul(x, x, stream=mx.gpu)
mx.eval(cpu_result, gpu_result)

assert mx.allclose(cpu_result, gpu_result, rtol=1e-5, atol=1e-6).item()
```

`stream` 인자는 해당 연산의 실행 문맥을 선택한다. 모든 배열을 특정 장치 전용 객체로 영구 변경한다는 뜻이 아니다.

부동소수점 연산은 계산 순서에 따라 작은 차이가 날 수 있어 허용 오차로 비교한다. 위의 작은 정수값 예제는 정확히 같은 결과지만, 큰 행렬과 낮은 정밀도에서는 오차 기준을 데이터의 스케일에 맞춰 결정해야 한다.

## 재현과 해석의 범위

[재현 스크립트]({{ '/assets/examples/mlx/reproduce.py' | relative_url }})는 배열 연산, 자동 미분, CPU/GPU 결과 비교, 메모리 관찰, 행렬곱 측정을 한 번에 실행한다.

```bash
python reproduce.py
```

이 스크립트의 검증 성공은 다룬 연산과 입력에 대한 결과다. 모든 모델의 학습 안정성이나 모든 GPU 작업의 성능을 보장하지 않는다. 실제 제품에서는 데이터 전처리와 결과 후처리까지 포함한 지연, 메모리 피크, 오류 처리도 측정해야 한다.

## 참고와 후속 글

- [MLX 배열과 수치 연산]({{ '/ai/mlx/array/' | relative_url }})
- [MLX 지연 평가와 성능 측정]({{ '/ai/mlx/lazy-evaluation/' | relative_url }})
- [MLX 공식 저장소](https://github.com/ml-explore/mlx)
- [MLX 설치 문서](https://ml-explore.github.io/mlx/build/html/install.html)
