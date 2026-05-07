# 📋 Test Cases Plan — CareerViet AI Data Analysis Assistant

> **Application:** CareerViet AI Analyst (Streamlit + OpenAI Responses API)
> **Modules Under Test:** `ai_agent.py`, `code_executor.py`, `log_store.py`, `app.py`
> **Date:** 2026-05-06

---

## 1. AI Connection & Initialization

### TC-1.1: Auto-connect with valid API key
| Item | Detail |
|------|--------|
| **Precondition** | `.env` file contains a valid `OPENAI_API_KEY` |
| **Steps** | 1. Run `streamlit run app.py` |
| **Expected Result** | Sidebar shows "✅ Đã kết nối OpenAI (Responses API)". No error messages. |
| **Mapped Requirement** | API connection, auto-connect on startup |

### TC-1.2: Auto-connect with missing API key
| Item | Detail |
|------|--------|
| **Precondition** | `.env` file is empty or `OPENAI_API_KEY` is not set |
| **Steps** | 1. Remove/rename `.env` → Run `streamlit run app.py` |
| **Expected Result** | Sidebar shows error "❌ OPENAI_API_KEY chưa được cấu hình trong file .env". "🔄 Thử kết nối lại" button is visible. |
| **Mapped Requirement** | Graceful error handling |

### TC-1.3: Auto-connect with invalid API key
| Item | Detail |
|------|--------|
| **Precondition** | `.env` file contains `OPENAI_API_KEY=sk-invalid-key` |
| **Steps** | 1. Run `streamlit run app.py` → 2. Send any message |
| **Expected Result** | Connection may succeed (key validation is deferred), but first message returns an API authentication error displayed in the chat. |
| **Mapped Requirement** | Error handling |

### TC-1.4: Retry connection
| Item | Detail |
|------|--------|
| **Precondition** | TC-1.2 failure state |
| **Steps** | 1. Fix `.env` with valid key → 2. Click "🔄 Thử kết nối lại" |
| **Expected Result** | App reconnects and sidebar shows "✅ Đã kết nối OpenAI (Responses API)" |
| **Mapped Requirement** | Recovery |

---

## 2. Conversation Management

### TC-2.1: Automatic conversation creation on first message
| Item | Detail |
|------|--------|
| **Precondition** | Connected. No active conversation (`conversation_id` is None) |
| **Steps** | 1. Type a message in the chat input → 2. Press Enter |
| **Expected Result** | A new conversation is created (internally `conv_...` ID is assigned). AI response appears. |
| **Mapped Requirement** | Responses API conversation lifecycle |

### TC-2.2: Context persistence across multiple turns
| Item | Detail |
|------|--------|
| **Precondition** | Active conversation from TC-2.1 |
| **Steps** | 1. Send "Có bao nhiêu dòng trong bộ dữ liệu?" → 2. After response, send "Còn số cột thì sao?" |
| **Expected Result** | The AI's second response references the dataset context from the first message, proving conversation state is persisted. |
| **Mapped Requirement** | Conversation state (Responses API), §5.2 AI API — context |

### TC-2.3: New conversation button resets state
| Item | Detail |
|------|--------|
| **Precondition** | Active conversation with at least 2 messages |
| **Steps** | 1. Click "🔄 Cuộc hội thoại mới" in the sidebar |
| **Expected Result** | Chat area clears. Suggestion buttons reappear. `conversation_id` is reset to None. Next message creates a new conversation. |
| **Mapped Requirement** | Multi-session support |

---

## 3. AI Code Generation (Responses API)

### TC-3.1: AI generates code with Vietnamese explanation
| Item | Detail |
|------|--------|
| **Precondition** | Connected |
| **Steps** | 1. Send "Phân tích mức lương trung bình theo ngành nghề" |
| **Expected Result** | AI response contains: (a) a Vietnamese explanation above the code, (b) a Python code block using `df` and available libraries, (c) code status badge shows "⏳ Chờ duyệt". |
| **Mapped Requirement** | §1.1 AI role, §2 Mandatory code display, §2 Natural language explanation |

### TC-3.2: AI response without code (text-only)
| Item | Detail |
|------|--------|
| **Precondition** | Connected |
| **Steps** | 1. Send "Xin chào, bạn là ai?" |
| **Expected Result** | AI responds with a text explanation only (no code block). No approval buttons are shown. |
| **Mapped Requirement** | §1.1 AI flexibility |

### TC-3.3: AI suggests analysis methods when user is unsure
| Item | Detail |
|------|--------|
| **Precondition** | Connected |
| **Steps** | 1. Send "Tôi không biết phân tích gì, gợi ý cho tôi" |
| **Expected Result** | AI responds with a list of suggested analysis methods for the CareerViet dataset, without generating code. |
| **Mapped Requirement** | §1.1 Human role — "can ask the AI to provide suggestions" |

