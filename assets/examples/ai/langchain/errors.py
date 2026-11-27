from langchain_core.runnables import RunnableLambda

calls = {"n": 0}
def flaky(x):
    calls["n"] += 1
    if calls["n"] < 3:
        raise ConnectionError(f"{calls['n']}번째 실패")
    return f"{calls['n']}번째에 성공: {x}"

safe = RunnableLambda(flaky).with_retry(
    retry_if_exception_type=(ConnectionError,),
    stop_after_attempt=3,
    wait_exponential_jitter=False,
)
print(safe.invoke("hi"))

def broken(x):
    raise TimeoutError("주 모델 응답 없음")
main = RunnableLambda(broken)
backup = RunnableLambda(lambda x: f"백업 답: {x}")
print(main.with_fallbacks([backup]).invoke("hi"))

try:
    RunnableLambda(lambda x: 1 / 0).with_retry(
        retry_if_exception_type=(ConnectionError,),
    ).invoke("x")
except ZeroDivisionError as e:
    print("재시도 안 함:", type(e).__name__)
