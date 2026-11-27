import asyncio

import httpx
from a2a.client import (
    A2ACardResolver,
    ClientConfig,
    create_client,
)
from a2a.helpers import new_text_message
from a2a.types import (
    Role,
    SendMessageRequest,
    TaskState,
)

URL = "http://127.0.0.1:9999"


async def main() -> None:
    async with httpx.AsyncClient() as http:
        resolver = A2ACardResolver(http, URL)
        card = await resolver.get_agent_card()
    print("카드:", card.name, card.skills[0].id)

    config = ClientConfig(streaming=True)
    client = await create_client(
        agent=card, client_config=config
    )
    message = new_text_message(
        "30달러는?", role=Role.ROLE_USER
    )
    request = SendMessageRequest(message=message)
    async for event in client.send_message(request):
        kind = event.WhichOneof("payload")
        print("이벤트:", kind)
        if kind == "status_update":
            state = event.status_update.status.state
            print("  상태:", TaskState.Name(state))
        if kind == "artifact_update":
            part = event.artifact_update.artifact.parts[0]
            print("  결과:", part.text)
    await client.close()


asyncio.run(main())
