import json
from mlx_lm import load, generate
import react_loop as rl

MODEL = "mlx-community/Qwen2.5-3B-Instruct-4bit"
model, tok = load(MODEL)

SYSTEM = """You control a tool loop.
Tools:
- get_order(order_id): order status
- get_eta(order_id): delivery date
- finish(answer): final answer to user
Reply with ONE JSON object only, e.g.
{"tool": "get_order", "args": {"order_id": "X"}}"""


def llm_policy(state):
    msgs = [{"role": "system", "content": SYSTEM},
            {"role": "user", "content": state.goal}]
    pairs = zip(state.actions, state.trace)
    for (name, args), (_, _, obs) in pairs:
        msgs.append({"role": "assistant",
                     "content": json.dumps(
                         {"tool": name,
                          "args": args})})
        msgs.append({"role": "user", "content":
                     "Observation: "
                     + json.dumps(obs)})
    prompt = tok.apply_chat_template(
        msgs, add_generation_prompt=True,
        tokenize=False)
    out = generate(model, tok, prompt=prompt,
                   max_tokens=80)
    print("    model:", out.strip())
    try:
        act = json.loads(out.strip())
        name = act["tool"]
        args = act.get("args", {})
        if name == "finish":
            return "finish", {}
        if name not in rl.TOOLS:
            raise KeyError(name)
        if set(args) != {"order_id"}:
            raise ValueError("need order_id")
        return name, args
    except Exception as e:
        return "invalid", {"why": repr(e)}


rl.TOOLS["invalid"] = lambda why: {"error": why}
goal = "주문 A-100의 배송 상태와 도착 예정일을 알려줘."
reason, s = rl.run(llm_policy, goal, max_steps=6)
print("->", reason, "steps =", s.step)
print("facts:", s.facts)
for step, name, obs in s.trace:
    print(f"  {step}. {name:<9} {obs}")
