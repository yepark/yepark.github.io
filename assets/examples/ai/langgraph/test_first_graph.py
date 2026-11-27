from langgraph.checkpoint.memory import InMemorySaver
from ex01_first import builder, choose_route, normalize


def test_normalize_is_plain_function():
    assert normalize({"original": " a "}) == {
        "cleaned": "a"}


def test_router():
    assert choose_route({"cleaned": ""}) == "empty"
    assert choose_route({"cleaned": "x"}) == "valid"


def test_one_node_of_compiled_graph():
    app = builder.compile()
    out = app.nodes["write_answer"].invoke(
        {"cleaned": "abc"})
    assert out["answer"].endswith("글자 수: 3")


def test_partial_run_from_middle():
    app = builder.compile(checkpointer=InMemorySaver())
    cfg = {"configurable": {"thread_id": "t"}}
    # normalize가 이미 끝난 것처럼 상태를 심는다
    app.update_state(cfg, {"original": "",
                           "cleaned": ""},
                     as_node="normalize")
    out = app.invoke(None, cfg)
    assert out["answer"] == "내용을 입력해 주세요."


def test_full_graph():
    app = builder.compile()
    out = app.invoke({"original": "  hi "})
    assert out["cleaned"] == "hi"
