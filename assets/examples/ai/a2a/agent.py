import re

from a2a.helpers import (
    get_message_text,
    new_data_part,
    new_task_from_user_message,
    new_text_message,
    new_text_part,
)
from a2a.server.agent_execution import (
    AgentExecutor,
    RequestContext,
)
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater

RATE = 1400  # 예제용 고정값: 1 USD = 1400 KRW


class ExchangeExecutor(AgentExecutor):
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        task = context.current_task
        if task is None:
            task = new_task_from_user_message(
                context.message
            )
            await event_queue.enqueue_event(task)

        updater = TaskUpdater(
            event_queue, task.id, task.context_id
        )
        await updater.start_work(
            new_text_message("계산 중...")
        )

        text = get_message_text(context.message)
        found = re.search(r"\d+(\.\d+)?", text)
        if found is None:
            await updater.requires_input(
                new_text_message("몇 달러인가요?")
            )
            return

        usd = float(found.group())
        krw = usd * RATE
        answer = f"{usd:g} USD = {krw:,.0f} KRW"
        await updater.add_artifact(
            name="result",
            parts=[
                new_text_part(answer),
                new_data_part({"usd": usd, "krw": krw}),
            ],
        )
        await updater.complete(new_text_message("완료"))

    async def cancel(self, context, event_queue):
        raise NotImplementedError("취소는 지원하지 않는다")
