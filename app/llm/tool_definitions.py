"""
Tool definitions passed to the LLM's tool/function-calling API.
Mirrors the OpenAI tool format; we translate for Gemini/Ollama as needed.
"""

TOOL_DEFINITIONS = [
    {
        "name": "check_credit_history",
        "description": (
            "Queries the credit_risk.csv dataset for a specific applicant's financial profile. "
            "Returns income, existing debt, credit score, loan history, number of previous defaults, "
            "and employment status. ALWAYS call this first when evaluating any loan application."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "applicant_id": {
                    "type": "string",
                    "description": "The unique applicant ID to look up (e.g., 'A001').",
                },
                "include_full_profile": {
                    "type": "boolean",
                    "description": "If true, return all available fields. Default: true.",
                    "default": True,
                },
            },
            "required": ["applicant_id"],
        },
    },
    {
        "name": "research_market_trends",
        "description": (
            "Uses RAG (Retrieval-Augmented Generation) over the Sujet Financial Dataset to research "
            "industry-specific economic conditions, sector volatility, and market risks. "
            "Use this when you need to understand whether the applicant's industry/sector has "
            "elevated risk factors that should influence the lending decision. "
            "Example queries: 'Is the retail sector volatile?', 'What are the credit risks in agriculture?'"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query about market/sector conditions.",
                },
                "sector": {
                    "type": "string",
                    "description": "The industry sector to focus on (e.g., 'retail', 'manufacturing').",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "regulatory_compliance_check",
        "description": (
            "Verifies if a loan application meets NeoStats regulatory compliance rules. "
            "Key rule: loan amount must NOT exceed 40% of the applicant's verified annual income. "
            "Additional checks: applicant must have income above poverty line, no active bankruptcies. "
            "ALWAYS run this before issuing any final recommendation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "applicant_id": {
                    "type": "string",
                    "description": "Applicant ID to fetch income data for compliance check.",
                },
                "loan_amount": {
                    "type": "number",
                    "description": "Requested loan amount in INR (₹).",
                },
                "loan_purpose": {
                    "type": "string",
                    "description": "Purpose of the loan (e.g., 'Home Purchase', 'Business Expansion').",
                },
            },
            "required": ["applicant_id", "loan_amount"],
        },
    },
    {
        "name": "score_risk_matrix",
        "description": (
            "Computes a composite risk score (0-100) using a weighted matrix of: "
            "credit score (30%), debt-to-income ratio (25%), previous defaults (20%), "
            "employment stability (15%), and market/sector risk (10%). "
            "Returns a structured risk assessment with sub-scores and an overall rating "
            "(LOW / MEDIUM / HIGH / CRITICAL). Call this after gathering credit history "
            "and market trends to produce a final quantitative risk score."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "applicant_id": {
                    "type": "string",
                    "description": "The applicant to score.",
                },
                "sector_risk_level": {
                    "type": "string",
                    "description": "Risk level from market research: 'low', 'medium', 'high', 'critical'.",
                    "enum": ["low", "medium", "high", "critical"],
                },
            },
            "required": ["applicant_id", "sector_risk_level"],
        },
    },
]


def get_anthropic_tools() -> list:
    """Returns tools in Anthropic Claude format."""
    return [{"name": t["name"], "description": t["description"], "input_schema": t["input_schema"]}
            for t in TOOL_DEFINITIONS]


def get_openai_tools() -> list:
    """Returns tools in OpenAI function-calling format."""
    tools = []
    for t in TOOL_DEFINITIONS:
        tools.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["input_schema"],
            }
        })
    return tools
def get_gemini_tools() -> list:
    """Returns tools in Google Gemini FunctionDeclaration format."""
    import google.generativeai as genai
    declarations = []
    for t in TOOL_DEFINITIONS:
        # Convert JSON schema to Gemini Schema
        schema = t["input_schema"]
        # Basic mapping of the schema for Gemini
        props = {}
        for k, v in schema.get("properties", {}).items():
            props[k] = genai.protos.Schema(
                type=genai.protos.Type.STRING if v.get("type") == "string" else \
                     genai.protos.Type.NUMBER if v.get("type") in ("number", "integer") else \
                     genai.protos.Type.BOOLEAN if v.get("type") == "boolean" else \
                     genai.protos.Type.STRING,
                description=v.get("description", ""),
            )
        
        declarations.append(
            genai.protos.FunctionDeclaration(
                name=t["name"],
                description=t["description"],
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties=props,
                    required=schema.get("required", []),
                ),
            )
        )
    return [genai.protos.Tool(function_declarations=declarations)]
