"""
ai_agent.py — OpenAI Responses API wrapper with Conversation-based context.

Uses the Responses API (replacement for the legacy Assistants API) with
Conversations for persistent multi-turn context. The AI generates analysis
code + explanations but NEVER executes code — that happens locally.
"""

import re
from openai import OpenAI


# Vietnamese system prompt — sent inline with each response request
SYSTEM_PROMPT = """Bạn là một trợ lý phân tích dữ liệu chuyên nghiệp. Bạn làm việc với bộ dữ liệu tuyển dụng từ CareerViet gồm ~23,500 tin tuyển dụng thuộc 69 ngành nghề.

## Dữ liệu có sẵn
Khi code được thực thi, các biến sau đã được nạp sẵn:
- `df`: DataFrame chính từ file `careerviet_all_jobs.csv` (23,536 dòng, 40 cột)
  Các cột quan trọng: job_id, job_title, emp_id, emp_name, job_salary_unit, job_active_date, job_contact_hide, location_name_en, location_name, job_is_urgent_job, job_competition, top_industries, emp_logo, job_check_profile, job_eoc, job_last_date, date_view, job_experience, job_to_experience, benefit_id, benefit_icon, benefit_name_en, benefit_name_vn, jobEoc, url_emp_default, prize_name, job_class_css_item, job_link, job_salary_string, job_new, job_title_red, job_premium_icon_item, has_save_job, premium_industries, district_id, industries, url_logo_emp_eoc, emp_eoc_active, job_from_salary, job_to_salary
  Kiểu dữ liệu đáng chú ý: job_experience (float), job_to_experience (float), job_from_salary (float), job_to_salary (float), industries và top_industries là JSON string.
- `df_industries`: DataFrame ngành nghề từ file `careerviet_industries.csv` (69 dòng)
  Các cột: industry_id, industry_name_en, industry_name_vn

## Thư viện có sẵn
pandas (pd), numpy (np), matplotlib (plt), seaborn (sns), plotly.express (px), plotly.graph_objects (go), json

## Quy tắc bắt buộc
1. LUÔN trả về code Python trong block ```python ... ``` khi người dùng yêu cầu phân tích.
2. LUÔN giải thích bằng tiếng Việt trước mỗi đoạn code: code này làm gì, xử lý bao nhiêu dòng, dùng hàm gì.
3. KHÔNG BAO GIỜ tự ý thực thi code — chỉ hiển thị để người dùng duyệt.
4. KHÔNG thêm dữ liệu ngoài — chỉ dùng df và df_industries đã có sẵn.
5. Khi tạo biểu đồ, dùng tiếng Việt cho tiêu đề và nhãn trục.
6. Nếu người dùng không biết phân tích gì, hãy GỢI Ý các phương pháp phân tích phù hợp để họ chọn.
7. Khi sửa lỗi: giải thích nguyên nhân lỗi trước, sau đó đưa ra code đã sửa.
8. Biến kết quả DataFrame nên đặt tên là `result` hoặc `result_df` để hệ thống tự hiển thị.
9. Với matplotlib, luôn gọi plt.tight_layout() trước khi kết thúc.
10. Dữ liệu cột `industries` và `top_industries` là JSON string, cần parse bằng json.loads() nếu muốn phân tích chi tiết ngành."""


class AIAgent:
    """Wrapper around OpenAI Responses API for code generation."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize the AI agent.

        Args:
            api_key: OpenAI API key
            model: Model to use for responses (default: gpt-4o-mini)
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

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
            instructions=SYSTEM_PROMPT,
            input=[{"role": "user", "content": message}],
            conversation=conversation_id,
            store=True,
        )

        if response.status != "completed":
            return {
                "explanation": f"❌ Lỗi: Response status = {response.status}",
                "code": None,
                "raw_response": "",
            }

        # Extract text from response output
        response_text = response.output_text

        if not response_text:
            return {
                "explanation": "❌ Không nhận được phản hồi từ AI.",
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
        Parse the AI response to extract code blocks and explanation.

        Looks for ```python ... ``` blocks. Everything outside code blocks
        is treated as explanation.
        """
        # Find all Python code blocks
        code_pattern = r"```python\s*\n(.*?)```"
        code_matches = re.findall(code_pattern, response_text, re.DOTALL)

        # Join multiple code blocks if present
        code = "\n\n".join(code_matches).strip() if code_matches else None

        # Explanation is everything outside code blocks
        explanation = re.sub(code_pattern, "", response_text, flags=re.DOTALL).strip()

        return {
            "explanation": explanation,
            "code": code,
            "raw_response": response_text,
        }
