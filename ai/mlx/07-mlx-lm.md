---
title: "mlx-lm으로 언어 모델 실행하기"
description: "mlx-lm의 Llama 모델 코드로 작은 언어 모델을 직접 만들어 다음 토큰 예측, 생성 반복, KV 캐시, 샘플러, 저장·불러오기와 4비트 양자화를 실행 결과로 설명합니다."
parent: MLX
grand_parent: iOS
nav_order: 7
permalink: /ai/mlx/mlx-lm/
date: 2026-11-21
first_written: 2026-11-21
last_modified_at: 2026-11-27
last_modified_date: 2026-11-27
seo:
  type: BlogPosting
tags: [MLX, Python, LLM, mlx-lm]
---

# mlx-lm으로 언어 모델 실행하기
{: .no_toc }

{% include article-toc.md %}

언어 모델에 숫자 세 개 `[5, 17, 42]`를 넣으면 무엇이 나올까. 문장이 통째로 나오지 않는다. "다음에 올 번호마다 매긴 점수" 100개가 나온다. 그중 점수가 가장 큰 번호를 골라 뒤에 붙이고, 다시 넣는다. 이것을 반복하면 글이 길어진다.

```text
[5, 17, 42]            → 점수 100개 → 94 선택
[5, 17, 42, 94]        → 점수 100개 → 94 선택
[5, 17, 42, 94, 94]    → ...
```

이 번호를 **토큰**이라고 부른다. 토큰은 모델이 다루는 글자 조각에 붙인 번호다. 사전의 쪽 번호처럼, 모델은 글자 대신 번호를 주고받는다. 글자를 번호로 바꾸고 되돌리는 일은 **토크나이저**가 맡는다.

[앞 글]({{ '/ai/mlx/neural-network/' | relative_url }})에서는 파라미터 33개짜리 신경망을 `nn.Module`로 만들었다. 이번 글에서는 `mlx-lm` 패키지가 제공하는 Llama 모델 코드로 작은 언어 모델을 직접 만들고, 위의 반복이 코드에서 어떻게 일어나는지 따라간다.

**mlx-lm**은 MLX로 언어 모델을 실행하고 미세 조정하기 위한 Python 패키지다. Hugging Face에 공개된 모델을 불러와 텍스트를 생성하고, 양자화(가중치를 4비트처럼 적은 비트로 줄여 메모리를 아끼는 것)와 LoRA 미세 조정(원래 가중치는 그대로 두고 작은 보조 행렬만 학습하는 방법) 같은 기능을 명령어와 Python API로 제공한다. 이 글은 그중 모델 코드 부분을 직접 사용한다.

{: .tip }
쉽게 말하면, 언어 모델은 "다음 한 칸 맞히기"를 아주 많이 반복하는 기계다.

## 실행 환경

이 글의 출력은 **Linux x86_64 클라우드 머신의 CPU**에서 직접 실행한 결과다. Mac에서 실행한 결과가 아니다.

| 항목 | 값 |
| --- | --- |
| 운영체제 | Linux, x86_64 |
| Python | 3.13.18 |
| MLX | 0.32.4 (`pip install 'mlx[cpu]'`) |
| mlx-lm | 0.32.2 (`pip install mlx-lm`) |
| 기본 장치 | `Device(cpu, 0)` |

`mlx-lm`의 README는 이 패키지를 "Apple 실리콘에서 MLX로 대형 언어 모델의 텍스트를 생성하고 미세 조정하는 Python 패키지"라고 소개한다. 이 머신에서는 Linux CPU용 MLX 위에서도 설치와 아래 코드 실행이 됐다.

{: .warning }
이 머신은 Hugging Face Hub에 접속할 수 없어서 이미 학습된 실제 모델을 내려받지 못했다. 그래서 본문 예제는 **학습하지 않은 무작위 가중치** 모델로 실행했다. 나오는 토큰 번호에는 의미가 없다. 실제 모델 실행 명령은 마지막 절에 공식 README 내용 그대로 옮기고, 출력은 싣지 않았다.

## 설정 딕셔너리로 모델 만들기

`mlx-lm`의 `load` 함수는 모델 폴더의 `config.json`을 읽는다. 그 안의 `model_type` 값으로 `mlx_lm.models` 아래의 같은 이름 모듈을 고른다. 이 머신에 설치된 소스(`mlx_lm/utils.py`의 `_get_classes`)가 그렇게 동작한다. `"llama"`라면 `mlx_lm.models.llama`의 `Model`과 `ModelArgs`를 쓴다.

