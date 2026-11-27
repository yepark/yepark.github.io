from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

sentences = [
    "사과를 먹었다.",
    "과일을 하나 먹었다.",
    "자동차를 수리했다.",
]

embeddings = model.encode(sentences, normalize_embeddings=True)

def cosine_sim(a, b):
    return float(np.dot(a, b))  # 정규화된 벡터이므로 내적 = 코사인 유사도

query = embeddings[0]  # "사과를 먹었다."
for i, (sent, emb) in enumerate(zip(sentences, embeddings)):
    score = cosine_sim(query, emb)
    print(f"{score:.4f}  {sent}")
