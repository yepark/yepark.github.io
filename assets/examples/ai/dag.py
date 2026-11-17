"""Python 3.12+: dependency scheduling without external packages or API keys."""

import asyncio
from graphlib import CycleError, TopologicalSorter


# Each value contains prerequisites, not the next nodes.
DEPENDENCIES = {
    "question": set(),
    "retrieve_manual": {"question"},
    "retrieve_policy": {"question"},
    "draft": {"retrieve_manual", "retrieve_policy"},
    "verify": {"draft"},
}


async def execute(node, inputs):
    # These fixed strings model data flow; no search service or LLM is called.
    if node == "question":
        return "파일을 내보내려면 어떤 권한이 필요한가?"
    if node == "retrieve_manual":
        await asyncio.sleep(0.01)  # Stand-in for an I/O wait.
        assert "question" in inputs
        return {"id": "manual-1", "text": "설정에서 내보내기를 선택한다."}
    if node == "retrieve_policy":
        await asyncio.sleep(0.01)
        assert "question" in inputs
        return {"id": "policy-1", "text": "내보내기에는 관리자 권한이 필요하다."}
    if node == "draft":
        manual = inputs["retrieve_manual"]
        policy = inputs["retrieve_policy"]
        return {
            "text": f"{policy['text']} {manual['text']}",
            "sources": [manual["id"], policy["id"]],
        }
    if node == "verify":
        draft = inputs["draft"]
        assert draft["sources"] == ["manual-1", "policy-1"]
        return {"status": "ready_for_review", "answer": draft}
    raise ValueError(f"Unknown node: {node}")


async def run_graph(dependencies, worker=execute):
    sorter = TopologicalSorter(dependencies)
    sorter.prepare()  # Detect a cycle before any task starts.
    results = {}
    batches = []

    while sorter.is_active():
        ready = tuple(sorted(sorter.get_ready()))
        # This small runner waits for the whole batch (a deliberate barrier).
        async with asyncio.TaskGroup() as group:
            tasks = {
                node: group.create_task(
                    worker(node, {p: results[p] for p in dependencies[node]})
                )
                for node in ready
            }
        # A failed task raises before this point; dependents are not released.
        results.update({node: task.result() for node, task in tasks.items()})
        sorter.done(*ready)
        batches.append(ready)

    return results, batches


async def main():
    results, batches = await run_graph(DEPENDENCIES)
    assert batches == [
        ("question",),
        ("retrieve_manual", "retrieve_policy"),
        ("draft",),
        ("verify",),
    ]
    assert results["verify"]["status"] == "ready_for_review"
    print("batches:", batches)
    print("answer:", results["verify"]["answer"]["text"])

    cyclic = {**DEPENDENCIES, "question": {"verify"}}
    try:
        await run_graph(cyclic)
    except CycleError:
        print("cycle: rejected before execution")
    else:
        raise AssertionError("The cycle was not detected")

    visited = []

    async def failing_worker(node, inputs):
        visited.append(node)
        if node == "retrieve_policy":
            raise RuntimeError("Policy source unavailable")
        return await execute(node, inputs)

    try:
        await run_graph(DEPENDENCIES, failing_worker)
    except ExceptionGroup:
        assert "draft" not in visited
        assert "verify" not in visited
        print("failure: draft and verify did not run")
    else:
        raise AssertionError("The expected failure did not occur")


if __name__ == "__main__":
    asyncio.run(main())
