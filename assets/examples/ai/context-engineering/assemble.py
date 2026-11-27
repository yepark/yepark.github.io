import tiktoken

enc = tiktoken.get_encoding("o200k_base")


def tok(text: str) -> int:
    return len(enc.encode(text))


system = "너는 사내 규정 도우미다. 제공한 문서에서만 답하고, 근거 문서 id를 붙인다."
tools = '{"name":"search_policy","description":"사내 규정 검색","input_schema":{"type":"object","properties":{"query":{"type":"string"}}}}'
memory = "- 사용자는 인사팀 소속\n- 답은 세 문장 이내"
docs = [  # 검색 점수가 높은 순
    ("doc-leave-2026", "연차는 다음 해 3월 31일까지 최대 5일 이월할 수 있다. 단, 수습 기간 중 생긴 연차는 이월하지 않는다. " * 3),
    ("doc-leave-2024", "(폐기됨) 연차는 이월할 수 없다. " * 3),
    ("doc-holiday", "회사 창립기념일은 유급 휴일이다. " * 6),
]
old_turns = [f"[{i}번째 대화] 지난 업무 이야기 " * 12 for i in range(1, 9)]
recent_turns = ["사용자: 작년 연차가 7일 남았어.", "도우미: 확인했습니다."]
question = "사용자: 이 중 몇 일을 올해로 넘길 수 있어?"


def assemble(budget: int):
    # 줄이지 않는 층을 먼저 넣는다
    layers = [
        ("system", system), ("tools", tools), ("memory", memory),
        ("question", question), ("recent", "\n".join(recent_turns)),
    ]
    used = sum(tok(t) for _, t in layers)
    log = []
    # 문서: 점수 순으로 넣되, 남은 예산을 넘으면 뺀다
    for doc_id, text in docs:
        cost = tok(text)
        if used + cost <= budget:
            layers.append((doc_id, text)); used += cost
        else:
            log.append(f"drop {doc_id} ({cost} tok)")
    # 오래된 대화: 원문이 안 들어가면 한 줄 요약으로 바꾼다
    history = "\n".join(old_turns)
    if used + tok(history) <= budget:
        layers.append(("history", history)); used += tok(history)
    else:
        summary = "요약: 지난 대화 8턴은 업무 잡담, 결정 사항 없음"
        log.append(f"compact history {tok(history)} -> {tok(summary)} tok")
        layers.append(("history-summary", summary)); used += tok(summary)
    return used, [n for n, _ in layers], log


print("encoding:", enc.name)
for name, text in [("system", system), ("tools", tools), ("memory", memory),
                   ("docs", "".join(t for _, t in docs)),
                   ("old_turns", "\n".join(old_turns)), ("recent+question", "\n".join(recent_turns) + question)]:
    print(f"{name:16s} {tok(text):5d} tok  {len(text):5d} chars")
for budget in (1300, 400, 250):
    used, names, log = assemble(budget)
    print(f"\nbudget={budget} used={used}")
    print(" kept:", ", ".join(names))
    for line in log:
        print(" ", line)
