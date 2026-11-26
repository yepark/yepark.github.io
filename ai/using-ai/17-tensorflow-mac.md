---
title: "Mac에서 TensorFlow 실습"
description: "Apple 실리콘 Mac에 TensorFlow를 설치하고, 텐서 연산, GradientTape 학습 루프, Keras로 MNIST 손글씨 분류 모델을 학습·평가·저장하는 과정을 실행 결과와 함께 따라갑니다."
parent: AI
nav_order: 17
permalink: /ai/using-ai/tensorflow-mac/
last_modified_at: 2026-11-26
seo:
  type: BlogPosting
date: 2026-11-26
first_written: 2026-11-26
last_modified_date: 2026-11-26
tags: [AI, Machine-Learning, TensorFlow, Keras, Python, macOS]
---

# Mac에서 TensorFlow 실습
{: .no_toc }

{% include article-toc.md %}

[머신러닝 기초]({{ '/ai/using-ai/machine-learning/' | relative_url }})에서 학습은 "손실을 재고, 파라미터를 조금 바꾸고, 다시 재는" 반복이라고 했다. 이 글에서는 그 반복을 TensorFlow로 직접 실행한다. 순서는 다음과 같다.

1. Mac에 TensorFlow 설치
2. 텐서 다루기
3. `GradientTape`로 직선 하나 학습하기
4. Keras로 손글씨 숫자 분류 모델 만들기

**TensorFlow**는 Google이 만든 머신러닝 라이브러리다. 다차원 배열(텐서) 연산, 자동 미분, 모델 학습과 배포 도구를 제공한다. **Keras**는 TensorFlow에 포함된 고수준 API로, 층을 쌓아 모델을 정의하고 `fit` 한 줄로 학습한다.

아래 출력은 TensorFlow 2.21.0을 CPU로 실행한 결과다. 같은 코드를 Mac에서 실행하면 소수점 아래 숫자나 실행 시간이 조금 다를 수 있다.

## 설치

### 준비할 것

