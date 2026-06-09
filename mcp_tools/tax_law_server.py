"""Minimal MCP-style tax law tool server.

This server is intentionally tiny for the lab. It speaks line-delimited
JSON-RPC methods that mirror MCP tool discovery and invocation:

- initialize
- tools/list
- tools/call

Tax Agent uses it as an external capability instead of keeping every tax-law
lookup inside the agent process.
"""

from __future__ import annotations

import json
import sys
from typing import Any


TAX_KNOWLEDGE = [
    {
        "id": "tax_evasion",
        "keywords": ["tax", "evasion", "fraud", "irs", "7201"],
        "text": (
            "Tax evasion under 26 U.S.C. Section 7201 is a felony. Penalties can include "
            "up to 5 years imprisonment, criminal fines, back taxes, interest, and a "
            "75% civil fraud penalty under IRC Section 6663."
        ),
    },
    {
        "id": "accuracy_penalty",
        "keywords": ["accuracy", "underpayment", "6662", "penalty"],
        "text": (
            "IRC Section 6662 can impose a 20% accuracy-related penalty for negligence, "
            "substantial understatement, or valuation misstatements."
        ),
    },
    {
        "id": "fbar_fatca",
        "keywords": ["fbar", "fatca", "foreign", "offshore", "fincen"],
        "text": (
            "FBAR/FATCA issues can trigger FinCEN and IRS enforcement. Willful FBAR "
            "violations may lead to penalties up to the greater of $100,000 or 50% "
            "of the account balance per violation."
        ),
    },
    {
        "id": "responsible_person",
        "keywords": ["responsible", "officer", "payroll", "trust", "6672"],
        "text": (
            "IRC Section 6672 allows the IRS to assess the Trust Fund Recovery Penalty "
            "against responsible persons who willfully fail to collect, account for, "
            "or pay payroll taxes."
        ),
    },
]


def search_tax_code(query: str) -> str:
    """Search a tiny external tax-law knowledge base."""
    query_lower = query.lower()
    results = []
    for entry in TAX_KNOWLEDGE:
        score = sum(1 for keyword in entry["keywords"] if keyword in query_lower)
        if score:
            results.append((score, entry))
    results.sort(key=lambda item: item[0], reverse=True)
    if not results:
        return "No external MCP tax-law matches found."
    return "\n\n".join(f"[{entry['id']}] {entry['text']}" for _, entry in results[:3])


def handle_request(request: dict[str, Any]) -> dict[str, Any]:
    """Handle one JSON-RPC request."""
    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params") or {}

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "tax-law-mcp-server", "version": "1.0.0"},
                "capabilities": {"tools": {}},
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": "search_tax_code",
                        "description": "Search external tax law references for statutes and penalties.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Tax law search query.",
                                }
                            },
                            "required": ["query"],
                        },
                    }
                ]
            }
        elif method == "tools/call":
            name = params.get("name")
            arguments = params.get("arguments") or {}
            if name != "search_tax_code":
                raise ValueError(f"Unknown tool: {name}")
            text = search_tax_code(str(arguments.get("query", "")))
            result = {"content": [{"type": "text", "text": text}]}
        else:
            raise ValueError(f"Unknown method: {method}")
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except Exception as exc:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32000, "message": str(exc)},
        }


def main() -> None:
    """Run the stdio JSON-RPC loop."""
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        response = handle_request(json.loads(line))
        sys.stdout.write(json.dumps(response, ensure_ascii=True) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
