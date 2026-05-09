"""
ai_agent.py — OpenAI Responses API wrapper with Conversation-based context.

Uses the Responses API (replacement for the legacy Assistants API) with
Conversations for persistent multi-turn context. The AI generates analysis
code + explanations but NEVER executes code — that happens locally.

System prompts are loaded from separate markdown files in AI/prompts/.
"""

import os
import re
from openai import OpenAI


# ---------------------------------------------------------------------------
# Load prompts from markdown files
# ---------------------------------------------------------------------------
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def _load_prompt(filename: str) -> str:
    """Load a prompt markdown file from the prompts directory."""
    filepath = os.path.join(PROMPTS_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def build_system_prompt() -> str:
    """Build the full system prompt by combining all prompt files."""
    parts = [
        _load_prompt("system.md"),
        _load_prompt("schema.md"),
        _load_prompt("examples.md"),
    ]
    return "\n\n---\n\n".join(parts)


class AIAgent:
    """Wrapper around OpenAI Responses API for code generation."""

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str | None = None):
        """
        Initialize the AI agent.

        Args:
            api_key: OpenAI API key
            model: Model to use for responses (default: gpt-4o)
            base_url: Optional custom API base URL
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.system_prompt = build_system_prompt()

    def create_conversation(self) -> str:
        """Create a new conversation for persistent context. Returns conversation ID."""
        conversation = self.client.conversations.create()
        return conversation.id

    def send_message(self, conversation_id: str, message: str) -> dict:
        """
        Send a user message and get the AI response within a conversation.

        Args:
            conversation_id: The conversation ID for context persistence
            message: User's message text

        Returns:
            dict with keys:
            - explanation (str): AI's Vietnamese explanation
            - code (str|None): Python code block if generated
            - raw_response (str): Full response text
        """
        response = self.client.responses.create(
            model=self.model,
            instructions=self.system_prompt,
            input=[{"role": "user", "content": message}],
            conversation=conversation_id,
            store=True,
        )

        if response.status != "completed":
            return {
                "explanation": f"Lỗi: Response status = {response.status}",
                "code": None,
                "raw_response": "",
            }

        # Extract text from response output
        response_text = response.output_text

        if not response_text:
            return {
                "explanation": "Không nhận được phản hồi từ AI.",
                "code": None,
                "raw_response": "",
            }

        # Parse code blocks and explanation
        return self._parse_response(response_text)

    def request_fix(self, conversation_id: str, code: str, error_traceback: str) -> dict:
        """
        Send an error back to the AI in the same conversation for a fix.

        The AI has full conversation context — it knows what was requested,
        what code it generated, and now sees the error.

        Args:
            conversation_id: Same conversation ID for context continuity
            code: The code that failed
            error_traceback: Full Python traceback

        Returns:
            Same format as send_message()
        """
        fix_message = (
            f"Code vừa chạy bị lỗi. Hãy sửa lại.\n\n"
            f"**Code gặp lỗi:**\n```python\n{code}\n```\n\n"
            f"**Traceback lỗi:**\n```\n{error_traceback}\n```\n\n"
            f"Hãy giải thích nguyên nhân lỗi và đưa ra code đã sửa."
        )
        return self.send_message(conversation_id, fix_message)

    @staticmethod
    def _parse_response(response_text: str) -> dict:
        """
        Parse the AI response to extract thinking, code blocks, and explanation.

        Extracts:
        - <Suy_nghĩ>...</Suy_nghĩ> blocks as chain-of-thought thinking
        - ```python ... ``` blocks as executable code
        - Everything else as the user-facing explanation
        """
        # Extract thinking (Chain-of-Thought) from <Suy_nghĩ> tags
        thinking_pattern = r"<Suy_nghĩ>(.*?)</Suy_nghĩ>"
        thinking_matches = re.findall(thinking_pattern, response_text, re.DOTALL)
        thinking = "\n\n".join(m.strip() for m in thinking_matches) if thinking_matches else None

        # Split numbered steps (e.g. "1. … 2. … 3. …") onto separate lines
        if thinking:
            thinking = re.sub(r'(?<!\n)\s*(\d+\.\s)', r'\n\1', thinking).strip()

        # Remove thinking tags from response before further parsing
        text_without_thinking = re.sub(thinking_pattern, "", response_text, flags=re.DOTALL)

        # Find all Python code blocks
        code_pattern = r"```python\s*\n(.*?)```"
        code_matches = re.findall(code_pattern, text_without_thinking, re.DOTALL)

        # Join multiple code blocks if present
        code = "\n\n".join(code_matches).strip() if code_matches else None

        # Explanation is everything outside code blocks and thinking tags
        explanation = re.sub(code_pattern, "", text_without_thinking, flags=re.DOTALL).strip()

        return {
            "thinking": thinking,
            "explanation": explanation,
            "code": code,
            "raw_response": response_text,
        }
