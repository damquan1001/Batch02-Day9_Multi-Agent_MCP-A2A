"""End-to-end test client for the Legal Multi-Agent System.

Sends a legal question to the Customer Agent and prints the response.
"""

import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

CUSTOMER_AGENT_URL = os.getenv("CUSTOMER_AGENT_URL", "http://localhost:10100")

QUESTION = (
    "If a company breaks a contract and avoids taxes, "
    "what are the legal and regulatory consequences?"
)


async def main() -> None:
    print(f"Connecting to Customer Agent at {CUSTOMER_AGENT_URL}")
    print(f"Question: {QUESTION}")
    print("-" * 60)

    api_key = os.getenv("A2A_API_KEY", "secret-a2a-key")
    headers = {"X-API-Key": api_key}

    async with httpx.AsyncClient(timeout=600.0, headers=headers) as http_client:
        # Resolve agent card
        card_url = f"{CUSTOMER_AGENT_URL}/.well-known/agent.json"
        try:
            card_resp = await http_client.get(card_url)
            card_resp.raise_for_status()
        except Exception as e:
            print(f"ERROR: Could not reach Customer Agent at {card_url}")
            print(f"  {e}")
            print("Make sure all services are running (./start_all.sh)")
            sys.exit(1)

        from a2a.types import AgentCard, Message, Part, Role, TextPart, MessageSendParams
        from a2a.client import A2AClient
        from uuid import uuid4

        agent_card = AgentCard.model_validate(card_resp.json())
        print(f"Connected to agent: {agent_card.name} v{agent_card.version}")
        print("-" * 60)

        # Build the legacy A2AClient
        client = A2AClient(httpx_client=http_client, agent_card=agent_card)

        # Share context ID across both messages to test memory
        shared_context_id = str(uuid4())

        # Construct the first message
        from a2a.types import SendMessageRequest, MessageSendParams as MSP
        message1 = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=QUESTION))],
            message_id=str(uuid4()),
            context_id=shared_context_id,
        )
        request1 = SendMessageRequest(
            id=str(uuid4()),
            params=MSP(message=message1),
        )

        print("Sending Turn 1 request (this may take 30-60s while agents chain)...\n")
        response1 = await client.send_message(request1)

        # Parse first response
        def parse_text(response) -> str:
            result_text = ""
            if hasattr(response, "root"):
                root = response.root
                if hasattr(root, "result"):
                    result = root.result
                    # Task with artifacts
                    if hasattr(result, "artifacts") and result.artifacts:
                        for artifact in result.artifacts:
                            for part in artifact.parts:
                                p = part.root if hasattr(part, "root") else part
                                if hasattr(p, "text"):
                                    result_text += p.text
                    # Message with parts
                    elif hasattr(result, "parts") and result.parts:
                        for part in result.parts:
                            p = part.root if hasattr(part, "root") else part
                            if hasattr(p, "text"):
                                result_text += p.text
            return result_text

        result_text1 = parse_text(response1)
        if result_text1:
            print("TURN 1 RESPONSE:")
            print("=" * 60)
            print(result_text1)
            print("=" * 60)
        else:
            print("No text response received for Turn 1. Raw response:")
            print(response1)
            return

        # Turn 2: Follow-up question in the same context
        print("\n" + "-" * 60)
        QUESTION_2 = "What was the first question I asked you? Please repeat it."
        print(f"Sending Turn 2 (Follow-up) request...")
        print(f"Question: {QUESTION_2}")
        print("-" * 60 + "\n")

        message2 = Message(
            role=Role.user,
            parts=[Part(root=TextPart(text=QUESTION_2))],
            message_id=str(uuid4()),
            context_id=shared_context_id,
        )
        request2 = SendMessageRequest(
            id=str(uuid4()),
            params=MSP(message=message2),
        )

        response2 = await client.send_message(request2)
        result_text2 = parse_text(response2)

        if result_text2:
            print("TURN 2 RESPONSE:")
            print("=" * 60)
            print(result_text2)
            print("=" * 60)
        else:
            print("No text response received for Turn 2. Raw response:")
            print(response2)


if __name__ == "__main__":
    asyncio.run(main())