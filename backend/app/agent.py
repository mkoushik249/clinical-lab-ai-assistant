import json
import logging
import time

from openai import OpenAI

from app.config import settings
from app.lab_repository import get_active_lab_tests, search_lab_test
from app.retriever import search_knowledge_base

logger =logging.getLogger(__name__)
logger.setLevel(logging.INFO)

NO_DATA_RESPONSE = (
    "The requested information is not available "
    "in the approved laboratory data sources."
)


SYSTEM_PROMPT = """
You are a Multi language Clinical Laboratory AI Assistant.

You may assist only with approved laboratory-test information and approved
laboratory policy/procedure information, including specimen information,
turnaround information, specimen collection guidance, and critical-result
communication. When responding in another language translate only information
supported by tools do not add any medical or laboratory facts during translation.

Use search_lab_test for structured laboratory test information such as
test name, test code, specimen type, aliases, and turnaround time.

Use search_knowledge_base for laboratory policies, procedures,
specimen collection guidance, turnaround policies, and critical-result
communication.

Use list_lab_tests when the user asks what tests or laboratory information
is currently available.

For laboratory factual questions, use approved tool results as the only
source of facts. Do not use general medical or laboratory knowledge.

If a laboratory test may not exist in the approved data, use search_lab_test
and allow the approved database to determine whether it is supported.

Use conversation history to understand short follow-up questions and
references to previously discussed laboratory tests or policies.

If the approved tools do not return the requested information, state that
the information is not available in the approved laboratory data sources.

For greetings, acknowledgements, thanks, and other brief casual messages,
reply briefly without calling tools.

For requests outside the supported clinical laboratory scope, respond:
"I can only assist with approved clinical laboratory information."

Do not provide diagnoses, treatment advice, patient-specific interpretation,
or medical advice.
"""


def sql_lab_tool(search_text: str) -> dict:
    lab_test = search_lab_test(search_text.strip())

    if lab_test is None:
        return {
            "found": False,
            "data": None,
        }

    return {
        "found": True,
        "data": lab_test.model_dump(),
    }


def rag_policy_tool(query: str) -> dict:
    results = search_knowledge_base(query.strip())

    return {
        "found": bool(results),
        "results": results,
        "sources": list(
            dict.fromkeys(
                result["source_name"]
                for result in results
            )
        ),
    }


def list_lab_tests_tool() -> dict:
    tests = get_active_lab_tests()

    return {
        "found": bool(tests),
        "tests": [
            test.model_dump()
            for test in tests
        ],
    }


TOOLS = [
    {
        "type": "function",
        "name": "search_lab_test",
        "description": (
            "Search approved structured laboratory test data. "
            "Use for test codes, test names, aliases, specimen types, "
            "and turnaround times. Use this even when you are unsure "
            "whether the requested laboratory test exists."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "search_text": {
                    "type": "string",
                    "description": (
                        "Laboratory test code, full name, or alias."
                    ),
                }
            },
            "required": ["search_text"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "search_knowledge_base",
        "description": (
            "Search approved laboratory policies, procedures, specimen "
            "collection guidance, turnaround policies, and critical-result "
            "documentation."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "The laboratory policy or procedure question."
                    ),
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "list_lab_tests",
        "description": (
            "List approved active laboratory tests currently available "
            "in the structured laboratory database."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
]


def run_agent(
    user_question: str,
    history: list | None = None,
) -> dict:

    total_start = time.perf_counter()
    routing_ms = 0.0
    tool_ms = 0.0
    final_ms = 0.0

    if history is None:
        history = []

    client = OpenAI(
        api_key=settings.openai_api_key,
    )

    model_input = []
    MAX_CONTEXT_MESSAGES = 20

    for message in history[-MAX_CONTEXT_MESSAGES:]:
        model_input.append(
            {
                "role": message.role,
                "content": message.content,
            }
        )

    model_input.append(
        {
            "role": "user",
            "content": user_question,
        }
    )
    routing_start = time.perf_counter()

    response = client.responses.create(
        model=settings.chat_model,
        instructions=SYSTEM_PROMPT,
        input=model_input,
        tools=TOOLS,
        tool_choice="auto",
    )

    routing_ms = (
        time.perf_counter() - routing_start
    ) * 1000

    tool_outputs = []
    sources = []
    evidence_found = False

    for item in response.output:
        if item.type != "function_call":
            continue

        arguments = json.loads(item.arguments)
        tool_start = time.perf_counter()

        if item.name == "search_lab_test":
            result = sql_lab_tool(
                arguments["search_text"]
            )

            if result["found"]:
                evidence_found = True

        elif item.name == "search_knowledge_base":
            result = rag_policy_tool(
                arguments["query"]
            )

            if result["found"]:
                evidence_found = True
                sources.extend(
                    result["sources"]
                )

        elif item.name == "list_lab_tests":
            result = list_lab_tests_tool()

            if result["found"]:
                evidence_found = True

        else:
            continue

        tool_ms += (
            time.perf_counter() - tool_start
        ) * 1000

        tool_outputs.append(
            {
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": json.dumps(result),
            }
        )

    # Greetings, thanks and out-of-scope requests can be answered
    # directly according to SYSTEM_PROMPT.
    if not tool_outputs:
        total_ms = (
            time.perf_counter() - total_start
        ) * 1000

        logger.info(
            "agent_latency total_ms=%.1f routing_ms=%.1f "
            "tool_ms=0 final_ms=0",
            total_ms,
            routing_ms,
        )

        return {
            "answer": response.output_text,
            "sources": [],
        }

    # A factual tool was called but approved evidence was not found.
    if not evidence_found:
        total_ms = (
            time.perf_counter() - total_start
        ) * 1000

        logger.info(
            "agent_latency total_ms=%.1f routing_ms=%.1f "
            "tool_ms=%.1f final_ms=0",
            total_ms,
            routing_ms,
            tool_ms,
        )

        return {
            "answer": NO_DATA_RESPONSE,
            "sources": [],
        }

    final_start = time.perf_counter()

    final_response = client.responses.create(
        model=settings.chat_model,
        instructions=SYSTEM_PROMPT,
        previous_response_id=response.id,
        input=tool_outputs,
        tools=TOOLS,
    )

    final_ms = (
        time.perf_counter() - final_start
    ) * 1000

    total_ms = (
        time.perf_counter() - total_start
    ) * 1000

    logger.info(
        "agent_latency total_ms=%.1f routing_ms=%.1f "
        "tool_ms=%.1f final_ms=%.1f",
        total_ms,
        routing_ms,
        tool_ms,
        final_ms,
    )

    return {
        "answer": final_response.output_text,
        "sources": list(
            dict.fromkeys(sources)
        ),
    }



