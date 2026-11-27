import uvicorn
from starlette.applications import Starlette

from a2a.server.request_handlers import (
    DefaultRequestHandler,
)
from a2a.server.routes import (
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentSkill,
)

from agent import ExchangeExecutor

skill = AgentSkill(
    id="usd_to_krw",
    name="달러 → 원 계산",
    description="달러 금액을 원화로 바꾼다.",
    tags=["exchange", "example"],
    examples=["100달러는 몇 원?"],
)

card = AgentCard(
    name="Exchange Agent",
    description="LLM 없이 고정 환율로 계산하는 예제",
    version="0.1.0",
    default_input_modes=["text/plain"],
    default_output_modes=[
        "text/plain",
        "application/json",
    ],
    capabilities=AgentCapabilities(streaming=True),
    supported_interfaces=[
        AgentInterface(
            protocol_binding="JSONRPC",
            url="http://127.0.0.1:9999",
            protocol_version="1.0",
        )
    ],
    skills=[skill],
)

handler = DefaultRequestHandler(
    agent_executor=ExchangeExecutor(),
    task_store=InMemoryTaskStore(),
    agent_card=card,
)

routes = []
routes.extend(create_agent_card_routes(card))
routes.extend(create_jsonrpc_routes(handler, "/"))
app = Starlette(routes=routes)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=9999)