같은 일을 손으로 해 보자. 아주 작은 설정을 준다.

```python
import mlx.core as mx
from mlx.utils import tree_flatten
from mlx_lm.models import llama

cfg = {
    "model_type": "llama",
    "hidden_size": 64,
    "num_hidden_layers": 2,
    "intermediate_size": 128,
    "num_attention_heads": 4,
    "rms_norm_eps": 1e-5,
    "vocab_size": 100,
    "tie_word_embeddings": False,
}
mx.random.seed(0)
args = llama.ModelArgs.from_dict(cfg)
model = llama.Model(args)
mx.eval(model.parameters())

print(model.model.layers[0].mlp)
n = sum(v.size for _, v in
        tree_flatten(model.parameters()))
print("params", n)
```

```text
MLP(
  (gate_proj): Linear(input_dims=64, output_dims=128, bias=False)
  (down_proj): Linear(input_dims=128, output_dims=64, bias=False)
  (up_proj): Linear(input_dims=64, output_dims=128, bias=False)
)
params 95040
```

설정의 뜻은 다음과 같다.

| 키 | 뜻 |
| --- | --- |
| `vocab_size` | 토큰 번호의 개수. 여기서는 0~99 |
| `hidden_size` | 토큰 하나를 나타내는 숫자 개수 |
| `num_hidden_layers` | 같은 모양의 블록을 몇 번 쌓는지 |
| `intermediate_size` | 블록 안 MLP의 중간 크기 |
| `num_attention_heads` | 앞 토큰을 참고하는 갈래 수 |

출력을 보면 낯익은 부품이 나온다. 앞 글의 `nn.Linear`다. 큰 언어 모델도 `Module` 안에 `Linear`가 겹겹이 든 트리다.

파라미터 95,040개를 직접 세어 보자.

| 부분 | 계산 | 개수 |
| --- | --- | ---: |
| 토큰 → 숫자 표 (`embed_tokens`) | 100 × 64 | 6,400 |
| 블록 1개의 어텐션 Linear 4개 | 4 × 64 × 64 | 16,384 |
| 블록 1개의 MLP Linear 3개 | 3 × 64 × 128 | 24,576 |
| 블록 1개의 RMSNorm 2개 | 2 × 64 | 128 |
| 블록 2개 합 | 2 × 41,088 | 82,176 |
| 마지막 RMSNorm | 64 | 64 |
| 숫자 → 점수 (`lm_head`) | 64 × 100 | 6,400 |
| 합계 | | 95,040 |

{: .note }
`tie_word_embeddings`의 기본값은 `True`다. 그러면 소스의 `Model.__call__`은 `lm_head`를 따로 만들지 않고 `embed_tokens` 표를 출력에도 다시 쓴다. 이 글은 출력 층을 따로 보려고 `False`로 두었다.

## 한 번 부르면 다음 토큰 점수가 나온다

```python
ids = mx.array([[5, 17, 42]])
logits = model(ids)
print(logits.shape)
last = logits[0, -1]
print(mx.argmax(last).item())
```

```text
(1, 3, 100)
94
```

입력 shape는 `(1, 3)`이다. 문장 1개, 토큰 3개라는 뜻이다. 출력 shape `(1, 3, 100)`은 문장 1개, 위치 3개, 위치마다 점수 100개다.

이 점수를 **로짓(logits)**이라고 부른다. 아직 확률로 바꾸기 전의 날점수다. 위치마다 "이 위치 다음에 올 토큰"의 점수가 들어 있다. 지금 필요한 것은 마지막 위치의 점수뿐이다. 그래서 `logits[0, -1]`을 꺼내고, 가장 큰 값의 번호를 `mx.argmax`로 골랐다. 답은 94다.

## 한 토큰씩 붙이며 반복하기

이제 맨 앞의 그림을 코드로 옮긴다.

```python
seq = [5, 17, 42]
for _ in range(5):
    out = model(mx.array([seq]))
    nxt = mx.argmax(out[0, -1]).item()
    seq.append(nxt)
print(seq)
```

```text
[5, 17, 42, 94, 94, 94, 94, 58]
```

