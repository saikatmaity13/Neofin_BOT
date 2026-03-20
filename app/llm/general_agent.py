"""
NeoStats — General Knowledge Agent
Uses Gemini Flash + Tavily web search. Reads keys from .env.
"""
import logging
import os
from typing import Any, Dict, List

from dotenv import load_dotenv

from app.memory.manager   import memory_manager
from app.tools.web_search import web_search, format_search_for_llm

load_dotenv()
logger = logging.getLogger(__name__)


def _get_api_key() -> str:
    return os.environ.get("GEMINI_API_KEY", "")

def _get_model() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-2.0-flash-latest")


GENERAL_SYSTEM_PROMPT = """You are ARIA-General, NeoStats' versatile AI assistant.
You are knowledgeable, helpful, and concise. You have access to a web_search tool
to find current information when needed.

Guidelines:
- Search the web for current events, news, prices, recent research, or anything time-sensitive.
- For stable knowledge questions, answer directly without searching.
- Always cite your web sources (mention the URL) when using search results.
- Be conversational but precise. Use markdown for structure when helpful.
- If asked about credit underwriting, mention the Credit Underwriter tab has dedicated tools.
- NEVER refuse a calculation or risk indexing prompt (even if you lack proprietary data). If asked to calculate or assess, boldly synthesize the closest available proxy models, indices, or web data to give an authoritative estimate instead of explaining what you can't do.
"""


def run_general_agent(session_id: str, user_message: str) -> Dict[str, Any]:
    try:
        from groq import Groq
    except ImportError:
        return {
            "reply": "⚠️ groq SDK not installed. Run: pip install groq",
            "tools_used": [], "thoughts": [],
        }

    from app.config import get_settings
    settings = get_settings()
    api_key = settings.GROQ_API_KEY
    if not api_key:
        return {
            "reply": "⚠️ No GROQ_API_KEY found. Add it to your .env file.",
            "tools_used": [], "thoughts": [],
        }

    client = Groq(api_key=api_key)
    sid = f"general_{session_id}"
    memory_manager.add_message(sid, "user", user_message)

    tools_used: List[str] = []
    thoughts:   List[str] = [f"Received: {user_message[:80]}…"]
    final_reply = "I encountered an issue — please retry."

    # Define web_search as an OpenAI-format tool
    groq_tools = [{
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the internet for current information, news, or any factual query.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Concise web search query."
                    }
                },
                "required": ["query"]
            }
        }
    }]

    history = memory_manager.get_history(sid)
    groq_messages = [{"role": "system", "content": GENERAL_SYSTEM_PROMPT}]
    for m in history:
        # Avoid passing memory tool uses back to Groq if they aren't structured well
        if m["role"] in ["user", "assistant"]:
            groq_messages.append({"role": m["role"], "content": str(m["content"])})

    for iteration in range(6):
        thoughts.append(f"Iteration {iteration+1} — calling Groq…")
        try:
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=groq_messages,
                tools=groq_tools,
                tool_choice="auto",
                max_tokens=2048,
            )
        except Exception as e:
            final_reply = f"⚠️ Groq API error: {e}"
            break

        choice = response.choices[0]
        msg = choice.message

        tool_calls = []
        if msg.content:
            final_reply = msg.content

        if msg.tool_calls:
            import json
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                tool_calls.append({"id": tc.id, "name": tc.function.name, "input": args})
                thoughts.append(f"→ Searching web: \"{args.get('query','')}\"")

        if not tool_calls or choice.finish_reason == "stop":
            thoughts.append("✓ Done.")
            break

        # Append assistant message with tool calls
        assistant_msg = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            assistant_msg["tool_calls"] = [tc.model_dump() for tc in msg.tool_calls]
        groq_messages.append(assistant_msg)

        # Execute search
        for tc in tool_calls:
            try:
                results    = web_search(tc["input"].get("query", ""))
                result_str = format_search_for_llm(results)
                tools_used.append("search_web")
                thoughts.append(f"← Got {len(results)} web results.")
            except Exception as e:
                result_str = f"Search error: {e}"

            groq_messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result_str,
            })

    memory_manager.add_message(sid, "assistant", final_reply)
    return {
        "reply":      final_reply,
        "tools_used": list(dict.fromkeys(tools_used)),
        "thoughts":   thoughts,
    }