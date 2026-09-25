"""
web_search tool - free, no API key required.

Uses the DuckDuckGo search library. That package has been published under two
names over time ("duckduckgo_search" and its successor "ddgs"); we try both so
this keeps working regardless of which one is installed. Results are handed
back as short raw snippets to the AI model (never shown to the user directly)
so the model can compose one natural-language answer - see core/assistant.py.
"""


def _get_backend():
    try:
        from ddgs import DDGS
        return DDGS
    except ImportError:
        pass
    try:
        from duckduckgo_search import DDGS
        return DDGS
    except ImportError:
        return None


def execute(args: dict) -> str:
    query = (args.get("query") or "").strip()
    if not query:
        return "No search query was given."

    DDGS = _get_backend()
    if DDGS is None:
        return "Web search isn't available (search package not installed)."

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=4))
    except Exception as e:
        return f"Web search failed: {e}"

    if not results:
        return f"No web results found for '{query}'."

    lines = []
    for r in results:
        title = r.get("title", "").strip()
        body = r.get("body", "").strip()
        href = r.get("href", "").strip()
        lines.append(f"- {title}: {body} ({href})")

    return "Search results for '{}':\n{}".format(query, "\n".join(lines))


TOOLS = [
    {
        "name": "web_search",
        "description": "Search the web for current information, e.g. news, weather, latest software versions.",
        "parameters": {"query": "string - what to search for"},
        "confirm": False,
        "func": execute,
    }
]