토큰 5개가 새로 붙었다. 학습하지 않은 모델이라 94를 반복하다 58로 바뀌는 것에 뜻은 없다. 중요한 것은 구조다. 모델은 한 번에 한 토큰만 정하고, 그 토큰을 입력에 붙여 다시 부른다.

`mlx-lm`에서 이 반복을 맡는 함수가 `generate_step`이다.

```python
from mlx_lm.generate import generate_step

prompt = mx.array([5, 17, 42])
steps = generate_step(prompt, model, max_tokens=5)
print([tok for tok, logprobs in steps])
```

```text
[94, 94, 94, 94, 58]
```

손으로 만든 반복과 같은 토큰 5개가 나왔다. 소스 설명에 따르면 `generate_step`은 토큰 하나와 로그 확률 벡터를 한 쌍씩 내놓는다. `sampler`를 주지 않으면 `greedy_sampler`를 쓰고, 이 함수는 `mx.argmax(logprobs, axis=-1)` 한 줄이다. 그래서 손으로 쓴 `argmax` 반복과 결과가 같다.

{: .note }
소스를 보면 README의 `generate`는 `stream_generate`를 부르고, `stream_generate`는 초안 모델(`draft_model`)을 주지 않으면 이 `generate_step`으로 토큰을 만든다.

## 같은 계산을 다시 하지 않기: KV 캐시

손으로 만든 반복에는 낭비가 있다. 다섯 번째 호출에서 모델은 토큰 7개를 처음부터 다시 계산한다. 앞의 6개는 이미 한 번 계산한 적이 있는데도 그렇다.

언어 모델의 각 블록에는 **어텐션**이 있다. 어텐션은 지금 토큰을 계산할 때 앞 토큰들의 정보를 다시 참고하는 단계다. 이때 앞 토큰마다 key와 value라는 참고용 자료를 만든다. **KV 캐시**는 이 key와 value를 모아 두는 저장소다. 시험 볼 때 앞에서 푼 계산을 여백에 적어 두고 다시 보는 것과 같다.

```python
from mlx_lm.models.cache import make_prompt_cache

cache = make_prompt_cache(model)
print(len(cache), type(cache[0]).__name__)
model(mx.array([[5, 17, 42]]), cache=cache)
print(cache[0].offset)
model(mx.array([[94]]), cache=cache)
print(cache[0].offset)
k, v = cache[0].keys_and_values()
print(k.shape)
```

```text
2 KVCache
3
4
(1, 4, 4, 16)
```

하나씩 읽어 보자.

- 블록이 2개라서 캐시도 2개다. 소스의 `make_prompt_cache`는 층마다 `KVCache`를 하나씩 만든다.
- 토큰 3개를 넣자 `offset`이 3이 됐다. 저장한 토큰 수다.
- 두 번째 호출에는 새 토큰 94 **하나만** 넣었다. 앞 3개는 캐시에서 꺼내 쓰고, `offset`은 4가 됐다.
- key의 shape `(1, 4, 4, 16)`은 문장 1개, 갈래 4개, 토큰 4개, 갈래마다 숫자 16개다. 16은 `64 ÷ 4`다.

`generate_step`은 이 캐시를 스스로 만든다. 소스를 보면 프롬프트의 마지막 토큰 앞까지를 먼저 모델에 넣어 캐시를 채운다. 그다음부터는 새 토큰 하나씩만 모델에 넣는다.

{: .tip }
쉽게 말하면, 캐시가 없으면 매번 처음부터 다시 읽고, 캐시가 있으면 새로 온 한 토큰만 읽는다.

`generate_step` 소스에는 [지연 평가 글]({{ '/ai/mlx/lazy-evaluation/' | relative_url }})에서 본 장면도 있다. 다음 토큰 계산을 `mx.async_eval`로 미리 걸어 두고, 그동안 현재 토큰을 `yield`로 내보낸다.

## 다음 토큰을 고르는 방법: 샘플러

지금까지는 늘 점수 1등을 골랐다. 이것을 **greedy**라고 한다. 늘 같은 답을 낸다. `mlx_lm.sample_utils.make_sampler`로 고르는 방법을 바꿀 수 있다.

예제를 단순하게 하려고, 토큰이 3개뿐이고 확률이 `0.1, 0.6, 0.3`인 경우를 만든다. 샘플러는 확률의 로그(`logprobs`)를 받는다.

