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

ids = mx.array([[5, 17, 42]])
logits = model(ids)
print(logits.shape)
last = logits[0, -1]
print(mx.argmax(last).item())

seq = [5, 17, 42]
for _ in range(5):
    out = model(mx.array([seq]))
    nxt = mx.argmax(out[0, -1]).item()
    seq.append(nxt)
print(seq)

from mlx_lm.generate import generate_step

prompt = mx.array([5, 17, 42])
steps = generate_step(prompt, model, max_tokens=5)
print([tok for tok, logprobs in steps])

from mlx_lm.models.cache import make_prompt_cache

cache = make_prompt_cache(model)
print(len(cache), type(cache[0]).__name__)
model(mx.array([[5, 17, 42]]), cache=cache)
print(cache[0].offset)
model(mx.array([[94]]), cache=cache)
print(cache[0].offset)
k, v = cache[0].keys_and_values()
print(k.shape)

from mlx_lm.sample_utils import make_sampler

lp = mx.log(mx.array([[0.1, 0.6, 0.3]]))
greedy = make_sampler(temp=0.0)
print(greedy.__name__, greedy(lp).tolist())

hot = make_sampler(temp=1.0)
mx.random.seed(1)
picks = [hot(lp).item() for _ in range(1000)]
print([picks.count(i) for i in range(3)])

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
