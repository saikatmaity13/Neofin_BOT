"""
NeoStats Agentic Credit Underwriter — Core Agent Loop
======================================================
Architecture:
  1. Build messages = system prompt + session history + user message
  2. Call LLM (Anthropic Claude / Gemini / Ollama) with tool definitions
  3. If model calls a tool → execute it → inject result → repeat (max N times)
  4. On plain-text reply → extract credit memo if present → return result
  5. Persist exchange to memory

The agent "thinks step by step":
  - First calls check_credit_history
  - If credit score is weak, proactively calls research_market_trends to see
    if there is a compelling sector-level reason to reconsider
  - Always calls regulatory_compliance_check
  - Finally calls score_risk_matrix for the quantitative recommendation
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.config import get_settings
from app.memory.manager import memory_manager
from app.llm.tool_definitions import get_anthropic_tools
from app.llm.system_prompt import SYSTEM_PROMPT
from app.tools.credit_history import check_credit_history, format_profile_for_llm
from app.tools.market_trends import research_market_trends, format_market_research_for_llm
from app.tools.compliance import (
    regulatory_compliance_check, format_compliance_for_llm,
    score_risk_matrix, format_risk_matrix_for_llm,
)

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Tool Dispatcher ───────────────────────────────────────────────────────────

def _dispatch_tool(tool_name: str, tool_input: Dict[str, Any]) -> Tuple[str, Optional[Dict]]:
    """
    Execute a named tool and return (formatted_string, raw_dict).
    The formatted string goes back to the LLM; raw_dict is used for credit memo extraction.
    """
    if tool_name == "check_credit_history":
        result = check_credit_history(
            applicant_id=tool_input.get("applicant_id", "UNKNOWN"),
            include_full_profile=tool_input.get("include_full_profile", True),
        )
        return format_profile_for_llm(result), result

    elif tool_name == "research_market_trends":
        result = research_market_trends(
            query=tool_input.get("query", ""),
            sector=tool_input.get("sector", ""),
        )
        return format_market_research_for_llm(result), result

    elif tool_name == "regulatory_compliance_check":
        result = regulatory_compliance_check(
            applicant_id=tool_input.get("applicant_id", "UNKNOWN"),
            loan_amount=float(tool_input.get("loan_amount", 0)),
            loan_purpose=tool_input.get("loan_purpose", "General"),
        )
        return format_compliance_for_llm(result), result

    elif tool_name == "score_risk_matrix":
        result = score_risk_matrix(
            applicant_id=tool_input.get("applicant_id", "UNKNOWN"),
            sector_risk_level=tool_input.get("sector_risk_level", "medium"),
        )
        return format_risk_matrix_for_llm(result), result

    else:
        return f"Unknown tool: {tool_name}", None


# ── LLM Clients ───────────────────────────────────────────────────────────────

def _call_anthropic(messages: List[Dict], thoughts: List[str]) -> Tuple[str, List[Dict], bool]:
    """
    Call Anthropic Claude. Returns (stop_reason, tool_calls_list, is_done).
    Mutates `messages` in place by appending assistant response.
    """
    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # Separate system from messages
    system_content = SYSTEM_PROMPT
    user_messages = [m for m in messages if m["role"] != "system"]

    response = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=2048,
        system=system_content,
        tools=get_anthropic_tools(),
        messages=user_messages,
    )

    tool_calls = []
    text_parts = []

    for block in response.content:
        if block.type == "tool_use":
            tool_calls.append({
                "id": block.id,
                "name": block.name,
                "input": block.input,
            })
            thoughts.append(f"Calling tool: {block.name}({json.dumps(block.input, indent=None)[:120]}...)")
        elif block.type == "text":
            text_parts.append(block.text)

    is_done = response.stop_reason == "end_turn" or not tool_calls
    text_content = "\n".join(text_parts)

    # Build assistant message for history
    content_list = []
    if text_content:
        content_list.append({"type": "text", "text": text_content})
    for tc in tool_calls:
        content_list.append({
            "type": "tool_use",
            "id": tc["id"],
            "name": tc["name"],
            "input": tc["input"],
        })

    messages.append({"role": "assistant", "content": content_list or text_content})

    return text_content, tool_calls, is_done


def _inject_tool_results(messages: List[Dict], tool_calls: List[Dict],
                         tool_results: List[Tuple[str, str]]) -> None:
    """Append tool results to messages in Anthropic format."""
    tool_result_content = []
    for tc, (result_str, _) in zip(tool_calls, tool_results):
        tool_result_content.append({
            "type": "tool_result",
            "tool_use_id": tc["id"],
            "content": result_str,
        })
    messages.append({"role": "user", "content": tool_result_content})


def _call_gemini(
    messages: List[Dict],
    thoughts: List[str],
    tool_data_out: Optional[Dict] = None,
) -> Tuple[str, List[Dict], bool]:
    """
    Call Google Gemini with native function/tool calling.
    Returns same signature as _call_anthropic: (text, tool_calls, is_done).
    tool_data_out: if provided, filled in-place with credit tool results.
    """
    try:
        import google.generativeai as genai
        from google.generativeai import protos
        genai.configure(api_key=settings.GEMINI_API_KEY)
    except ImportError:
        return "google-generativeai not installed. Run: pip install google-generativeai", [], True

    # ── Build Gemini tool declarations ───────────────────────────────────────
    def _schema(props_dict: dict, required: list) -> protos.Schema:
        """Convert a simple props dict to a Gemini Schema."""
        gprops = {}
        for k, v in props_dict.items():
            t = v.get("type", "string")
            if t in ("number", "integer"):
                gtype = protos.Type.NUMBER
            elif t == "boolean":
                gtype = protos.Type.BOOLEAN
            else:
                gtype = protos.Type.STRING
            gprops[k] = protos.Schema(type=gtype, description=v.get("description", ""))
        return protos.Schema(type=protos.Type.OBJECT, properties=gprops, required=required)

    gemini_tools = [protos.Tool(function_declarations=[
        protos.FunctionDeclaration(
            name="check_credit_history",
            description="Queries credit_risk dataset for an applicant's full financial profile. ALWAYS call first.",
            parameters=_schema(
                {"applicant_id": {"type": "string", "description": "Unique applicant ID e.g. 'A001'"},
                 "include_full_profile": {"type": "boolean", "description": "Return all fields. Default true."}},
                required=["applicant_id"],
            ),
        ),
        protos.FunctionDeclaration(
            name="research_market_trends",
            description="RAG over financial data to assess sector risk and market conditions.",
            parameters=_schema(
                {"query": {"type": "string", "description": "Natural language query about market conditions."},
                 "sector": {"type": "string", "description": "Industry sector e.g. 'retail'."}},
                required=["query"],
            ),
        ),
        protos.FunctionDeclaration(
            name="regulatory_compliance_check",
            description="Checks if loan meets 40% LTI and other NeoStats compliance rules. ALWAYS run before final answer.",
            parameters=_schema(
                {"applicant_id": {"type": "string", "description": "Applicant ID."},
                 "loan_amount":   {"type": "number", "description": "Loan amount in INR."},
                 "loan_purpose":  {"type": "string", "description": "Purpose of the loan."}},
                required=["applicant_id", "loan_amount"],
            ),
        ),
        protos.FunctionDeclaration(
            name="score_risk_matrix",
            description="Computes composite risk score 0-100. Call after credit history and market trends.",
            parameters=_schema(
                {"applicant_id":       {"type": "string", "description": "Applicant to score."},
                 "sector_risk_level":  {"type": "string", "description": "Risk level: low/medium/high/critical."}},
                required=["applicant_id", "sector_risk_level"],
            ),
        ),
    ])]

    # ── Convert conversation history to Gemini format ─────────────────────────
    gemini_history = []
    for m in messages:
        if m["role"] == "system":
            continue  # handled via system_instruction below
        role    = "user" if m["role"] == "user" else "model"
        content = m["content"] if isinstance(m["content"], str) else json.dumps(m["content"])
        gemini_history.append({"role": role, "parts": [content]})

    # Use a safe, known-good model name
    safe_model = settings.GEMINI_MODEL
    if safe_model in ("gemini-flash-latest", "gemini-pro-latest", "gemini-1.5-flash", ""):
        safe_model = "gemini-2.0-flash"

    model = genai.GenerativeModel(
        model_name=safe_model,
        system_instruction=SYSTEM_PROMPT,
        tools=gemini_tools,
    )

    # ── Agentic inner loop: Gemini may request multiple tool calls ───────────
    # We handle up to 4 rounds of function calling within a single _call_gemini
    # invocation so that all tools fire and the outer loop sees is_done=True
    # with a rich text reply.
    chat = model.start_chat(history=gemini_history[:-1] if gemini_history else [])
    last_user_msg = gemini_history[-1]["parts"][0] if gemini_history else "Proceed."

    all_tool_calls: List[Dict] = []
    final_text = ""

    for _inner in range(5):
        try:
            response = chat.send_message(last_user_msg if _inner == 0 else "Continue with analysis.")
        except Exception as e:
            final_text = f"⚠️ Gemini API error: {e}"
            break

        # Parse response parts
        tool_reqs: List[Dict] = []
        text_parts: List[str] = []

        for cand in (response.candidates or []):
            for part in (cand.content.parts if hasattr(cand.content, "parts") else []):
                if hasattr(part, "function_call") and part.function_call.name:
                    fc = part.function_call
                    tool_reqs.append({
                        "id":    f"call_{fc.name}_{_inner}",
                        "name":  fc.name,
                        "input": dict(fc.args),
                    })
                    thoughts.append(f"→ Gemini calling tool: {fc.name}({json.dumps(dict(fc.args))[:100]})")
                elif hasattr(part, "text") and part.text:
                    text_parts.append(part.text)

        final_text = "\n".join(text_parts) if text_parts else final_text

        if not tool_reqs:
            # No more tool calls — Gemini is done
            break

        # Execute each requested tool and send results back
        fn_responses = []
        for tr in tool_reqs:
            try:
                result_str, result_dict = _dispatch_tool(tr["name"], tr["input"])
                thoughts.append(f"← Tool '{tr['name']}' returned {len(result_str)} chars.")
                # Fill caller's memo dict if provided
                if tool_data_out is not None and result_dict:
                    if tr["name"] == "check_credit_history":
                        tool_data_out["credit_profile"] = result_dict
                    elif tr["name"] == "research_market_trends":
                        tool_data_out["market_trends"] = result_dict
                    elif tr["name"] == "regulatory_compliance_check":
                        tool_data_out["compliance"] = result_dict
                    elif tr["name"] == "score_risk_matrix":
                        tool_data_out["risk_matrix"] = result_dict
            except Exception as e:
                result_str = f"Tool error: {e}"
                result_dict = None
            fn_responses.append(
                protos.Part(function_response=protos.FunctionResponse(
                    name=tr["name"],
                    response={"result": result_str},
                ))
            )
            all_tool_calls.append(tr)

        try:
            response = chat.send_message(fn_responses)
            # Collect any text from the follow-up
            for cand in (response.candidates or []):
                for part in (cand.content.parts if hasattr(cand.content, "parts") else []):
                    if hasattr(part, "text") and part.text:
                        final_text = part.text
        except Exception as e:
            thoughts.append(f"⚠️ Tool result send error: {e}")
            break

    if not final_text:
        final_text = "Analysis complete — see credit memo panel for structured results."

    messages.append({"role": "assistant", "content": final_text})
    thoughts.append(f"✓ Gemini complete. Tools used: {[t['name'] for t in all_tool_calls]}")
    # Return with is_done=True so the outer loop stops and builds the memo
    return final_text, all_tool_calls, True


def _call_groq(
    messages: List[Dict],
    thoughts: List[str],
    tool_data_out: Optional[Dict] = None,
) -> Tuple[str, List[Dict], bool]:
    """
    Call Groq (Llama-3.3-70b) using OpenAI-compatible API with tool calling.
    """
    try:
        from groq import Groq
    except ImportError:
        return "groq not installed. Run: pip install groq", [], True

    client = Groq(api_key=settings.GROQ_API_KEY)

    # Build Groq-compatible tool definitions (OpenAI format)
    groq_tools = [
        {
            "type": "function",
            "function": {
                "name": "check_credit_history",
                "description": "Queries credit_risk dataset for an applicant's full financial profile. ALWAYS call first.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "applicant_id": {"type": "string", "description": "Unique applicant ID"},
                        "include_full_profile": {"type": "boolean", "description": "Return all fields. Default true."},
                    },
                    "required": ["applicant_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "research_market_trends",
                "description": "RAG over financial data to assess sector risk and market conditions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Natural language query about market conditions."},
                        "sector": {"type": "string", "description": "Industry sector e.g. 'retail'."},
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "regulatory_compliance_check",
                "description": "Checks if loan meets 40% LTI and other NeoStats compliance rules. ALWAYS run before final answer.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "applicant_id": {"type": "string"},
                        "loan_amount": {"type": "number", "description": "Loan amount in INR."},
                        "loan_purpose": {"type": "string"},
                    },
                    "required": ["applicant_id", "loan_amount"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "score_risk_matrix",
                "description": "Computes composite risk score 0-100. Call after credit history and market trends.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "applicant_id": {"type": "string"},
                        "sector_risk_level": {"type": "string", "description": "low/medium/high/critical"},
                    },
                    "required": ["applicant_id", "sector_risk_level"],
                },
            },
        },
    ]

    # Normalize messages for OpenAI-compatible format
    groq_messages = []
    for m in messages:
        role = m["role"]
        content = m["content"]
        if isinstance(content, list):
            # Flatten Anthropic-style content blocks to plain text
            text_parts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
            content = " ".join(text_parts)
        if role == "system":
            groq_messages.append({"role": "system", "content": content})
        elif role in ("user", "assistant"):
            groq_messages.append({"role": role, "content": str(content)})

    all_tool_calls: List[Dict] = []
    final_text = ""

    for _inner in range(5):
        try:
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=groq_messages,
                tools=groq_tools,
                tool_choice="auto",
                max_tokens=2048,
            )
        except Exception as e:
            final_text = f"⚠️ Groq API error: {e}"
            thoughts.append(f"Groq error at iteration {_inner}: {e}")
            break

        choice = response.choices[0]
        msg = choice.message

        # Collect text
        if msg.content:
            final_text = msg.content

        # Collect tool calls
        tool_reqs = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                tool_reqs.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "input": args,
                })
                thoughts.append(f"→ Groq calling tool: {tc.function.name}({tc.function.arguments[:100]})")

        if not tool_reqs or choice.finish_reason == "stop":
            break

        # Add assistant message with tool_calls to history
        assistant_msg = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            assistant_msg["tool_calls"] = [tc.model_dump() for tc in msg.tool_calls]
        groq_messages.append(assistant_msg)

        # Execute tools and inject results
        for tr in tool_reqs:
            try:
                result_str, result_dict = _dispatch_tool(tr["name"], tr["input"])
                thoughts.append(f"← Tool '{tr['name']}' returned {len(result_str)} chars.")
                if tool_data_out is not None and result_dict:
                    if tr["name"] == "check_credit_history":
                        tool_data_out["credit_profile"] = result_dict
                    elif tr["name"] == "research_market_trends":
                        tool_data_out["market_trends"] = result_dict
                    elif tr["name"] == "regulatory_compliance_check":
                        tool_data_out["compliance"] = result_dict
                    elif tr["name"] == "score_risk_matrix":
                        tool_data_out["risk_matrix"] = result_dict
            except Exception as e:
                result_str = f"Tool error: {e}"
            groq_messages.append({
                "role": "tool",
                "tool_call_id": tr["id"],
                "content": result_str,
            })
            all_tool_calls.append(tr)

    if not final_text:
        final_text = "Analysis complete — see credit memo panel for structured results."

    messages.append({"role": "assistant", "content": final_text})
    thoughts.append(f"✓ Groq complete. Tools used: {[t['name'] for t in all_tool_calls]}")
    return final_text, all_tool_calls, True
def _call_ollama(messages: List[Dict], thoughts: List[str]) -> Tuple[str, List[Dict], bool]:
    """Call local Ollama. Returns same signature."""
    try:
        import httpx
    except ImportError:
        return "httpx not installed. Run: pip install httpx", [], True

    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": [
            {"role": m["role"], "content": m["content"] if isinstance(m["content"], str) else json.dumps(m["content"])}
            for m in messages
        ],
        "stream": False,
    }
    with httpx.Client(timeout=60) as client:
        resp = client.post(f"{settings.OLLAMA_BASE_URL}/api/chat", json=payload)
        resp.raise_for_status()
        data = resp.json()

    text = data.get("message", {}).get("content", "No response from Ollama.")
    messages.append({"role": "assistant", "content": text})
    thoughts.append(f"Used Ollama ({settings.OLLAMA_MODEL}) — single-shot response")
    return text, [], True


# ── Credit Memo Extraction ────────────────────────────────────────────────────

def _extract_credit_memo(
    final_reply: str,
    tool_data: Dict[str, Any],
    applicant_id: str,
    loan_amount: float,
    loan_purpose: str,
    industry: str,
) -> Optional[Dict]:
    """
    Attempt to build a structured credit memo from tool data and LLM reply.
    """
    credit_profile = tool_data.get("credit_profile", {})
    compliance_data = tool_data.get("compliance", {})
    risk_data = tool_data.get("risk_matrix", {})
    market_data = tool_data.get("market_trends", {})

    if not credit_profile and not compliance_data and not risk_data:
        return None  # Not enough data to build a memo

    # Determine decision
    decision = "MANUAL_REVIEW"
    reply_upper = final_reply.upper()
    if "APPROVE" in reply_upper and "REJECT" not in reply_upper:
        decision = "APPROVED"
    elif "REJECT" in reply_upper:
        decision = "REJECTED"
    elif risk_data.get("recommendation"):
        rec = risk_data["recommendation"].upper()
        if "APPROVE" in rec:
            decision = "APPROVED"
        elif "REJECT" in rec:
            decision = "REJECTED"
        elif compliance_data.get("compliance_status") == "NON_COMPLIANT":
            decision = "REJECTED"

    annual_income = credit_profile.get("annual_income", compliance_data.get("annual_income", "N/A"))
    existing_debt = credit_profile.get("existing_debt", 0)
    if annual_income and isinstance(annual_income, (int, float)) and annual_income > 0:
        dti = f"{existing_debt / annual_income:.1%}"
    else:
        dti = "N/A"

    return {
        "applicant_id": applicant_id,
        "loan_amount": f"₹{float(loan_amount):,.0f}" if loan_amount else "N/A",
        "annual_income": f"₹{float(annual_income):,.0f}" if isinstance(annual_income, (int, float)) else str(annual_income),
        "loan_purpose": loan_purpose,
        "industry": industry,
        "credit_score": credit_profile.get("credit_score", risk_data.get("inputs", {}).get("credit_score", "N/A")),
        "risk_level": risk_data.get("risk_rating", market_data.get("risk_level", "N/A")),
        "debt_to_income": dti,
        "defaults": credit_profile.get("previous_defaults", "N/A"),
        "compliance": compliance_data.get("compliance_status", "N/A"),
        "market_risk": market_data.get("risk_level", "N/A"),
        "decision": decision,
        "rationale": _extract_rationale(final_reply),
    }


def _extract_rationale(text: str) -> str:
    """Pull out the most relevant summary sentences from the LLM reply."""
    # Try to find a rationale/recommendation block
    for keyword in ["rationale:", "recommendation:", "in conclusion", "final assessment", "decision:"]:
        idx = text.lower().find(keyword)
        if idx != -1:
            snippet = text[idx:idx + 600].strip()
            return snippet[:500] + ("..." if len(snippet) > 500 else "")
    # Fallback: last 400 chars of reply
    return text[-400:].strip()


def _parse_applicant_context(user_message: str) -> Dict[str, str]:
    """Extract applicant context injected by the Streamlit UI."""
    ctx = {}
    match = re.search(r"\[APPLICANT CONTEXT:(.*?)\]", user_message, re.DOTALL)
    if match:
        raw = match.group(1)
        for part in raw.split(","):
            if "=" in part:
                k, v = part.strip().split("=", 1)
                ctx[k.strip()] = v.strip()
    return ctx


# ── Main Agent Entry Point ────────────────────────────────────────────────────

async def run_agent(
    session_id: str,
    user_message: str,
    max_iterations: int = None,
) -> Dict[str, Any]:
    """
    Full agentic loop. Returns:
        reply       - final assistant text
        tools_used  - list of tool names called
        thoughts    - step-by-step reasoning log (for the UI expander)
        credit_memo - structured dict for the memo panel (or None)
    """
    if max_iterations is None:
        max_iterations = settings.MAX_ITERATIONS

    # Parse embedded applicant context from UI
    ctx = _parse_applicant_context(user_message)
    applicant_id = ctx.get("ID", "UNKNOWN")
    loan_amount_str = ctx.get("LoanAmount", "0").replace("₹", "").replace(",", "")
    try:
        loan_amount = float(loan_amount_str)
    except ValueError:
        loan_amount = 0.0
    loan_purpose = ctx.get("Purpose", "General")
    industry = ctx.get("Industry", "General")

    # Persist user message to memory
    memory_manager.add_message(session_id, "user", user_message)

    # Build initial messages list
    messages: List[Dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *memory_manager.get_history(session_id),
    ]

    tools_used: List[str] = []
    thoughts: List[str] = [
        f"Received request for applicant {applicant_id}, "
        f"loan ₹{loan_amount:,.0f}, purpose: {loan_purpose}, sector: {industry}"
    ]
    tool_data_accumulated: Dict[str, Any] = {}
    final_reply = "I encountered an issue processing this request."

    # Select LLM caller — for Gemini we use a wrapper that passes tool_data_accumulated
    if settings.LLM_PROVIDER == "gemini":
        import functools
        _call_llm = functools.partial(_call_gemini, tool_data_out=tool_data_accumulated)
    elif settings.LLM_PROVIDER == "groq":
        import functools
        _call_llm = functools.partial(_call_groq, tool_data_out=tool_data_accumulated)
    elif settings.LLM_PROVIDER == "ollama":
        _call_llm = _call_ollama
    else:
        _call_llm = _call_anthropic

    # ── Agentic Loop ──────────────────────────────────────────────────────────
    for iteration in range(max_iterations):
        thoughts.append(f"Iteration {iteration + 1}/{max_iterations} — calling LLM...")

        try:
            text_content, tool_calls, is_done = _call_llm(messages, thoughts)
        except Exception as e:
            logger.error(f"[Agent] LLM error: {e}")
            final_reply = f"⚠️ LLM error: {str(e)}"
            break

        if is_done or not tool_calls:
            final_reply = text_content or final_reply
            thoughts.append("Agent reached final answer.")
            # For Gemini: tools were dispatched internally — record names used
            for tc in tool_calls:
                if tc["name"] not in tools_used:
                    tools_used.append(tc["name"])
            break

        # Execute all tool calls
        tool_results: List[Tuple[str, Optional[Dict]]] = []
        for tc in tool_calls:
            name = tc["name"]
            inp = tc["input"]
            thoughts.append(f"→ Executing '{name}' with args: {json.dumps(inp)[:100]}")
            try:
                result_str, result_dict = _dispatch_tool(name, inp)
                tools_used.append(name)
                tool_results.append((result_str, result_dict))

                # Accumulate structured data for memo building
                if name == "check_credit_history" and result_dict:
                    tool_data_accumulated["credit_profile"] = result_dict
                elif name == "research_market_trends" and result_dict:
                    tool_data_accumulated["market_trends"] = result_dict
                elif name == "regulatory_compliance_check" and result_dict:
                    tool_data_accumulated["compliance"] = result_dict
                elif name == "score_risk_matrix" and result_dict:
                    tool_data_accumulated["risk_matrix"] = result_dict

                thoughts.append(f"← '{name}' returned {len(result_str)} chars of data.")
            except Exception as e:
                logger.error(f"[Agent] Tool '{name}' error: {e}")
                tool_results.append((f"Error in {name}: {str(e)}", None))
                thoughts.append(f"⚠️ Tool '{name}' failed: {str(e)}")

        # Inject tool results back into conversation
        if settings.LLM_PROVIDER == "anthropic":
            _inject_tool_results(messages, tool_calls, tool_results)
        else:
            # For Gemini/Ollama (no native tool calling), inject as user message
            summary = "\n\n".join(r for r, _ in tool_results)
            messages.append({"role": "user", "content": f"Tool Results:\n{summary}\n\nNow provide your analysis."})

    else:
        thoughts.append("⚠️ Max iterations reached.")
        final_reply = text_content if text_content else final_reply  # noqa: F821

    # Build credit memo if we have enough data
    credit_memo = None
    if tool_data_accumulated:
        credit_memo = _extract_credit_memo(
            final_reply=final_reply,
            tool_data=tool_data_accumulated,
            applicant_id=applicant_id,
            loan_amount=loan_amount,
            loan_purpose=loan_purpose,
            industry=industry,
        )

    # Persist final assistant reply to memory
    memory_manager.add_message(session_id, "assistant", final_reply)

    return {
        "reply": final_reply,
        "tools_used": list(dict.fromkeys(tools_used)),  # deduplicated, order-preserving
        "thoughts": thoughts,
        "credit_memo": credit_memo,
    }