```python
from mlx_lm.sample_utils import make_sampler

lp = mx.log(mx.array([[0.1, 0.6, 0.3]]))
greedy = make_sampler(temp=0.0)
print(greedy.__name__, greedy(lp).tolist())

hot = make_sampler(temp=1.0)
mx.random.seed(1)
picks = [hot(lp).item() for _ in range(1000)]
print([picks.count(i) for i in range(3)])
```

```text
greedy_sampler [1]
[124, 598, 278]
```

`temp=0`이면 소스가 바로 `greedy_sampler`를 돌려준다. 확률 0.6인 1번만 고른다.

`temp=1.0`이면 확률에 따라 뽑는다. 1000번 뽑았더니 0번, 1번, 2번이 각각 124번, 598번, 278번 나왔다. 확률 0.1, 0.6, 0.3과 비슷한 비율이다. **온도(temperature)**는 이 뽑기를 얼마나 고르게 할지 정하는 값이다. `make_sampler` 설명에는 `top_p`, `min_p`, `top_k`처럼 후보를 줄이는 옵션도 있다.

{: .question }
`temp`를 0보다 크게 하면 같은 프롬프트에서도 매번 다른 글이 나올 수 있다. 이 글의 1000번 결과도 `mx.random.seed(1)`로 시작점을 고정했기 때문에 다시 실행해도 같았다.

## 폴더에 저장하고 load_model로 불러오기

소스의 `load_model`은 모델 폴더에서 `config.json`과 `model*.safetensors` 파일을 찾는다. 같은 모양의 폴더를 직접 만들어 보자.

```python
import json
from pathlib import Path
from mlx_lm.utils import load_model

path = Path("tiny")
path.mkdir(exist_ok=True)
cfg_text = json.dumps(cfg)
(path / "config.json").write_text(cfg_text)
model.save_weights(str(path / "model.safetensors"))
print(sorted(p.name for p in path.iterdir()))

loaded, config = load_model(path)
print(type(loaded).__module__)
print(mx.allclose(model(ids), loaded(ids)).item())
```

```text
['config.json', 'model.safetensors']
mlx_lm.models.llama
True
```

`Module.save_weights`는 파일 확장자가 `.safetensors`면 safetensors 형식으로 저장한다. `load_model`은 `config.json`의 `"llama"`를 보고 `mlx_lm.models.llama`의 모델을 만들고, 저장한 가중치를 넣었다. 같은 입력에 같은 로짓을 내므로 `True`다.

`load` 함수는 여기에 두 가지를 더한다. 이 머신에 설치된 소스 순서는 다음과 같다.

1. 경로가 로컬에 없으면 Hugging Face Hub에서 내려받는다.
2. `load_model`로 모델을 만들고 가중치를 넣는다.
3. `load_tokenizer`로 같은 폴더의 토크나이저를 불러온다.

위 `tiny` 폴더에는 토크나이저 파일이 없다. 그래서 이 머신에서 `load("tiny")`를 실행하니 `load_tokenizer` 단계에서 `ValueError`가 났다. 1단계에서 Hub로부터 내려받을 때는 `*.json`, `tokenizer.model` 같은 토크나이저 파일 이름도 내려받기 목록(`DEFAULT_ALLOW_PATTERNS`)에 들어 있다.

## 4비트 양자화

README의 기본 모델 이름은 `mlx-community/Llama-3.2-3B-Instruct-4bit`다. 끝의 `4bit`는 가중치를 4비트로 줄였다는 뜻이다. 이렇게 숫자를 적은 비트로 줄여 담는 것을 **양자화**라고 한다. 소수점 아래 여러 자리를 반올림해서 공책 칸을 아끼는 것과 비슷하다.

`load_model` 소스는 `config.json`에 `quantization` 항목이 있으면 `nn.quantize`로 모델의 층을 바꾼 뒤 가중치를 넣는다. 우리 모델에 `nn.quantize`를 직접 적용해 보자.

```python
import mlx.nn as nn

def nbytes(m):
    return sum(v.nbytes for _, v in
               tree_flatten(m.parameters()))

print("before", nbytes(model))
nn.quantize(model, group_size=64, bits=4)
mx.eval(model.parameters())
print("after ", nbytes(model))
print(model.model.layers[0].mlp.up_proj)
print(mx.argmax(model(ids)[0, -1]).item())
```

