# 📋 Architecture & Design Decisions

This document outlines the key architectural and code decisions made while building TechSupport Pro - the AI-powered customer support chatbot.

---

## 🏗️ Architectural Decisions

### 1. Framework Selection: Streamlit

**Decision:** Use Streamlit as the frontend framework.

**Rationale:**
- Rapid prototyping with minimal boilerplate code
- Built-in chat UI components (`st.chat_message`, `st.chat_input`)
- Native session state management for conversation history
- Easy deployment to Streamlit Cloud
- No need for separate frontend/backend servers

**Trade-offs:**
- Less flexibility compared to React/Vue for complex UIs
- Limited control over real-time WebSocket connections
- Reruns entire script on each interaction (mitigated by session state)

---

### 2. LLM Choice: Google Gemini 1.5 Flash

**Decision:** Use `gemini-1.5-flash` as the language model.

**Rationale:**
- Cost-effective (significantly cheaper than GPT-4)
- Native function calling support
- Fast response times suitable for customer support
- Free tier available for development/testing
- Multi-turn conversation support
- **Stable production model** (vs experimental versions)

**Trade-offs:**
- Slightly less capable than larger models for complex reasoning
- Rate limits on free tier require error handling

**Update (Dec 2024):** Initially used `gemini-2.0-flash-exp` but switched to `gemini-1.5-flash` for stability and better rate limit handling in production.

---

### 3. Backend Integration: MCP (Model Context Protocol)

**Decision:** Integrate with backend services via MCP over HTTP.

**Rationale:**
- Standardized protocol for AI-tool integration
- Clean separation between LLM and business logic
- JSON-RPC based communication is simple to implement
- Supports tool discovery (`tools/list`) for dynamic capabilities

**Implementation Details:**
```
Client → HTTP POST → MCP Server → Database
        (JSON-RPC)
```

---

### 4. Three-Tier Architecture

**Decision:** Implement a clean three-tier architecture.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│  Gemini Flash   │────▶│   MCP Server    │
│   (Frontend)    │◀────│  (LLM Engine)   │◀────│  (Backend API)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

**Rationale:**
- Clear separation of concerns
- UI is decoupled from business logic
- LLM acts as intelligent middleware
- Backend can be replaced without UI changes

---

## 💻 Code Design Decisions

### 5. Async HTTP Client with httpx

**Decision:** Use `httpx` for async HTTP communication instead of `requests`.

**Rationale:**
- Native async/await support
- Timeout configuration for long-running requests
- Streaming response support (for SSE if needed)
- Better performance for concurrent tool calls

**Code Example:**
```python
async with httpx.AsyncClient(timeout=30.0) as client:
    response = await client.post(self.server_url, json=payload)
```

---

### 6. Session State for Conversation Management

**Decision:** Store all conversation state in `st.session_state`.

**State Variables:**
| Variable | Purpose |
|----------|---------|
| `messages` | Chat history for UI display |
| `customer_verified` | Authentication flag |
| `customer_info` | Verified customer details |
| `mcp_client` | Persistent MCP client instance |
| `chat_history` | Extended context for LLM |

**Rationale:**
- Persists across Streamlit reruns
- No external database needed for MVP
- Clean reset on new session

---

### 7. Tool Definition Pattern

**Decision:** Define tools as a declarative list with schema validation.

**Structure:**
```python
MCP_TOOLS = [
    {
        "name": "tool_name",
        "description": "What this tool does",
        "parameters": {
            "type": "object",
            "properties": {...},
            "required": [...]
        }
    }
]
```

**Rationale:**
- Single source of truth for tool schemas
- Easy conversion to Gemini's `FunctionDeclaration` format
- Self-documenting code
- Matches JSON Schema standard

---

### 8. Iterative Tool Execution Loop

**Decision:** Implement a loop that processes multiple sequential tool calls.

```python
max_iterations = 5
while iteration < max_iterations:
    if not has_tool_call:
        break
    tool_results = process_tool_calls(response)
    response = chat.send_message(function_responses)
    iteration += 1
```

**Rationale:**
- LLM may need to call multiple tools to fulfill a request
- Prevents infinite loops with max iterations
- Aggregates all tool results before final response

**Example Flow:**
1. User: "Place an order for a laptop"
2. Tool: `search_products` → Find laptop SKU
3. Tool: `get_product` → Get current price
4. Tool: `create_order` → Place order
5. Response: "Order placed successfully!"

---

### 9. Customer Authentication Flow

**Decision:** PIN-based verification stored in session state.

**Flow:**
1. Customer provides email + PIN
2. LLM calls `verify_customer_pin` tool
3. On success: `st.session_state.customer_verified = True`
4. Customer context added to system prompt

**Rationale:**
- Simple but secure for demo purposes
- No password complexity requirements
- State persists for entire session
- Easy to upgrade to OAuth/SSO later

---

### 10. System Prompt Engineering

**Decision:** Dynamic system prompt with customer context injection.

**Structure:**
```
[Role Definition]
[Capabilities List]
[Guidelines]
[Product Categories]
[Dynamic Customer Context]  ← Injected when verified
[Tool Usage Instructions]
```

**Rationale:**
- Provides consistent personality and boundaries
- Customer context enables personalized responses
- Tool instructions improve accuracy

---

## 🛡️ Resilience & Error Handling

### 11. Retry Logic with Exponential Backoff

**Decision:** Implement automatic retries with exponential backoff for API rate limits.

**Implementation:**
```python
for attempt in range(max_retries):  # max_retries = 3
    try:
        response = chat.send_message(user_message)
        # ... process response
    except google_exceptions.ResourceExhausted:
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            time.sleep(wait_time)
            continue
        else:
            return "Rate limit error message..."
```