- Apple 실리콘(M1 이후) Mac. 최근 TensorFlow 버전의 macOS 패키지는 arm64 기준이다. Intel Mac에서는 최신 버전이 설치되지 않을 수 있으므로, 설치가 실패하면 [TensorFlow 설치 안내](https://www.tensorflow.org/install/pip)에서 지원 환경을 확인한다.
- Python 3. macOS에 기본으로 들어 있는 Python 대신 Homebrew나 python.org에서 설치한 Python을 쓰는 편이 관리하기 쉽다.

```bash
brew install python@3.12
python3.12 --version
```

### 가상 환경 만들고 설치하기

프로젝트마다 패키지 버전이 섞이지 않도록 가상 환경을 만든다.

```bash
mkdir tf-practice && cd tf-practice
python3.12 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install tensorflow
```

`pip install tensorflow`가 "No matching distribution" 오류로 끝나면 대부분 Python 버전이 TensorFlow가 지원하는 범위 밖이거나, Intel Mac이거나, 가상 환경이 아닌 다른 Python에 설치하려는 경우다. `which python`으로 `.venv` 안의 Python을 쓰고 있는지 먼저 확인한다.

### GPU(Metal) 가속은 선택

기본 설치는 CPU로 실행된다. 이 글의 예제는 CPU로도 몇십 초면 끝난다. Mac의 GPU를 쓰려면 Apple이 제공하는 `tensorflow-metal` 플러그인을 추가로 설치한다.

```bash
pip install tensorflow-metal
```

다만 이 플러그인은 TensorFlow의 특정 버전과만 맞는다. 설치 후 아래 확인 코드에서 `GPU`가 보이지 않거나 import 오류가 나면, [Apple의 tensorflow-metal 안내](https://developer.apple.com/metal/tensorflow-plugin/)에서 호환 버전을 확인한다. 처음 배울 때는 플러그인 없이 CPU로 시작하는 편이 문제가 적다.

## 텐서 다루기

설치가 됐는지 확인하면서 텐서를 만들어 보자. `t1.py`로 저장한다.

```python
import tensorflow as tf

print("TensorFlow", tf.__version__)
print("devices:", [d.device_type for d in tf.config.list_physical_devices()])

a = tf.constant([[1.0, 2.0], [3.0, 4.0]])
b = tf.constant([[1.0], [1.0]])
print("a.shape:", a.shape, "dtype:", a.dtype.name)
print("a @ b:", (a @ b).numpy().ravel())
print("a * 10:", (a * 10).numpy().tolist())
print("row mean:", tf.reduce_mean(a, axis=1).numpy())
```

```bash
python t1.py
```

```
TensorFlow 2.21.0
devices: ['CPU']
a.shape: (2, 2) dtype: float32
a @ b: [3. 7.]
a * 10: [[10.0, 20.0], [30.0, 40.0]]
row mean: [1.5 3.5]
```

- `devices`에 `GPU`가 있으면 Metal 플러그인이 동작하는 것이다. `CPU`만 있어도 예제를 실행하는 데 문제없다.
- 텐서는 **shape**(각 축의 길이)와 **dtype**(원소 타입)을 가진다. 머신러닝 코드의 오류는 대부분 shape가 맞지 않아서 생기므로, 막히면 `.shape`부터 출력해 본다.
- `@`는 행렬 곱, `*`는 원소별 곱이다. `axis=1`은 "열 방향으로 줄여서 행마다 하나씩" 남긴다.
- `.numpy()`는 텐서를 NumPy 배열로 바꾼다.

실행할 때 `oneDNN`이나 CPU 명령어 관련 안내 문구가 먼저 찍힐 수 있다. 오류가 아니라 정보 메시지다. 보기 싫으면 `TF_CPP_MIN_LOG_LEVEL=2 python t1.py`로 실행한다.

## GradientTape로 직선 학습하기

`y = 2x + 1`에 약간의 잡음을 섞은 데이터를 만들고, 모델 `w·x + b`가 `w=2`, `b=1`을 스스로 찾게 한다. `t2.py`로 저장한다.

```python
import tensorflow as tf

tf.random.set_seed(0)
x = tf.random.uniform((100, 1), -1.0, 1.0)
y = 2.0 * x + 1.0 + tf.random.normal((100, 1), stddev=0.05)

w = tf.Variable(0.0)
b = tf.Variable(0.0)
optimizer = tf.keras.optimizers.SGD(learning_rate=0.1)

for step in range(1, 201):
    with tf.GradientTape() as tape:
        pred = w * x + b
        loss = tf.reduce_mean((pred - y) ** 2)
    grads = tape.gradient(loss, [w, b])
    optimizer.apply_gradients(zip(grads, [w, b]))
    if step in (1, 50, 200):
        print(f"step {step:3d}  loss={loss.numpy():.4f}  w={w.numpy():.3f}  b={b.numpy():.3f}")
```

```
step   1  loss=2.3612  w=0.138  b=0.194
step  50  loss=0.0039  w=1.955  b=1.003
step 200  loss=0.0027  w=2.008  b=1.005
```

[머신러닝 기초]({{ '/ai/using-ai/machine-learning/' | relative_url }})의 네 가지가 코드에 그대로 있다.

| 구성 요소 | 코드 |
| --- | --- |
| 데이터 | `x`, `y` |
| 모델 | `w * x + b` (`tf.Variable`이 파라미터) |
| 손실 함수 | `reduce_mean((pred - y) ** 2)`, 평균제곱오차 |
| 최적화 | `tape.gradient`로 기울기를 구하고 `SGD`로 파라미터 갱신 |

`GradientTape`는 블록 안에서 일어난 연산을 기록했다가, `tape.gradient`를 호출하면 손실을 각 파라미터로 미분한 값을 돌려준다. 옵티마이저는 그 기울기의 반대 방향으로 파라미터를 `learning_rate`만큼 움직인다.

손실이 0까지 떨어지지 않고 0.0027 근처에서 멈춘 것은 데이터에 넣은 잡음(표준편차 0.05, 분산 0.0025) 때문이다. 잡음은 모델이 설명할 수 없는 부분이다.

`learning_rate`를 `1.5`로 바꿔 실행하면 50번째 스텝에서 손실이 10의 29제곱 수준으로 커지고, 200번째 스텝에서는 `nan`이 된다. 한 번에 너무 크게 움직여서 최솟값을 넘어가기 때문이다.

## Keras로 손글씨 숫자 분류하기

이제 실제 데이터로 분류 모델을 만든다. **MNIST**는 0~9 손글씨 숫자 이미지 7만 장(28×28 흑백)으로 이루어진 데이터셋이다. Keras가 처음 실행할 때 자동으로 내려받는다(약 11MB, `~/.keras/datasets`에 저장).

`t3.py`로 저장한다.

```python
import tensorflow as tf

tf.keras.utils.set_random_seed(42)

(x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
x_train = x_train.astype("float32") / 255.0
x_test = x_test.astype("float32") / 255.0
print("train:", x_train.shape, "test:", x_test.shape)

model = tf.keras.Sequential([
    tf.keras.Input(shape=(28, 28)),
    tf.keras.layers.Flatten(),
    tf.keras.layers.Dense(128, activation="relu"),
    tf.keras.layers.Dropout(0.2),
    tf.keras.layers.Dense(10),
])
model.compile(
    optimizer="adam",
    loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
    metrics=["accuracy"],
)
model.summary()

history = model.fit(
    x_train, y_train,
    epochs=5,
    batch_size=64,
    validation_split=0.1,
    callbacks=[tf.keras.callbacks.EarlyStopping(patience=2, restore_best_weights=True)],
    verbose=2,
)

loss, acc = model.evaluate(x_test, y_test, verbose=0)
print(f"test loss={loss:.4f} accuracy={acc:.4f}")

model.save("mnist.keras")
restored = tf.keras.models.load_model("mnist.keras")
logits = restored.predict(x_test[:3], verbose=0)
probs = tf.nn.softmax(logits).numpy()
print("pred:", probs.argmax(axis=1), "label:", y_test[:3], "conf:", probs.max(axis=1).round(3))
```

### 데이터 준비

```
train: (60000, 28, 28) test: (10000, 28, 28)
```

학습용 6만 장, 테스트용 1만 장이 이미 나뉘어 있다. 픽셀 값은 0~255 정수인데, 255로 나눠 0~1 사이 실수로 바꾼다. 입력 값의 범위가 크면 학습이 불안정해지기 쉽기 때문이다.

### 모델 구조

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Layer (type)                    ┃ Output Shape           ┃       Param # ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ flatten (Flatten)               │ (None, 784)            │             0 │
├─────────────────────────────────┼────────────────────────┼───────────────┤
│ dense (Dense)                   │ (None, 128)            │       100,480 │
├─────────────────────────────────┼────────────────────────┼───────────────┤
│ dropout (Dropout)               │ (None, 128)            │             0 │
├─────────────────────────────────┼────────────────────────┼───────────────┤
│ dense_1 (Dense)                 │ (None, 10)             │         1,290 │
└─────────────────────────────────┴────────────────────────┴───────────────┘
 Total params: 101,770 (397.54 KB)
```

| 층 | 하는 일 |
| --- | --- |
| `Flatten` | 28×28 이미지를 784개 숫자 한 줄로 편다 |
| `Dense(128, relu)` | 784개 입력을 128개 특징으로 바꾼다. 파라미터 784×128 + 128 = 100,480개 |
| `Dropout(0.2)` | 학습 중 무작위로 20%를 꺼서 특정 특징에 의존하지 않게 한다. 과적합을 줄이는 규제다 |
| `Dense(10)` | 숫자 0~9 각각의 점수(logit)를 낸다 |

`shape`의 `None`은 배치 크기다. 한 번에 몇 장을 넣든 받을 수 있다는 뜻이다.

`compile`에서 정하는 세 가지는 앞의 직선 예제와 같은 역할이다.

- `optimizer="adam"`: SGD를 발전시킨 옵티마이저. 대부분의 경우 기본값으로 쓰기 좋다.
- `SparseCategoricalCrossentropy(from_logits=True)`: 분류용 손실 함수. 정답이 `3` 같은 정수이고(Sparse), 마지막 층이 확률이 아닌 점수를 낸다(from_logits)는 뜻이다.
- `metrics=["accuracy"]`: 학습 중 확인할 지표. 손실과 별개로 사람이 읽기 쉬운 숫자를 보여 준다.

### 학습

```
Epoch 1/5
844/844 - 2s - 3ms/step - accuracy: 0.8951 - loss: 0.3599 - val_accuracy: 0.9610 - val_loss: 0.1435
Epoch 2/5
844/844 - 2s - 2ms/step - accuracy: 0.9475 - loss: 0.1789 - val_accuracy: 0.9672 - val_loss: 0.1037
Epoch 3/5
844/844 - 2s - 2ms/step - accuracy: 0.9610 - loss: 0.1323 - val_accuracy: 0.9730 - val_loss: 0.0889
Epoch 4/5
844/844 - 2s - 2ms/step - accuracy: 0.9669 - loss: 0.1073 - val_accuracy: 0.9738 - val_loss: 0.0826
Epoch 5/5
844/844 - 2s - 2ms/step - accuracy: 0.9726 - loss: 0.0903 - val_accuracy: 0.9770 - val_loss: 0.0783
```

- **epoch**: 학습 데이터 전체를 한 번 다 보는 단위다. 5 epoch이면 6만 장을 다섯 번 봤다.
- **844**: 한 epoch의 스텝 수. `validation_split=0.1`로 6만 장 중 10%(6천 장)를 검증용으로 떼어 냈으므로, 남은 54,000장을 64장씩 나누면 844번이다.
- `accuracy`/`loss`는 학습 데이터, `val_accuracy`/`val_loss`는 학습에 쓰지 않은 검증 데이터의 결과다.

검증 손실이 계속 줄고 있으므로 아직 과적합 신호는 없다. 학습 정확도가 검증 정확도보다 낮은 것은 `Dropout`이 학습 중에만 켜지기 때문이다.

`EarlyStopping(patience=2)`는 검증 손실이 2 epoch 연속 나아지지 않으면 학습을 멈추고, `restore_best_weights=True`로 가장 좋았던 시점의 파라미터로 되돌린다. `epochs`를 20으로 늘려 실행해 보면 어느 시점에서 멈추는지 볼 수 있다.

### 평가와 예측

```
test loss=0.0839 accuracy=0.9739
pred: [7 2 1] label: [7 2 1] conf: [0.998 0.998 0.997]
```

학습과 설정 선택에 전혀 쓰지 않은 테스트 데이터 1만 장에서 정확도 97.4%가 나왔다. 검증 정확도(97.7%)와 비슷하므로, 검증 데이터로 본 성능이 새 데이터에서도 유지된다고 볼 수 있다.

`model.save("mnist.keras")`는 모델 구조와 학습된 파라미터를 파일 하나로 저장한다. `load_model`로 불러온 모델로 테스트 이미지 3장을 예측하니 정답과 모두 같았다. 모델이 내는 점수를 `softmax`로 확률로 바꾸면, 가장 높은 확률이 모델의 확신 정도다.

## 더 해 볼 것

같은 파일을 조금씩 바꿔 가며 결과가 어떻게 달라지는지 보면 각 설정의 역할이 분명해진다.

| 바꿀 것 | 확인할 것 |
| --- | --- |
| `Dense(128)` → `Dense(16)` | 모델이 작아지면 정확도가 얼마나 떨어지는가 |
| `Dropout(0.2)` 제거, `epochs=20` | 학습 정확도와 검증 정확도의 차이가 벌어지는가 (과적합) |
| 255로 나누는 줄 제거 | 정규화하지 않으면 학습이 어떻게 달라지는가 |
| `tf.keras.datasets.fashion_mnist` | 옷 이미지에서도 같은 모델이 잘 되는가 |
| `Conv2D`, `MaxPooling2D` 층 추가 | 이미지 구조를 쓰는 합성곱 모델이 더 나은가 |

## 문제가 생길 때

| 증상 | 확인할 것 |
| --- | --- |
| `pip install tensorflow`가 패키지를 못 찾음 | Python 버전, Apple 실리콘 여부, 가상 환경 활성화 |
| `import tensorflow`에서 멈추거나 오류 | 다른 Python에 설치하지 않았는지 `which python`, `pip show tensorflow` |
| `tensorflow-metal` 설치 후 오류 | 플러그인과 TensorFlow 버전 호환. 플러그인을 지우고 CPU로 먼저 확인 |
| MNIST 다운로드 실패 | 네트워크·프록시. 받다 만 파일이 `~/.keras/datasets`에 남았으면 지우고 다시 실행 |
| shape 관련 오류 | 각 단계에서 `.shape`를 출력해 입력과 층이 기대하는 shape 비교 |

## 이어서 읽기

- [머신러닝 기초]({{ '/ai/using-ai/machine-learning/' | relative_url }})
- [MLX 자동 미분과 학습 루프]({{ '/ai/mlx/training-loop/' | relative_url }}): 같은 직선 학습을 Apple의 MLX로
- [MLX로 작은 신경망 만들기]({{ '/ai/mlx/neural-network/' | relative_url }})

## 참고

- [TensorFlow: pip로 설치](https://www.tensorflow.org/install/pip)
- [TensorFlow: 초보자를 위한 빠른 시작](https://www.tensorflow.org/tutorials/quickstart/beginner)
- [TensorFlow: GradientTape와 자동 미분](https://www.tensorflow.org/guide/autodiff)
- [Apple: tensorflow-metal](https://developer.apple.com/metal/tensorflow-plugin/)
- [Keras: Model training APIs](https://keras.io/api/models/model_training_apis/)
