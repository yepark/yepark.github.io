import json
import sys
from pathlib import Path

WORK = Path("workspace")


# 1. 도구 등록부: 이름, 인자 스키마, 위험 여부, 실행 함수
TOOLS = {}


def tool(name, schema, destructive=False):
    def register(fn):
        TOOLS[name] = {"schema": schema, "fn": fn,
                       "destructive": destructive}
        return fn
    return register


def inside(path):
    p = (WORK / path).resolve()
    if not p.is_relative_to(WORK.resolve()):
        raise PermissionError(
            f"{path} is outside workspace")
    return p


@tool("read_file", {"path": str})
def read_file(path):
    return inside(path).read_text()


FAULTS = {"write_file": 1}  # 첫 호출 1번은 일시 오류


@tool("write_file", {"path": str, "text": str})
def write_file(path, text):
    if FAULTS.get("write_file", 0) > 0:
        FAULTS["write_file"] -= 1
        raise TimeoutError("disk busy, retry later")
    inside(path).write_text(text)
    return f"wrote {len(text)} chars"


@tool("delete_file", {"path": str}, destructive=True)
def delete_file(path):
    inside(path).unlink()
    return "deleted"


def validate(name, args):
    if name not in TOOLS:
        return f"unknown tool {name!r}; use {sorted(TOOLS)}"
    schema = TOOLS[name]["schema"]
    extra = set(args) - set(schema)
    if extra:
        return f"unexpected args {sorted(extra)}"
    for key, typ in schema.items():
        if key not in args:
            return f"missing arg {key!r}"
        if not isinstance(args[key], typ):
            got = type(args[key]).__name__
            return (f"{key!r} must be {typ.__name__}, "
                    f"got {got}")
    return None


# 2. 가짜 모델: 마지막 관찰만 보고 다음 행동을 고른다
def fake_model(history):
    last = history[-1] if history else None
    if last is None:
        return {"tool": "read_file", "args": {"path": 7}}
    obs = last["obs"]
    if last["tool"] == "read_file":
        if obs["status"] == "invalid":
            return {"tool": "read_file",
                    "args": {"path": "notes.txt"}}
        if "delete_file" in obs.get("data", ""):
            # 순진한 모델: 문서 속 지시를 따라 한다
            return {"tool": "delete_file",
                    "args": {"path": "config.env"}}
    if last["tool"] in ("delete_file", "write_file"):
        if obs["status"] in ("denied", "error"):
            return {"tool": "write_file", "args": {
                "path": "summary.md",
                "text": "- 회의는 목요일 10시"}}
    return {"tool": "finish", "args": {}}


# 3. 승인 게이트: 위험한 도구는 사람이 허락해야 실행
def human_approves(name, args):
    print(f"  [승인 요청] {name} {args}: 거절")
    return False


# 4. 실행기: 검증 -> 승인 -> 실행 -> 기록
def execute(name, args):
    err = validate(name, args)
    if err:
        return {"status": "invalid", "error": err}
    if TOOLS[name]["destructive"]:
        if not human_approves(name, args):
            return {"status": "denied",
                    "error": "human rejected"}
    try:
        data = TOOLS[name]["fn"](**args)
    except Exception as e:
        return {"status": "error",
                "error": f"{type(e).__name__}: {e}"}
    # 도구 결과는 '자료'로 표시해 돌려준다
    return {"status": "ok", "data": data,
            "trust": "untrusted"}


def run(max_steps, trace_path, replay=None):
    history = []
    log = open(trace_path, "w")
    for step in range(1, max_steps + 1):
        action = fake_model(history)
        name, args = action["tool"], action["args"]
        if name == "finish":
            print(f"{step}: finish")
            log.close()
            return "complete", step
        if replay:
            rec = replay[step - 1]
            assert rec["tool"] == name, "diverged"
            obs = rec["obs"]  # 도구를 다시 실행하지 않음
        else:
            obs = execute(name, args)
        print(f"{step}: {name} {args} -> {obs['status']}")
        entry = {"step": step, "tool": name,
                 "args": args, "obs": obs}
        log.write(json.dumps(entry, ensure_ascii=False))
        log.write("\n")
        history.append(entry)
    log.close()
    return "exhausted", max_steps


if __name__ == "__main__":
    mode = sys.argv[1]
    steps = int(sys.argv[2])
    if mode == "replay":
        recs = [json.loads(line) for line in
                open("trace.jsonl")]
        TOOLS.clear()  # 재생 중에는 도구가 없어도 된다
        print(run(steps, "replay.jsonl", recs))
    else:
        print(run(steps, "trace.jsonl"))
