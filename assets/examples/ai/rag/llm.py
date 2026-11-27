from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from mlx_lm import generate, load
from mlx_lm.sample_utils import make_sampler

MODEL_ID = "mlx-community/Qwen2.5-3B-Instruct-4bit"
mlx_model, tokenizer = load(MODEL_ID)
ROLE = {"system": "system", "human": "user", "ai": "assistant"}

class LocalMLX(BaseChatModel):
    max_tokens: int = 200

    @property
    def _llm_type(self):
        return "local-mlx"

    def _generate(self, messages, stop=None,
                  run_manager=None, **kwargs):
        chat = [{"role": ROLE[m.type], "content": m.content}
                for m in messages]
        text = tokenizer.apply_chat_template(
            chat, add_generation_prompt=True, tokenize=False
        )
        out = generate(
            mlx_model, tokenizer, prompt=text,
            max_tokens=self.max_tokens,
            sampler=make_sampler(temp=0.0),
        )
        msg = AIMessage(content=out)
        return ChatResult(generations=[ChatGeneration(message=msg)])

model = LocalMLX()