### TC-3.4: Suggestion buttons trigger analysis
| Item | Detail |
|------|--------|
| **Precondition** | Connected, no messages yet (suggestion buttons visible) |
| **Steps** | 1. Click any suggestion button (e.g., "💡 Top 10 công ty tuyển dụng nhiều nhất") |
| **Expected Result** | The suggestion text is sent as a user message. AI generates code and explanation. |
| **Mapped Requirement** | UI/UX — request receiving function |

### TC-3.5: AI does not add external data
| Item | Detail |
|------|--------|
| **Precondition** | Connected |
| **Steps** | 1. Send "Hãy thêm dữ liệu thị trường chứng khoán vào phân tích" |
| **Expected Result** | AI refuses or explains that it can only use `df` and `df_industries`. Does not generate code that imports external data or fetches URLs. |
| **Mapped Requirement** | §1.1 — "not allowed to arbitrarily add other data" |

---

## 4. Code Approval Workflow

### TC-4.1: Approve and execute code
| Item | Detail |
|------|--------|
| **Precondition** | AI has generated code with status "⏳ Chờ duyệt" |
| **Steps** | 1. Review code in the text area → 2. Click "✅ Duyệt & Chạy" |
| **Expected Result** | Code executes locally. Status changes to "✅ Đã thực thi". Results (tables/charts/stdout) display below the code. |
| **Mapped Requirement** | §2.1 Approval Principle — "code is only executed if human approves" |

### TC-4.2: Edit code before approving
| Item | Detail |
|------|--------|
| **Precondition** | AI has generated code with status "⏳ Chờ duyệt" |
| **Steps** | 1. Modify the code in the text area (e.g., change `.head(10)` to `.head(20)`) → 2. Click "✅ Duyệt & Chạy" |
| **Expected Result** | The **modified** code runs (not the original). Results reflect the edited parameters. Log stores both generated and edited code. |
| **Mapped Requirement** | §2.1 — "Humans have the right to directly intervene and edit" |

### TC-4.3: Reject code
| Item | Detail |
|------|--------|
| **Precondition** | AI has generated code with status "⏳ Chờ duyệt" |
| **Steps** | 1. Click "❌ Từ chối" |
| **Expected Result** | Status changes to "🚫 Đã từ chối". Code is displayed read-only. No execution occurs. Log status updated to "rejected". |
| **Mapped Requirement** | §2.1 — Decision Maker role |

### TC-4.4: Code is NOT auto-executed
| Item | Detail |
|------|--------|
| **Precondition** | Connected |
| **Steps** | 1. Send an analysis request → 2. Observe the AI response |
| **Expected Result** | Code appears with "⏳ Chờ duyệt" badge. NO results are shown. Code did NOT run. Approval buttons are visible. |
| **Mapped Requirement** | §2 — "No Background Execution" principle |

---

## 5. Local Code Execution (Sandbox)

### TC-5.1: Execute code that produces a DataFrame result
| Item | Detail |
|------|--------|
| **Precondition** | Approved code that creates a variable named `result` |
| **Steps** | 1. Approve code like `result = df['emp_name'].value_counts().head(10).reset_index()` |
| **Expected Result** | A table is displayed with company names and counts. No errors. |
| **Mapped Requirement** | §5.2 Execution API — collect data tables |

### TC-5.2: Execute code that produces a Matplotlib chart
| Item | Detail |
|------|--------|
| **Precondition** | Approved code that uses `plt` |
| **Steps** | 1. Approve code that includes `plt.bar(...)` and `plt.tight_layout()` |
| **Expected Result** | A PNG chart image is displayed inline. |
| **Mapped Requirement** | §5.2 Execution API — collect chart images |

### TC-5.3: Execute code that produces a Plotly chart
| Item | Detail |
|------|--------|
| **Precondition** | Approved code that uses `px` or `go` |
| **Steps** | 1. Approve code like `fig = px.bar(df['location_name'].value_counts().head(10), ...)` |
| **Expected Result** | An interactive Plotly chart is rendered. |
| **Mapped Requirement** | §5.2 Execution API — collect charts |

### TC-5.4: Execute code that prints output
| Item | Detail |
|------|--------|
| **Precondition** | Approved code with `print()` statements |
| **Steps** | 1. Approve code like `print(f"Tổng số dòng: {len(df)}")` |
| **Expected Result** | "📋 Output" expander shows the printed text. |
| **Mapped Requirement** | §5.2 Execution API — collect logs |

### TC-5.5: Execution timeout (30s limit)
| Item | Detail |
|------|--------|
| **Precondition** | Connected |
| **Steps** | 1. Manually enter code in the editor: `import time; time.sleep(60)` → 2. Approve |
| **Expected Result** | After 30 seconds, execution is terminated. Error message shows "⏰ Code đã chạy quá 30 giây và bị dừng lại." |
| **Mapped Requirement** | Safety — prevent infinite loops |

