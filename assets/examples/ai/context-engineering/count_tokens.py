import tiktoken
from transformers import AutoTokenizer

enc = tiktoken.get_encoding("o200k_base")
qwen = AutoTokenizer.from_pretrained("mlx-community/Qwen2.5-3B-Instruct-4bit")

for s in ["연차는 다음 해 3월 31일까지 최대 5일 이월할 수 있다.",
          "Up to 5 days of annual leave can be carried over until March 31 of the next year."]:
    print(len(s), "chars | o200k_base:", len(enc.encode(s)), "| Qwen2.5:", len(qwen.encode(s)), "|", s)