**Rationale:**
- Google's free tier has strict rate limits (15 RPM for Gemini)
- Exponential backoff prevents thundering herd
- Graceful degradation with user-friendly error messages
- Up to 3 retries before giving up

---

### 12. Reduced Conversation History

**Decision:** Limit conversation history sent to the LLM to 6 messages.

**Rationale:**
- Reduces token usage per request
- Lowers costs and helps stay within rate limits
- 6 messages (3 turns) provides sufficient context for most queries
- Prevents context window overflow on long conversations

**Trade-off:**
- May lose context in very long conversations
- Mitigated by customer context in system prompt

---

### 13. Stable Model Selection

**Decision:** Use `gemini-1.5-flash` instead of experimental models.

**Rationale:**
- Experimental models (`gemini-2.0-flash-exp`) have stricter quotas
- Production stability is more important than cutting-edge features
- Consistent behavior across deployments
- Better rate limit allowances

---

### 14. Specific Exception Handling

**Decision:** Catch and handle specific Google API exceptions.

**Handled Exceptions:**
| Exception | Handling |
|-----------|----------|
| `ResourceExhausted` | Retry with backoff, then user message |
| `InvalidArgument` | Configuration error message |
| Generic `Exception` | Retry once, then generic error |

**Rationale:**
- Different errors need different user messaging
- Prevents exposing internal error details
- Provides actionable feedback to users

---

## 🎨 UI/UX Decisions

### 15. Dark Theme with Cyan Accents

**Decision:** Use a dark theme with `#00d4ff` (cyan) as the primary accent color.

**Color Palette:**
| Element | Color |
|---------|-------|
| Background | `#0e1117` |
| Secondary | `#1a1a2e` |
| Primary | `#00d4ff` |
| Text | `#fafafa` |

**Rationale:**
- Reduces eye strain for extended use
- Professional appearance for B2B/enterprise
- High contrast for accessibility

---

### 16. Sidebar for Controls, Main Area for Chat

**Decision:** Place all controls/status in sidebar, keep main area focused on conversation.

**Sidebar Contains:**
- System status indicators
- Customer verification status
- Quick action buttons
- API configuration
- Demo test accounts

**Rationale:**
- Follows chat app conventions (WhatsApp, Slack)
- Reduces cognitive load during conversations
- Quick actions provide discoverability

---

### 17. Quick Action Buttons

**Decision:** Provide pre-built quick action buttons for common tasks.

**Buttons:**
- 🖥️ Computers
- 🖵 Monitors
- 🖨️ Printers
- 🎧 Accessories
- 📦 My Orders

**Rationale:**
- Reduces typing for common queries
- Teaches users what's possible
- Improves demo experience

---

## 🔧 Infrastructure Decisions

### 18. Minimal Dependencies

**Decision:** Keep dependencies minimal and well-maintained.

**Dependencies:**
```
streamlit>=1.31.0          # UI framework
google-generativeai>=0.8.0 # LLM integration
httpx>=0.27.0              # Async HTTP client
python-dotenv>=1.0.0       # Environment management
```

**Rationale:**
- Faster installation and startup
- Fewer security vulnerabilities to track
- Easier maintenance and upgrades

---

### 19. API Key Management

**Decision:** Support multiple API key sources with priority order.

**Priority:**
1. Session state (user input in UI)
2. Streamlit secrets (`st.secrets`)
3. Environment variable (`GOOGLE_API_KEY`)

**Rationale:**
- Works in all deployment scenarios
- Users can test without modifying files
- Production uses secure secrets management

---

### 20. Single-File MCP Client

**Decision:** Implement MCP client in a single `mcp_client.py` file.

**Contents:**
- `MCPClient` class with async methods
- `MCP_TOOLS` constant with tool definitions
- `get_tool_definitions_for_gemini()` converter

**Rationale:**
- Easy to understand and modify
- All MCP logic in one place
- Can be extracted to a package later if needed

---

## 📈 Scalability Considerations

### Future Improvements

| Area | Current | Future Enhancement |
|------|---------|-------------------|
| State | In-memory | Redis/PostgreSQL |
| Auth | PIN-based | OAuth 2.0 / SSO |
| LLM | Single model | Model router |
| UI | Streamlit | React + FastAPI |
| Tools | Static list | Dynamic discovery |
| Rate Limits | Retry + backoff | Queue + caching |

---

## 🔒 Security Decisions

### Implemented
- PIN verification before order placement
- No storage of sensitive customer data in session
- XSRF protection enabled
- CORS disabled (same-origin)
- Error messages don't expose internal details

### Deferred for Production
- Rate limiting at application level
- Input sanitization beyond LLM
- Audit logging
- PII encryption

---

## 📝 Summary

The key philosophy behind these decisions was **simplicity first**:

1. **Minimize complexity** - Use frameworks that handle boilerplate
2. **Leverage LLM capabilities** - Let Gemini handle conversation flow
3. **Clean interfaces** - MCP provides a standard tool interface
4. **Progressive enhancement** - Start simple, upgrade as needed
5. **Graceful degradation** - Handle errors without crashing

This architecture supports rapid iteration while maintaining a clear path to production-ready scaling.

---

## 📅 Changelog

| Date | Decision | Change |
|------|----------|--------|
| Initial | Model Selection | Used `gemini-2.0-flash-exp` |
| Dec 2024 | Model Selection | Switched to `gemini-1.5-flash` for stability |
| Dec 2024 | Error Handling | Added retry logic with exponential backoff |
| Dec 2024 | Token Optimization | Reduced history from 10 to 6 messages |