```text
before 380160
after  60480
QuantizedLinear(input_dims=64, output_dims=128, bias=False, group_size=64, bits=4, mode=affine)
94
```

가중치가 차지하는 바이트가 380,160에서 60,480으로 줄었다. 약 6분의 1이다.

- 전: 파라미터 95,040개가 모두 `float32`(4바이트)라서 `95,040 × 4 = 380,160`이다.
- 후: `Linear`가 `QuantizedLinear`로 바뀌었다. 문서에 따르면 `nn.quantize`는 기본으로 `Linear`와 `Embedding` 층을 양자화한다.

줄어든 값을 맞춰 보자. 이 머신에서 `QuantizedLinear(64 → 128)` 하나를 들여다보니 `weight`는 `(128, 8)` 모양의 `uint32`였다. 입력 64개 × 4비트 = 256비트 = `uint32` 8개다. 그리고 `scales`, `biases`가 줄마다 하나씩 `float32`로 있었다. `mx.quantize` 문서는 한 줄에서 `group_size`개씩 묶어 양자화하고, 한 묶음이 scale과 bias를 공유한다고 설명한다.

| 부분 | 계산 | 바이트 |
| --- | --- | ---: |
| 4비트 가중치 | 94,720개 × 0.5 | 47,360 |
| 묶음마다 scale, bias | 1,480묶음 × 2 × 4 | 11,840 |
| 양자화하지 않은 RMSNorm | 320개 × 4 | 1,280 |
| 합계 | | 60,480 |

94,720은 RMSNorm 320개를 뺀 파라미터 수이고, 1,480은 `94,720 ÷ 64`다.

{: .warning }
4비트로 줄인 값은 원래 값과 정확히 같지 않다. 이 예제에서 마지막 줄의 다음 토큰은 양자화 전과 같은 94였지만, 무작위 모델 하나에서 본 결과일 뿐이다. 실제 모델의 품질이 얼마나 바뀌는지는 이 글에서 확인하지 않았다.

## 실제 모델을 실행하는 명령

여기부터는 이 머신에서 실행하지 못한 내용이다. 공식 README에 적힌 명령을 그대로 옮긴다.

설치:

```bash
pip install mlx-lm
```

명령줄에서 텍스트 생성과 대화:

```bash
mlx_lm.generate --prompt "How tall is Mt Everest?"
mlx_lm.chat
```

README에 따르면 모델을 지정하지 않으면 `mlx-community/Llama-3.2-3B-Instruct-4bit`를 쓴다. 다른 모델은 `--model`로 고른다. `-h`를 붙이면 옵션 목록이 나온다. 이 머신에서 `-h`는 실행됐고 `--model`, `--adapter-path` 같은 옵션이 출력됐다.

Python에서:

```python
from mlx_lm import load, generate

repo = "mlx-community/Mistral-7B-Instruct-v0.3-4bit"
model, tokenizer = load(repo)

messages = [{"role": "user",
             "content": "Write a story about Einstein"}]
prompt = tokenizer.apply_chat_template(
    messages, add_generation_prompt=True,
)
text = generate(model, tokenizer, prompt=prompt,
                verbose=True)
```

이 코드의 흐름은 본문에서 본 것과 같다. `load`가 내려받기 → `load_model` → `load_tokenizer`를 하고, `apply_chat_template`가 대화를 모델이 기대하는 형식의 프롬프트로 바꾸고, `generate`가 `generate_step`으로 토큰을 하나씩 만든다.

{: .note }
Mac의 GPU에서 이 모델이 얼마나 빠른지, 메모리를 얼마나 쓰는지는 이 글에서 측정하지 않았다. 직접 실행할 때는 [지연 평가 글]({{ '/ai/mlx/lazy-evaluation/' | relative_url }})의 측정 방법을 따른다.

## 주요 API

