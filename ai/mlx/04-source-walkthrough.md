---
title: "MLX 실행 엔진 소스 분석"
description: "MLX 실제 소스를 따라 Python 바인딩, C++ array, 지연 계산 그래프, eval과 Metal 백엔드의 역할을 설명합니다."
parent: MLX
grand_parent: iOS
nav_order: 4
permalink: /ai/mlx/source-walkthrough/
date: 2026-11-17
last_modified_at: 2026-11-17
seo:
  type: BlogPosting
last_modified_date: 2026-11-17
---

# MLX 실행 엔진 소스 분석
{: .no_toc }

{% include article-toc.md %}

MLX에서 배열을 더하는 코드는 짧다. 하지만 실제 계산은 Python 한 줄 안에서 모두 처리되지 않는다. Python과 C++을 잇는 계층, 배열의 모양을 검사하는 계층, 나중에 계산할 그래프를 만드는 계층, CPU나 GPU에서 실행하는 계층이 연결된다.

이 글은 [ml-explore/mlx](https://github.com/ml-explore/mlx)의 커밋 [`fc344c986c4169d99f76b5d95ae6b4a58a359a63`](https://github.com/ml-explore/mlx/tree/fc344c986c4169d99f76b5d95ae6b4a58a359a63)을 2026년 11월 17일에 읽은 기준으로 설명한다. 아래 경로는 해당 커밋에 고정했다.

설명용 의사 코드는 원문을 그대로 복사한 것이 아니라 동작을 이해하기 위해 단순화한 것이다.

## C++을 처음 읽는 독자를 위해

`namespace`는 이름 충돌을 줄이기 위한 범위이고, `mx::add`의 `::`는 그 범위 안의 함수를 가리킨다. `std::shared_ptr`는 여러 객체가 같은 대상의 수명을 함께 관리하는 참조다.

처음에는 템플릿과 매크로 전체를 이해하려고 멈추기보다 입력과 출력이 무엇인지 적어 보자. Python 배열이 C++ 배열로 바뀌고, 결과 노드가 만들어지고, backend가 실행하는 큰 흐름을 먼저 잡으면 세부 구현을 읽기 쉽다.

## 먼저 분석할 예제

```python
import mlx.core as mx

a = mx.array([1.0, 2.0, 3.0])
b = mx.array([10.0, 20.0, 30.0])
c = mx.add(a, b)
mx.eval(c)
print(c)
```

예상 값은 `[11.0, 22.0, 33.0]`이다. 관심을 둘 부분은 `mx.add`와 `mx.eval` 사이의 역할 차이다. `add`는 계산 관계를 만들고, `eval`은 그 결과가 필요하다고 요청한다. `print`처럼 값을 관찰하는 동작도 평가를 유발할 수 있으므로 지연 계산을 실험할 때는 관찰 코드의 영향을 생각해야 한다.

## 저장소를 어디부터 읽을까

| 위치 | 담당하는 일 | 먼저 찾을 단서 |
| --- | --- | --- |
| `python/src/` | Python과 C++ 연결 | `add`, `to_arrays` |
| `mlx/array.h` | 배열 메타데이터와 그래프 노드 | `ArrayDesc` |
| `mlx/ops.cpp` | 연산의 입력 검사와 그래프 생성 | `array add` |
| `mlx/primitives.h` | 기본 연산 객체의 선언 | `eval_cpu`, `eval_gpu` |
| `mlx/transforms.cpp` | 평가와 함수 변환 | `eval` |
| `mlx/backend/cpu/` | CPU 연산 구현 | `binary.cpp` |
| `mlx/backend/metal/` | Apple GPU 실행 구현 | `binary.cpp`, `kernels/` |
| `mlx/backend/cuda/` | CUDA 백엔드 구현 | `binary/` |
| `python/mlx/nn/` | 신경망의 Python 구성 요소 | 레이어와 모듈 |
| `tests/`, `python/tests/` | C++·Python 동작 검증 | 덧셈과 broadcasting 테스트 |

MLX는 Apple 실리콘에서 출발했지만 분석한 트리에는 CUDA 백엔드도 있다. 따라서 ‘MLX 전체가 Metal만 지원한다’고 단정하면 현재 구조를 잘못 이해하게 된다. 이 글의 실행 경로는 Apple 실리콘의 Metal을 중심으로 좁혀 읽는다.

## 1단계: Python 호출이 C++로 넘어간다

[`python/src/ops.cpp`의 add 등록부](https://github.com/ml-explore/mlx/blob/fc344c986c4169d99f76b5d95ae6b4a58a359a63/python/src/ops.cpp#L340)를 보면 Python의 `add` 이름에 C++ 함수를 연결한다. 이 연결을 바인딩이라고 한다.

입력은 Python 배열뿐 아니라 스칼라일 수도 있다. `to_arrays`는 이 입력을 C++ 연산이 받을 배열 표현으로 맞춘다. 이후 `mx::add`에 전달한다.

```text
Python의 mx.add(a, b)
  → 입력을 C++ 배열 표현으로 정리
  → C++의 mx::add 호출
```

소스의 `nb`는 nanobind 라이브러리의 별칭이다. Python 이름과 인자, 문서, C++ 구현을 연결하는 부분이지 GPU 커널 자체는 아니다.

## 2단계: 덧셈 전에 자료형과 모양을 맞춘다

[`mlx/ops.cpp`의 add](https://github.com/ml-explore/mlx/blob/fc344c986c4169d99f76b5d95ae6b4a58a359a63/mlx/ops.cpp#L3266)는 개념적으로 다음 순서다.

```text
출력 자료형 결정
  → 입력 자료형 변환
  → broadcasting으로 모양 정렬
  → Add 연산을 가리키는 결과 배열 생성
```

`dtype`은 원소의 자료형이다. 정수와 실수를 더할 때 어떤 자료형으로 계산할지 먼저 정해야 한다. `promote_types`가 그 선택에 관여하고 `astype`이 필요한 변환을 표현한다.

`shape`는 배열의 각 축 길이다. 길이가 3인 벡터와 숫자 하나를 더하면 숫자가 세 자리에 적용되는 것처럼 보인다. 이것이 broadcasting이다. 항상 입력을 물리적으로 복사한다는 뜻은 아니다. 실제 접근 방식은 배열의 stride와 커널이 함께 처리한다.

```python
x = mx.array([1, 2, 3])
y = x + 10
# 개념적인 결과: [11, 12, 13]
```

## 3단계: 결과 배열은 그래프 노드가 된다

[`mlx/array.h`의 ArrayDesc](https://github.com/ml-explore/mlx/blob/fc344c986c4169d99f76b5d95ae6b4a58a359a63/mlx/array.h#L460)에는 모양, stride, 원소 수, 자료형, primitive, 상태, 동기화용 event 같은 정보가 있다.

배열 객체는 숫자 버퍼만 뜻하지 않는다. 아직 계산되지 않은 결과라면 ‘무슨 연산으로 어떤 입력에서 값을 만들 것인가’도 표현한다.

```text
a ─┐
   Add ─→ c
b ─┘
```

- `a`, `b`: 입력 노드
- `Add`: 계산할 연산을 나타내는 primitive
- `c`: 결과를 나타내는 배열 노드

primitive는 ‘이 값은 덧셈으로 만든다’는 실행 규칙이다. 결과 배열을 만드는 시점에 모든 숫자가 계산돼 있어야 하는 것은 아니다.

### stride를 알아야 하는 이유

stride는 다음 원소나 축으로 이동할 때 메모리에서 얼마나 건너뛸지 나타낸다. 전치나 일부 슬라이스는 데이터 전체를 다시 복사하는 대신 모양과 stride를 바꿔 표현할 수 있다. 그래서 backend는 shape뿐 아니라 데이터 배치도 살펴야 한다.

## 4단계: eval이 계산을 요청한다

[`mlx/transforms.cpp`의 eval](https://github.com/ml-explore/mlx/blob/fc344c986c4169d99f76b5d95ae6b4a58a359a63/mlx/transforms.cpp#L426)을 읽으면 이미 계산이 예약됐는지 확인하고, 필요한 경우 결과 완료를 기다리는 경로가 보인다.

지연 계산 상태에서는 출력에서 입력으로 의존 관계를 추적해야 한다. `d = (a + b) * 2`라면 곱셈 결과가 덧셈 결과에 의존한다. 실행은 이 관계를 지켜야 한다. GPU 작업은 제출과 완료 시점이 다를 수 있어 동기화도 필요하다.

`eval`을 호출할 때마다 새 스레드가 생긴다거나, 모든 연산을 하나의 거대한 GPU 커널로 합친다고 해석하면 안 된다. 실제 실행은 그래프·스트림·백엔드와 최적화 설정에 따라 달라진다.

## 5단계: Metal 백엔드에서 덧셈을 실행한다

[`mlx/backend/metal/binary.cpp`](https://github.com/ml-explore/mlx/blob/fc344c986c4169d99f76b5d95ae6b4a58a359a63/mlx/backend/metal/binary.cpp#L8)에는 이항 연산의 GPU 평가 함수를 만드는 매크로가 있고, 같은 파일의 `BINARY_GPU(Add)`가 덧셈을 연결한다.

이항 연산은 입력 두 개를 받는 연산이라는 뜻이다. 덧셈과 곱셈, 비교 연산은 서로 계산식이 달라도 입력 배치 검사와 커널 실행 준비를 공유할 수 있다.

```text
Add의 GPU 평가
  → 공통 binary GPU 실행 경로
  → 입력 형태에 맞는 커널 준비
  → GPU 작업 제출
  → 완료 후 결과 사용
```

초보자가 소스를 읽을 때 막히는 이유 중 하나가 매크로다. `Add::eval_gpu`라는 완성된 함수 이름만 검색하면 생성 지점을 놓칠 수 있다. `BINARY_GPU` 정의와 `BINARY_GPU(Add)` 호출을 함께 읽어야 한다.

CPU 경로는 [`mlx/backend/cpu/binary.cpp`](https://github.com/ml-explore/mlx/blob/fc344c986c4169d99f76b5d95ae6b4a58a359a63/mlx/backend/cpu/binary.cpp)에서 출발해 비교할 수 있다. 같은 논리 연산에 다른 실행 구현을 연결하는 구조다.

## 통합 메모리여도 동기화는 필요하다

CPU와 GPU가 같은 메모리 체계의 배열을 사용할 수 있다는 것은 명시적인 장치 간 복사를 줄이는 장점이다. 하지만 GPU가 쓰는 중인 결과를 CPU가 먼저 읽어도 된다는 뜻은 아니다. 작업 제출 순서, 완료 event, 결과를 기다리는 경계가 필요하다.

이 차이를 알면 ‘공유 메모리인데 왜 기다리지?’라는 의문이 풀린다. 데이터를 놓는 장소와 계산이 끝났는지는 서로 다른 문제다.

## 소스를 직접 따라 읽는 순서

```bash
git clone https://github.com/ml-explore/mlx.git
cd mlx
git show fc344c986c4169d99f76b5d95ae6b4a58a359a63:mlx/ops.cpp
rg -n 'to_arrays|"add"' python/src/ops.cpp
rg -n 'array add|make_shared<Add>' mlx/ops.cpp
rg -n 'ArrayDesc|Status|Event' mlx/array.h
rg -n 'BINARY_GPU' mlx/backend/metal/binary.cpp
```

`git show 커밋:경로`는 해당 버전의 파일을 출력한다. 로컬 main이 바뀌었다면 `rg` 결과는 달라질 수 있으므로 글의 링크와 비교할 때 커밋을 맞춘다. 처음부터 전체를 빌드하지 않고 하나의 연산 경로부터 읽어도 충분하다.

## 배열 상태와 비동기 완료의 경계

`array.h`의 상태 정의와 `transforms.cpp`의 `eval`·`async_eval`을 나란히 읽으면 ‘평가됨’과 ‘사용 가능함’이 분리돼 있음을 확인할 수 있다. GPU 명령을 준비하고 제출했더라도 실제 장치 계산은 진행 중일 수 있다.

| 관찰할 위치 | 소스에서 확인하는 책임 | 애플리케이션 관점 |
| --- | --- | --- |
| `array::Status` | 미예약·평가·사용 가능 상태 | 변수 존재와 계산 완료는 다름 |
| `async_eval` | 필요한 작업의 평가를 예약 | 호출 복귀가 결과 완료를 뜻하지 않음 |
| `eval` | 작업 평가 후 완료 대기 | 동기식 결과 관찰 경계 |
| `Event`와 `wait` | 실행 의존성과 완료 확인 | 스트림 사이에도 순서가 필요함 |

분석한 `eval`은 출력에 미예약 작업이 없는 경우에도 각 출력의 `wait`를 호출하는 경로가 있다. 따라서 이미 예약됐다는 이유로 완료를 무조건 가정하지 않는다. 이 차이는 GPU 작업 제출 시간만 측정하는 벤치마크 오류와 직접 연결된다.

## Metal 이항 연산의 커널 선택

`binary.cpp`의 `get_kernel_name`은 입력 형태에 따라 scalar–scalar, scalar–vector, vector–scalar, 일반 배치 등의 구분을 사용한다. 일반 경로에서는 shape와 stride를 함께 전달하고, 연속 차원을 합치는 처리도 보인다.

예를 들어 길이 N의 배열과 스칼라를 더할 때는 두 개의 N원소 배열을 읽는 경우와 접근 패턴이 다르다. 일반적인 다차원 stride 처리가 필요 없는 입력에는 더 단순한 경로를 사용할 여지가 있다. 소스의 분기 조건을 확인해야 실제 선택된 경로를 알 수 있다.

한편 shape가 같다고 모든 입력이 같은 커널을 사용하는 것은 아니다. 자료형, 연속성, 큰 인덱스가 필요한지, 한 스레드에서 처리할 원소 수 같은 조건이 커널 이름과 디스패치 구성에 관여한다.

## 호스트 코드와 장치 코드 연결

Metal 백엔드 C++ 코드는 입력 버퍼를 연결하고 compute pipeline을 선택해 작업을 디스패치한다. 실제 GPU 원소 연산은 [`kernels/binary.h`](https://github.com/ml-explore/mlx/blob/fc344c986c4169d99f76b5d95ae6b4a58a359a63/mlx/backend/metal/kernels/binary.h)와 [`binary_ops.h`](https://github.com/ml-explore/mlx/blob/fc344c986c4169d99f76b5d95ae6b4a58a359a63/mlx/backend/metal/kernels/binary_ops.h)를 함께 따라간다.

일반 stride 커널은 스레드 인덱스를 각 입력의 데이터 위치로 변환하고, 선택한 `Op`를 적용해 출력에 기록한다. `Add`의 연산 자체는 두 값을 더하는 짧은 함수지만, 실제 프레임워크의 복잡성은 그 주변의 메모리 접근과 실행 관리에 있다.

이 연결을 다음 세 질문으로 나눠 읽으면 된다.

1. 호스트에서 어떤 입력 형태를 분류했는가?
2. 선택한 커널에 어떤 shape·stride·버퍼를 전달했는가?
3. 장치 코드가 그 정보를 사용해 어떤 위치를 읽고 쓰는가?

단순히 `x + y`를 찾은 것만으로 GPU 구현을 분석했다고 보기 어렵다. 입력 주소 계산과 실행 범위를 함께 확인해야 한다.

## 전치한 배열의 덧셈을 주소 계산까지 따라가기

일반 stride 경로가 왜 필요한지 작은 배열로 확인해 보자.

```python
x = mx.arange(6).reshape(2, 3)
transposed = x.T
y = mx.full((3, 2), 10)
z = transposed + y
print(z.tolist())
```

```text
[[10, 13], [11, 14], [12, 15]]
```

논리적 shape는 두 입력 모두 `(3, 2)`다. 그러나 원본 x가 행 우선으로 연속하고 전치가 그 버퍼를 보는 뷰로 표현된 경우, 전치 입력의 원소 단위 stride는 `(1, 3)`으로 생각할 수 있다. 연속한 y의 stride `(2, 1)`과 다르다. 이 조건에서 좌표 `(행, 열)`의 원소 위치는 `행 × 첫 stride + 열 × 둘째 stride`로 계산한다.

| 출력의 선형 번호 | 논리 좌표 | 전치 입력의 위치 | y의 위치 | 더한 값 |
| ---: | --- | ---: | ---: | ---: |
| 0 | `(0, 0)` | 0 | 0 | `0 + 10 = 10` |
| 1 | `(0, 1)` | 3 | 1 | `3 + 10 = 13` |
| 2 | `(1, 0)` | 1 | 2 | `1 + 10 = 11` |
| 3 | `(1, 1)` | 4 | 3 | `4 + 10 = 14` |
| 4 | `(2, 0)` | 2 | 4 | `2 + 10 = 12` |
| 5 | `(2, 1)` | 5 | 5 | `5 + 10 = 15` |

출력의 3번 원소를 계산하는 작업이 두 입력 모두에서 물리적 3번 원소를 읽으면 결과가 틀린다. 전치 입력에서는 4번 위치의 값을 읽어야 한다. GPU 스레드의 번호를 입력 버퍼 주소에 그대로 대입할 수 없는 이유다.

이 표는 주소 변환을 이해하기 위한 계산 모델이다. 특정 실행에서 뷰가 그대로 전달됐는지, 연속화가 먼저 일어났는지, 몇 개의 원소를 한 스레드가 처리했는지까지 측정한 결과는 아니다. 그 부분은 앞서 살펴본 호스트의 커널 선택과 실제 실행 관찰로 확인해야 한다.

소스를 다시 읽을 때는 입력마다 별도의 위치를 계산하는 부분을 찾자. 같은 논리 좌표를 서로 다른 stride로 해석한 뒤 값을 읽고, `Op`를 적용해 출력에 쓰는 흐름이 이 표와 연결된다. 덧셈 공식 자체보다 주소 대응을 먼저 이해하면 전치·슬라이스·broadcasting의 구현도 이어서 읽을 수 있다.

## 검증 가능한 주장과 추가 관찰이 필요한 주장

소스에서 ‘그런 최적화 경로가 존재한다’는 것은 확인할 수 있다. 그러나 내 입력에서 실제 그 경로가 선택됐는지, 시간이 어느 단계에 쓰였는지까지 자동으로 증명되지는 않는다.

| 주장 | 필요한 근거 |
| --- | --- |
| `add`가 결과 노드를 구성함 | `ops.cpp`의 반환 경로 |
| Metal 경로에 stride 처리 분기가 존재함 | `binary.cpp`와 커널 구현 |
| 특정 입력이 특정 커널을 실행함 | 로깅·디버거·프로파일러 관찰 |
| 특정 최적화로 속도가 향상됨 | 같은 조건의 전후 비교와 정확성 검증 |

실행 검증은 패키지 0.32.4로 수행했고, 이 글의 소스 링크는 명시한 개발 커밋에 고정했다. 두 버전이 동일한 빌드라는 주장은 하지 않는다. 정확한 실행 경로 연구에서는 사용한 바이너리와 소스 버전을 맞춰 빌드해야 한다.

## 연구를 확장하는 방법

`add` 경로를 이해한 뒤 `matmul`을 따라가면 큰 행렬 계산이 다른 커널 선택과 최적화를 필요로 한다는 점을 볼 수 있다. 그다음 `grad`가 primitive의 미분 규칙을 어떻게 활용하는지 읽으면 학습 코드와 저수준 연산의 연결이 보인다.

이 글은 소스 읽기와 실행 경로 분석을 수행했다. 개발 커밋을 직접 빌드하거나 특정 GPU 커널을 프로파일링하지는 않았다. 릴리스 패키지에서 실행한 연산과 벤치마크는 [MLX 지연 평가와 성능 측정]({{ '/ai/mlx/lazy-evaluation/' | relative_url }})에 환경과 측정 경계를 기록했다.

## 참고 소스

- [분석한 커밋 전체 트리](https://github.com/ml-explore/mlx/tree/fc344c986c4169d99f76b5d95ae6b4a58a359a63)
- [Python 연산 바인딩](https://github.com/ml-explore/mlx/blob/fc344c986c4169d99f76b5d95ae6b4a58a359a63/python/src/ops.cpp)
- [C++ 배열 구조](https://github.com/ml-explore/mlx/blob/fc344c986c4169d99f76b5d95ae6b4a58a359a63/mlx/array.h)
- [C++ 연산 구성](https://github.com/ml-explore/mlx/blob/fc344c986c4169d99f76b5d95ae6b4a58a359a63/mlx/ops.cpp)
- [Metal 이항 연산](https://github.com/ml-explore/mlx/blob/fc344c986c4169d99f76b5d95ae6b4a58a359a63/mlx/backend/metal/binary.cpp)
