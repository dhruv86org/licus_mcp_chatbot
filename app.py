"""
Customer Support Chatbot for Computer Products Company
Built with Streamlit and OpenRouter (GPT-4o-mini)
"""
import streamlit as st
import asyncio
import json
import time
import httpx
from openai import OpenAI
from mcp_client import MCPClient, MCP_TOOLS

# Configuration
MCP_SERVER_URL = "https://vipfapwm3x.us-east-1.awsapprunner.com/mcp"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# OpenAI model with function calling support
DEFAULT_MODEL = "openai/gpt-4o-mini"


def run_async(coro):
    """Run async code safely in Streamlit environment"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# Page configuration
st.set_page_config(
    page_title="TechSupport Pro - Customer Support",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern dark UI
st.markdown("""
<style>
    /* Main app background - dark gradient */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #00d4ff !important;
    }
    
    /* Chat messages - dark cards with good contrast */
    [data-testid="stChatMessage"] {
        background: linear-gradient(135deg, #1e1e2f 0%, #2d2d44 100%) !important;
        border: 1px solid #3d3d5c;
        border-radius: 16px !important;
        padding: 16px !important;
        margin: 10px 0 !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }
    
    /* Chat message text - ensure readability */
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] span {
        color: #f0f0f0 !important;
        font-size: 1rem;
        line-height: 1.6;
    }
    
    /* Code blocks in chat */
    [data-testid="stChatMessage"] code {
        background: #1a1a2e !important;
        color: #00d4ff !important;
        padding: 2px 6px;
        border-radius: 4px;
    }
    
    /* User message accent */
    [data-testid="stChatMessage"][data-testid*="user"] {
        border-left: 4px solid #00d4ff;
    }
    
    /* Assistant message accent */
    [data-testid="stChatMessage"][data-testid*="assistant"] {
        border-left: 4px solid #9d4edd;
    }
    
    /* Header container */
    .header-container {
        background: linear-gradient(90deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 24px 32px;
        border-radius: 20px;
        margin-bottom: 24px;
        text-align: center;
        border: 1px solid #3d3d5c;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    .header-title {
        font-size: 2.5em;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(90deg, #00d4ff, #9d4edd);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .header-subtitle {
        font-size: 1.15em;
        color: #a0a0c0;
        margin-top: 8px;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #00d4ff 0%, #0099cc 100%);
        color: white !important;
        border: none;
        border-radius: 25px;
        padding: 10px 25px;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 212, 255, 0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0, 212, 255, 0.5);
    }
    
    /* Status indicators */
    .status-connected { color: #00ff88 !important; font-weight: bold; }
    
    /* Chat input styling */
    [data-testid="stChatInput"] {
        background: #1e1e2f !important;
        border: 1px solid #3d3d5c !important;
        border-radius: 12px !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #f0f0f0 !important;
        background: transparent !important;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: #1e1e2f !important;
        color: #e0e0e0 !important;
        border-radius: 8px;
    }
    
    /* Welcome card */
    .welcome-card {
        background: linear-gradient(135deg, #1e1e2f 0%, #2d2d44 100%);
        border: 1px solid #3d3d5c;
        border-radius: 20px;
        padding: 40px;
        margin: 20px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    .welcome-card h2 {
        color: #00d4ff;
        margin-bottom: 16px;
    }
    .welcome-card p {
        color: #c0c0d0;
        font-size: 1.1em;
    }
    .feature-badge {
        display: inline-block;
        padding: 12px 20px;
        border-radius: 10px;
        margin: 8px;
        font-weight: 600;
        color: white;
    }
    
    /* Markdown text color */
    .stMarkdown, .stMarkdown p, .stMarkdown li {
        color: #e0e0e0;
    }
    
    /* Dividers */
    hr {
        border-color: #3d3d5c !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "customer_verified" not in st.session_state:
    st.session_state.customer_verified = False
if "customer_info" not in st.session_state:
    st.session_state.customer_info = None
if "mcp_client" not in st.session_state:
    st.session_state.mcp_client = MCPClient(MCP_SERVER_URL)


def get_api_key():
    """Get OpenRouter API key from secrets, environment, or session state"""
    if "user_api_key" in st.session_state and st.session_state.user_api_key:
        return st.session_state.user_api_key
    try:
        return st.secrets["OPENROUTER_API_KEY"]
    except:
        pass
    import os
    return os.getenv("OPENROUTER_API_KEY", "")


async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Call an MCP tool and return the result"""
    client = st.session_state.mcp_client
    try:
        result = await client.call_tool(tool_name, arguments)
        if "error" in result:
            error_msg = result.get('error', {})
            if isinstance(error_msg, dict):
                return f"Error: {error_msg.get('message', str(error_msg))}"
            return f"Error: {error_msg}"
        return result.get("result", "No result returned")
    except httpx.ConnectError:
        return "Connection error: Could not connect to MCP server."
    except httpx.TimeoutException:
        return "Timeout error: MCP server took too long to respond."
    except Exception as e:
        return f"Error calling tool '{tool_name}': {str(e)}"


def get_openai_tools():
    """Get tool definitions in OpenAI format"""
    tools = []
    for tool in MCP_TOOLS:
        tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
        })
    return tools


def get_system_prompt():
    """Get the system prompt for the chatbot"""
    customer_context = ""
    if st.session_state.customer_verified and st.session_state.customer_info:
        customer_context = f"""
VERIFIED CUSTOMER CONTEXT:
{st.session_state.customer_info}
The customer has been verified and can place orders.
"""
    
    return f"""You are a helpful and friendly customer support agent for TechSupport Pro, a company that sells computer products including computers, monitors, printers, accessories, and networking equipment.

Your capabilities:
1. Help customers browse and search for products
2. Provide detailed product information and pricing
3. Verify customer identity using their email and PIN
4. View customer order history
5. Help customers place new orders (only after verification)

Guidelines:
- Be friendly, professional, and helpful
- Always verify customer identity (email + PIN) before accessing their account or placing orders
- Provide clear pricing information in USD
- If a customer wants to order, ensure they're verified first
- Suggest relevant products based on customer needs
- Keep responses concise but informative

Available product categories:
- Computers (desktops, laptops, workstations, gaming PCs, MacBooks)
- Monitors (24", 27", 32", ultrawide, 4K, curved, portable, touch screen)
- Printers (laser, inkjet, all-in-one, photo, large format, 3D, label, receipt)
- Accessories (keyboards, mice, webcams, headsets, USB hubs, docking stations, KVM switches)
- Networking (routers, switches, access points, modems)

{customer_context}

When you need to perform actions, use the available tools:
- verify_customer_pin: Verify customer with email and PIN
- list_products: List products by category
- search_products: Search products by name/description
- get_product: Get product details by SKU
- list_orders: View customer orders
- create_order: Place a new order (requires verified customer)
"""


def chat_with_openrouter(user_message: str, max_retries: int = 3) -> str:
    """Send a message to OpenRouter and get a response with tool use"""
    print(f"[DEBUG] chat_with_openrouter called with: {user_message}")
    
    api_key = get_api_key()
    print(f"[DEBUG] API key found: {'Yes' if api_key else 'No'}")
    
    if not api_key:
        return "⚠️ Please configure your OpenRouter API key in the sidebar or in Streamlit secrets (OPENROUTER_API_KEY)."
    
    client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
    )
    
    # Build conversation messages
    messages = [{"role": "system", "content": get_system_prompt()}]
    
    # Add last 6 messages for context
    for msg in st.session_state.messages[-6:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add current user message
    messages.append({"role": "user", "content": user_message})
    
    tools = get_openai_tools()
    all_tool_results = []
    
    for attempt in range(max_retries):
        try:
            print(f"[DEBUG] Calling OpenRouter API with model: {DEFAULT_MODEL}")
            
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                extra_headers={
                    "HTTP-Referer": "https://techsupport-pro.streamlit.app",
                    "X-Title": "TechSupport Pro Chatbot"
                }
            )
            
            assistant_message = response.choices[0].message
            
            # Process tool calls if any
            max_iterations = 5
            iteration = 0
            
            while assistant_message.tool_calls and iteration < max_iterations:
                print(f"[DEBUG] Processing {len(assistant_message.tool_calls)} tool calls...")
                
                # Add assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in assistant_message.tool_calls
                    ]
                })
                
                # Execute each tool call
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except:
                        arguments = {}
                    
                    print(f"[DEBUG] Calling tool: {tool_name} with args: {arguments}")
                    
                    try:
                        result = run_async(call_mcp_tool(tool_name, arguments))
                        print(f"[DEBUG] Tool result: {str(result)[:200]}")
                    except Exception as e:
                        result = f"Error: {str(e)}"
                    
                    all_tool_results.append({
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": result
                    })
                    
                    # Check for customer verification
                    if tool_name == "verify_customer_pin" and "Customer ID:" in str(result):
                        print("[DEBUG] Customer verified!")
                        st.session_state.customer_verified = True
                        st.session_state.customer_info = result
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result)
                    })
                
                # Get next response
                response = client.chat.completions.create(
                    model=DEFAULT_MODEL,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    extra_headers={
                        "HTTP-Referer": "https://techsupport-pro.streamlit.app",
                        "X-Title": "TechSupport Pro Chatbot"
                    }
                )
                assistant_message = response.choices[0].message
                iteration += 1
            
            # Extract final response
            final_response = assistant_message.content or "I apologize, but I couldn't generate a response."
            
            # Add tool info for debugging
            if all_tool_results:
                tool_info = "\n\n---\n*🔧 Tools used:*\n"
                for tr in all_tool_results:
                    result_preview = str(tr['result'])[:100]
                    tool_info += f"- `{tr['tool']}` → {result_preview}{'...' if len(str(tr['result'])) > 100 else ''}\n"
                final_response += tool_info
            
            return final_response
            
        except Exception as e:
            print(f"[DEBUG] Error: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                return f"⚠️ **Error**\n\nAn error occurred: {str(e)}\n\n*Please check your API key and try again.*"
    
    return "I apologize, but I couldn't generate a response. Please try again."


# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <h2 style="color: #00d4ff;">🖥️ TechSupport Pro</h2>
        <p style="color: #888;">Customer Support Portal</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Connection status
    st.markdown("### 🔌 System Status")
    st.markdown(f"**MCP Server:** <span class='status-connected'>Connected</span>", unsafe_allow_html=True)
    st.markdown(f"**LLM:** GPT-4o-mini")
    
    st.divider()
    
    # Customer status
    st.markdown("### 👤 Customer Status")
    if st.session_state.customer_verified:
        st.success("✅ Customer Verified")
        if st.session_state.customer_info:
            info_lines = st.session_state.customer_info.split('\n')
            for line in info_lines:
                if 'Name:' in line:
                    st.info(line.strip())
                    break
    else:
        st.warning("🔒 Not Verified")
        st.caption("Ask me to verify with your email and PIN")
    
    st.divider()
    
    # Quick actions
    st.markdown("### 🚀 Quick Actions")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🖥️ Computers", use_container_width=True, key="btn_computers"):
            st.session_state.quick_action = "Show me computers"
            st.rerun()
    with col2:
        if st.button("🖵 Monitors", use_container_width=True, key="btn_monitors"):
            st.session_state.quick_action = "Show me monitors"
            st.rerun()
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("🖨️ Printers", use_container_width=True, key="btn_printers"):
            st.session_state.quick_action = "Show me printers"
            st.rerun()
    with col4:
        if st.button("🎧 Accessories", use_container_width=True, key="btn_accessories"):
            st.session_state.quick_action = "Show me accessories"
            st.rerun()
    
    if st.button("📦 My Orders", use_container_width=True, key="btn_orders"):
        st.session_state.quick_action = "Show my orders"
        st.rerun()
    
    st.divider()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True, key="btn_clear"):
        st.session_state.messages = []
        st.session_state.customer_verified = False
        st.session_state.customer_info = None
        st.rerun()
    
    st.divider()
    
    # API Key configuration
    st.markdown("### 🔑 API Configuration")
    api_key = get_api_key()
    if api_key:
        st.success("✅ API Key configured")
    else:
        st.warning("⚠️ API Key needed")
        user_key = st.text_input(
            "Enter OpenRouter API Key:",
            type="password",
            key="api_key_input",
            help="Get your free API key at https://openrouter.ai/keys"
        )
        if user_key:
            st.session_state.user_api_key = user_key
            st.rerun()
    
    st.divider()
    
    # Test customers info
    with st.expander("🧪 Demo Test Accounts"):
        st.markdown("""
        **Test Customers:**
        - `donaldgarcia@example.net` / PIN: `7912`
        - `michellejames@example.com` / PIN: `1520`
        - `laurahenderson@example.org` / PIN: `1488`
        - `spenceamanda@example.org` / PIN: `2535`
        - `glee@example.net` / PIN: `4582`
        - `williamsthomas@example.net` / PIN: `4811`
        """)


# Main content area
st.markdown("""
<div class="header-container">
    <p class="header-title">🖥️ TechSupport Pro</p>
    <p class="header-subtitle">Your AI-Powered Customer Support Assistant</p>
</div>
""", unsafe_allow_html=True)

# Verification notice banner
if not st.session_state.customer_verified:
    st.markdown("""
    <div style="
        background: linear-gradient(90deg, #ff6b6b 0%, #ee5a24 100%);
        border-radius: 12px;
        padding: 16px 24px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 16px;
        box-shadow: 0 4px 15px rgba(238, 90, 36, 0.3);
    ">
        <span style="font-size: 2em;">🔐</span>
        <div>
            <p style="color: white; font-weight: 700; font-size: 1.1em; margin: 0;">
                Verify Your Account to Place Orders
            </p>
            <p style="color: rgba(255,255,255,0.9); font-size: 0.95em; margin: 4px 0 0 0;">
                Please verify with your <strong>email</strong> and <strong>PIN</strong> before placing orders.
                <br/>Example: <em>"Verify donaldgarcia@example.net, PIN: 7912"</em>
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    # Show verified status banner
    customer_name = ""
    if st.session_state.customer_info:
        for line in st.session_state.customer_info.split('\n'):
            if 'verified:' in line.lower():
                customer_name = line.split(':')[-1].strip()
                break
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, #00b894 0%, #00cec9 100%);
        border-radius: 12px;
        padding: 14px 24px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 16px;
        box-shadow: 0 4px 15px rgba(0, 184, 148, 0.3);
    ">
        <span style="font-size: 1.8em;">✅</span>
        <div>
            <p style="color: white; font-weight: 700; font-size: 1.1em; margin: 0;">
                Welcome, {customer_name if customer_name else 'Verified Customer'}!
            </p>
            <p style="color: rgba(255,255,255,0.9); font-size: 0.9em; margin: 4px 0 0 0;">
                You can now browse products, view orders, and place new orders.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle quick actions
if "quick_action" in st.session_state and st.session_state.quick_action:
    user_input = st.session_state.quick_action
    st.session_state.quick_action = None
    
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.spinner("Thinking..."):
        response = chat_with_openrouter(user_input)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# Chat input
if prompt := st.chat_input("How can I help you today?"):
    print(f"[DEBUG] Chat input received: {prompt}")
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = chat_with_openrouter(prompt)
        st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

# Welcome message if no messages
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-card" style="text-align: center;">
        <h2 style="font-size: 2em; margin-bottom: 16px;">👋 Welcome to TechSupport Pro!</h2>
        <p style="font-size: 1.15em; color: #b0b0c0; margin-bottom: 24px;">
            I'm your AI customer support assistant. I can help you with:
        </p>
        <div style="display: flex; justify-content: center; gap: 16px; flex-wrap: wrap; margin: 24px 0;">
            <div class="feature-badge" style="background: linear-gradient(135deg, #00b894 0%, #00cec9 100%);">
                🔍 Browse Products
            </div>
            <div class="feature-badge" style="background: linear-gradient(135deg, #0984e3 0%, #74b9ff 100%);">
                💰 Check Prices
            </div>
            <div class="feature-badge" style="background: linear-gradient(135deg, #e17055 0%, #fdcb6e 100%);">
                📦 Track Orders
            </div>
            <div class="feature-badge" style="background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);">
                🛒 Place Orders
            </div>
        </div>
        <p style="color: #808090; margin-top: 24px; font-size: 1.05em;">
            <em>Try asking: "Show me gaming laptops" or "I need a 4K monitor"</em>
        </p>
        <div style="margin-top: 24px; padding-top: 20px; border-top: 1px solid #3d3d5c;">
            <p style="color: #606070; font-size: 0.9em;">
                💡 <strong style="color: #00d4ff;">Tip:</strong> Verify your account first to access orders and make purchases
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