### TC-5.6: Execution with runtime error
| Item | Detail |
|------|--------|
| **Precondition** | Connected |
| **Steps** | 1. Manually enter code: `result = df['nonexistent_column'].sum()` → 2. Approve |
| **Expected Result** | Status changes to "❌ Lỗi". Error details show the `KeyError` traceback. "🔧 Sửa lỗi với AI" and "✏️ Sửa thủ công" buttons appear. |
| **Mapped Requirement** | Error handling, §5.2 Execution API |

### TC-5.7: Dataset isolation — no mutation across runs
| Item | Detail |
|------|--------|
| **Precondition** | Connected |
| **Steps** | 1. Approve code: `df.drop(columns=['job_id'], inplace=True); print(len(df.columns))` → 2. Start a new conversation → 3. Approve code: `print(len(df.columns))` |
| **Expected Result** | First run shows (n-1) columns. Second run shows n columns (original). Dataset is reloaded fresh each execution. |
| **Mapped Requirement** | Data integrity — sandbox isolation |

### TC-5.8: Large DataFrame result is truncated
| Item | Detail |
|------|--------|
| **Precondition** | Connected |
| **Steps** | 1. Approve code: `result = df.copy()` (23,536 rows) |
| **Expected Result** | Table displays with note "hiển thị 500 dòng đầu" and total row count shown. |
| **Mapped Requirement** | Performance — display limit |

---

## 6. Error Recovery

### TC-6.1: Auto-fix with AI
| Item | Detail |
|------|--------|
| **Precondition** | Code execution failed (TC-5.6) |
| **Steps** | 1. Click "🔧 Sửa lỗi với AI" |
| **Expected Result** | AI receives the error traceback in the same conversation context. It responds with: (a) error explanation in Vietnamese, (b) corrected code in `⏳ Chờ duyệt` state. |
| **Mapped Requirement** | §1.1 AI role — error correction, conversation context |

### TC-6.2: Manual fix
| Item | Detail |
|------|--------|
| **Precondition** | Code execution failed (TC-5.6) |
| **Steps** | 1. Click "✏️ Sửa thủ công" |
| **Expected Result** | Code status resets to "⏳ Chờ duyệt". The text area becomes editable again. User can modify and re-approve. |
| **Mapped Requirement** | §2.1 — Human editing rights |

### TC-6.3: Approve fixed code from AI
| Item | Detail |
|------|--------|
| **Precondition** | AI has provided fixed code (TC-6.1) |
| **Steps** | 1. Review AI's fixed code → 2. Click "✅ Duyệt & Chạy" |
| **Expected Result** | Fixed code executes successfully. Status shows "✅ Đã thực thi". Results display correctly. |
| **Mapped Requirement** | End-to-end error recovery cycle |

---

## 7. SQLite Log Storage

### TC-7.1: Log created on AI response
| Item | Detail |
|------|--------|
| **Precondition** | Connected |
| **Steps** | 1. Send any analysis request → 2. Check sidebar "📜 Lịch sử" |
| **Expected Result** | New log entry appears with timestamp, status emoji, and truncated request text. |
| **Mapped Requirement** | §2.2 Storage Principle |

### TC-7.2: Log updated on code execution
| Item | Detail |
|------|--------|
| **Precondition** | AI generated code → User approved (TC-4.1) |
| **Steps** | 1. Query `ai_logs.db`: `SELECT status, edited_code, execution_result FROM logs ORDER BY id DESC LIMIT 1` |
| **Expected Result** | `status = "executed"`, `edited_code` contains the approved code, `execution_result` contains JSON with stdout/figures/tables count. |
| **Mapped Requirement** | §2.2, §5.2 Logs API — store source code and results |

### TC-7.3: Log updated on rejection
| Item | Detail |
|------|--------|
| **Precondition** | AI generated code → User rejected (TC-4.3) |
| **Steps** | 1. Query `ai_logs.db`: `SELECT status FROM logs ORDER BY id DESC LIMIT 1` |
| **Expected Result** | `status = "rejected"` |
| **Mapped Requirement** | §2.2 |

### TC-7.4: Log updated on failure
| Item | Detail |
|------|--------|
| **Precondition** | Code execution failed (TC-5.6) |
| **Steps** | 1. Query `ai_logs.db`: `SELECT status, error_traceback FROM logs ORDER BY id DESC LIMIT 1` |
| **Expected Result** | `status = "failed"`, `error_traceback` contains the Python traceback string |
| **Mapped Requirement** | §2.2 — store explanations |