| API | 역할 |
| --- | --- |
| `llama.ModelArgs(...)`, `llama.Model(args)` | `mlx_lm.models.llama`. 설정으로 Llama 구조 모델을 만든다 |
| `model(ids, cache=)` | 토큰 번호 배열을 받아 위치마다 다음 토큰 점수(logits)를 낸다 |
| `generate_step(prompt, model, ...)` | `mlx_lm.generate`. 한 토큰씩 생성하는 제너레이터 |
| `make_prompt_cache(model)` | `mlx_lm.models.cache`. 층마다 KV 캐시를 만든다 |
| `make_sampler(temp=, top_p=, ...)` | `mlx_lm.sample_utils`. 점수에서 다음 토큰을 고르는 함수를 만든다 |
| `model.save_weights(path)` | 가중치를 safetensors로 저장 |
| `load_model(path)` | `mlx_lm.utils`. `config.json`과 가중치 파일로 모델을 불러온다 |
| `nn.quantize(model, group_size=, bits=)` | 선형 층을 양자화 층으로 바꾼다 |
| `load(repo)`, `generate(model, tokenizer, prompt=)` | `mlx_lm`. 공개 모델 불러오기와 텍스트 생성 |

## 실습 소스

본문의 예제 코드를 파일로 받을 수 있다. 내려받은 파일을 한 폴더에 두고 본문 순서대로 실행한다.

패키지는 `pip install -r requirements.txt`로 설치한다.

- [requirements.txt]({{ '/assets/examples/mlx/mlx-lm/requirements.txt' | relative_url }})
- [tiny_llama.py]({{ '/assets/examples/mlx/mlx-lm/tiny_llama.py' | relative_url }})

## 정리

{: .note }
언어 모델은 토큰 번호를 받아 위치마다 다음 토큰 점수(로짓)를 내놓는다. 마지막 위치의 점수로 한 토큰을 골라 붙이고 다시 부르는 것이 생성이다.

- `mlx-lm`의 모델도 `nn.Module` 트리다. 작은 Llama 설정의 파라미터 95,040개를 층별로 셀 수 있었다.
- `config.json`의 `model_type`이 어떤 모델 코드를 쓸지 정한다. `"llama"`는 `mlx_lm.models.llama`다.
- `generate_step`은 손으로 쓴 `argmax` 반복과 같은 토큰을 냈다. 기본 샘플러가 `argmax`이기 때문이다.
- KV 캐시는 층마다 앞 토큰의 key, value를 저장한다. 캐시가 있으면 새 토큰 하나만 모델에 넣는다.
- `make_sampler(temp=0)`은 greedy, `temp>0`은 확률에 따라 뽑는다.
- `load`는 내려받기 → `load_model` → `load_tokenizer` 순서다. `load_model`은 `config.json`과 `model*.safetensors`를 읽는다.
- `nn.quantize(..., bits=4)`로 이 모델의 가중치 바이트가 380,160에서 60,480으로 줄었다.

## 다음 편

다음 편은 아직 준비 중이다.

함께 읽으면 좋은 글:

- [MLX로 작은 신경망 만들기]({{ '/ai/mlx/neural-network/' | relative_url }}) — `nn.Module`, `nn.Linear`, 파라미터 트리
- [MLX 지연 평가와 성능 측정]({{ '/ai/mlx/lazy-evaluation/' | relative_url }}) — `mx.eval`, `mx.async_eval`과 측정 방법

## 참고

- [ml-explore/mlx-lm 저장소 README](https://github.com/ml-explore/mlx-lm) — 설치, `mlx_lm.generate`, `load`·`generate`·`stream_generate`, 샘플러, 기본 모델
- mlx-lm 0.32.2 소스: `mlx_lm/utils.py`(`load`, `load_model`, `_get_classes`), `mlx_lm/generate.py`(`generate_step`), `mlx_lm/sample_utils.py`(`make_sampler`, `greedy_sampler`), `mlx_lm/models/llama.py`, `mlx_lm/models/cache.py`(`make_prompt_cache`, `KVCache`)
- [MLX nn.quantize](https://ml-explore.github.io/mlx/build/html/python/_autosummary/mlx.nn.quantize.html) — 기본으로 양자화하는 층
- [MLX mlx.core.quantize](https://ml-explore.github.io/mlx/build/html/python/_autosummary/mlx.core.quantize.html) — `group_size`, `bits`, scale과 bias
- [MLX nn.QuantizedLinear](https://ml-explore.github.io/mlx/build/html/python/nn/_autosummary/mlx.nn.QuantizedLinear.html) — 양자화된 Linear 층
- [MLX Module.save_weights](https://ml-explore.github.io/mlx/build/html/python/nn/_autosummary/mlx.nn.Module.save_weights.html) — 확장자에 따른 저장 형식
- [MLX 설치 문서](https://ml-explore.github.io/mlx/build/html/install.html) — Linux CPU 설치(`mlx[cpu]`)
