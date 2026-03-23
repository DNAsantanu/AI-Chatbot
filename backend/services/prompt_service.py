"""
Prompt Service — Manages chat prompt templates.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# System prompt defining the assistant's persona and behavior
SYSTEM_PROMPT = """You are an intelligent, helpful AI assistant. Your capabilities include:

1. **Conversational Memory**: You remember the context of our conversation and can reference previous messages.
2. **Web-Enhanced Knowledge**: When web search results are provided, you incorporate them into your answers with proper attribution.
3. **Clear Communication**: You provide well-structured, accurate, and helpful responses.

Guidelines:
- Be concise but thorough. Use markdown formatting for readability.
- If web search context is provided below, use it to give up-to-date information and cite sources.
- If you don't know something and no search context is available, say so honestly.
- Maintain a friendly, professional tone.

{web_context}"""


def create_chat_prompt() -> ChatPromptTemplate:
    """
    Create the main chat prompt template with:
    - System message (with optional web context injection)
    - Conversation history placeholder
    - Human message placeholder

    Returns:
        A ChatPromptTemplate ready for use in an LCEL chain.
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])
    return prompt


def format_web_context(search_results: list[dict] | None) -> str:
    """
    Format Tavily search results into a context string for the system prompt.

    Args:
        search_results: List of search result dicts with 'url' and 'content' keys.

    Returns:
        Formatted context string, or empty string if no results.
    """
    if not search_results:
        return ""

    context_parts = ["\n--- Web Search Results ---"]
    for i, result in enumerate(search_results, 1):
        url = result.get("url", "")
        content = result.get("content", "")
        context_parts.append(f"\n[{i}] {url}\n{content}")
    context_parts.append("\n--- End of Search Results ---")

    return "\n".join(context_parts)