### TC-7.5: Log stores conversation ID
| Item | Detail |
|------|--------|
| **Precondition** | Multiple messages in a conversation |
| **Steps** | 1. Query `ai_logs.db`: `SELECT thread_id FROM logs ORDER BY id DESC LIMIT 5` |
| **Expected Result** | All entries from the same conversation share the same `conv_...` ID |
| **Mapped Requirement** | §2.2, traceability |

### TC-7.6: Logs persist across restarts
| Item | Detail |
|------|--------|
| **Precondition** | App has been used (logs exist) |
| **Steps** | 1. Stop Streamlit → 2. Restart `streamlit run app.py` → 3. Check sidebar "📜 Lịch sử" |
| **Expected Result** | Previous log entries are still displayed from `ai_logs.db` |
| **Mapped Requirement** | §2.2 — "retrieved later" |

---

## 8. UI/UX Components

### TC-8.1: Sidebar dataset info
| Item | Detail |
|------|--------|
| **Steps** | 1. Expand "Xem thông tin dataset" in the sidebar |
| **Expected Result** | Shows row count (~23,536), column count (40), and column name list from `careerviet_all_jobs.csv` |
| **Mapped Requirement** | §5.1 — data context display |

### TC-8.2: Chat message styling
| Item | Detail |
|------|--------|
| **Steps** | 1. Send a message and observe the chat layout |
| **Expected Result** | User messages: purple gradient bubble, right-aligned. AI messages: light gray bubble, left-aligned with "🤖 AI Analyst" header. |
| **Mapped Requirement** | §5.1 — intuitive UI |

### TC-8.3: Code status badges display correctly
| Item | Detail |
|------|--------|
| **Steps** | 1. Observe code in different states through the workflow |
| **Expected Result** | Badges render: ⏳ Chờ duyệt (yellow), ✅ Đã thực thi (green), ❌ Lỗi (red), 🚫 Đã từ chối (gray) |
| **Mapped Requirement** | §5.1 — source code viewing |

### TC-8.4: Log history displays in sidebar with correct status emojis
| Item | Detail |
|------|--------|
| **Steps** | 1. Perform multiple actions (approve, reject, fail) → 2. Check sidebar |
| **Expected Result** | Each log entry shows the correct emoji: ⏳/✅/❌/🚫/🔧 with timestamp and truncated request |
| **Mapped Requirement** | §5.1 — result display |

---

## 9. Edge Cases & Security

### TC-9.1: Empty message input
| Item | Detail |
|------|--------|
| **Steps** | 1. Press Enter in the chat input without typing anything |
| **Expected Result** | No message is sent. No error occurs. |
| **Mapped Requirement** | Input validation |

### TC-9.2: Very long user message
| Item | Detail |
|------|--------|
| **Steps** | 1. Paste a 5000-character message into the chat input → 2. Press Enter |
| **Expected Result** | Message is sent and AI responds normally. UI remains stable. |
| **Mapped Requirement** | Robustness |

### TC-9.3: Code attempts to access filesystem
| Item | Detail |
|------|--------|
| **Steps** | 1. Manually enter: `import os; os.listdir('C:/')` → 2. Approve |
| **Expected Result** | Code executes (sandbox uses `__builtins__`), but results are limited to stdout display. No data exfiltration to external services. |
| **Mapped Requirement** | §1.1 — "Code execution must be on user's local environment" (acceptable since it's the user's own machine) |

### TC-9.4: Code attempts network access
| Item | Detail |
|------|--------|
| **Steps** | 1. Manually enter: `import urllib.request; urllib.request.urlopen('https://example.com')` → 2. Approve |
| **Expected Result** | Code may execute (user approved it), but AI should not generate such code. If manually entered, user takes responsibility. |
| **Mapped Requirement** | §1.1 — AI must not add external data |

### TC-9.5: Multiple rapid messages
| Item | Detail |
|------|--------|
| **Steps** | 1. Send 3 messages rapidly in succession |
| **Expected Result** | Each message is processed sequentially. No duplicate messages or state corruption. |
| **Mapped Requirement** | Stability |

---

## Test Summary Matrix

| Module | # Test Cases | Requirement Coverage |
|--------|:---:|---|
| **1. Connection** | 4 | Auto-connect, error handling, recovery |
| **2. Conversation** | 3 | Responses API, context persistence, reset |
| **3. AI Code Gen** | 5 | Code + explanation, suggestions, data boundary |
| **4. Approval Workflow** | 4 | Approve, edit, reject, no-auto-execution |
| **5. Code Execution** | 8 | DataFrame, charts, stdout, timeout, errors, isolation |
| **6. Error Recovery** | 3 | Auto-fix, manual fix, fix approval |
| **7. Log Storage** | 6 | Create, update, persist, conversation tracking |
| **8. UI/UX** | 4 | Sidebar, chat styling, badges, history |
| **9. Edge Cases** | 5 | Empty input, long input, filesystem, network, rapid |
| **Total** | **42** | |
