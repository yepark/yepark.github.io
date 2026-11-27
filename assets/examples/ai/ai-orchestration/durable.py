# 체크포인트와 멱등 키 실습. 외부 서비스도 가짜다.
import json
import pathlib
import sys

JOURNAL = pathlib.Path("journal.json")
SENT = pathlib.Path("provider.json")  # 가짜 메일 서버


def load(p):
    return json.loads(p.read_text()) if p.exists() else {}


def send_mail(key, body):
    sent = load(SENT)
    if key in sent:                 # 같은 키는 한 번만
        return "duplicate ignored"
    sent[key] = body
    SENT.write_text(json.dumps(sent))
    return "sent"


STEPS = ["research", "draft", "notify", "publish"]


def run(run_id, crash_at=None):
    j = load(JOURNAL)
    for step in STEPS:
        if j.get(step) == "done":
            print(f"  {step:8s} skip (checkpoint)")
            continue
        if step == "notify":
            key = f"{run_id}:notify"  # 실행 ID에서 만든 키
            print(f"  {step:8s}", send_mail(key, "draft"))
        else:
            print(f"  {step:8s} run")
        if step == crash_at:
            print("  !! crash before checkpoint")
            sys.exit(1)
        j[step] = "done"
        JOURNAL.write_text(json.dumps(j))


if __name__ == "__main__":
    run("run-42", crash_at=sys.argv[1]
        if len(sys.argv) > 1 else None)
