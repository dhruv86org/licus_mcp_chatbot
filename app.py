"""
Customer Support Chatbot for Computer Products Company
Built with Streamlit and Google Gemini Flash
"""
import streamlit as st
import asyncio
import json
import time
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from mcp_client import MCPClient, MCP_TOOLS, get_tool_definitions_for_gemini

# Configuration
MCP_SERVER_URL = "https://vipfapwm3x.us-east-1.awsapprunner.com/mcp"

# Page configuration
st.set_page_config(
    page_title="TechSupport Pro - Customer Support",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Chat message styling */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 10px;
        margin: 5px 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        color: white;
        text-align: center;
    }
    
    .header-title {
        font-size: 2.5em;
        font-weight: bold;
        margin: 0;
        color: #00d4ff;
    }
    
    .header-subtitle {
        font-size: 1.2em;
        color: #a0a0a0;
        margin-top: 5px;
    }
    
    /* Sidebar styling */
    .sidebar-info {
        background: linear-gradient(180deg, #1e3a5f 0%, #0d1b2a 100%);
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        color: white;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(90deg, #00d4ff 0%, #0099cc 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 10px 25px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(0, 212, 255, 0.4);
    }
    
    /* Tool call indicator */
    .tool-call {
        background: #f0f8ff;
        border-left: 4px solid #00d4ff;
        padding: 10px;
        margin: 5px 0;
        border-radius: 0 10px 10px 0;
        font-family: monospace;
        font-size: 0.85em;
    }
    
    /* Status indicator */
    .status-connected {
        color: #00ff88;
        font-weight: bold;
    }
    
    .status-disconnected {
        color: #ff4444;
        font-weight: bold;
    }
    
    /* Product category badges */
    .category-badge {
        display: inline-block;
        padding: 5px 15px;
        border-radius: 20px;
        margin: 3px;
        font-size: 0.9em;
        cursor: pointer;
    }
    
    .cat-computers { background: #4CAF50; color: white; }
    .cat-monitors { background: #2196F3; color: white; }
    .cat-printers { background: #FF9800; color: white; }
    .cat-accessories { background: #9C27B0; color: white; }
    .cat-networking { background: #F44336; color: white; }
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
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


def get_gemini_api_key():
    """Get Gemini API key from secrets, environment, or session state"""
    # First check session state (user input)
    if "user_api_key" in st.session_state and st.session_state.user_api_key:
        return st.session_state.user_api_key
    # Then check Streamlit secrets
    try:
        return st.secrets["GOOGLE_API_KEY"]
    except:
        pass
    # Finally check environment
    import os
    return os.getenv("GOOGLE_API_KEY", "")


async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Call an MCP tool and return the result"""
    client = st.session_state.mcp_client
    try:
        result = await client.call_tool(tool_name, arguments)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("result", "No result returned")
    except Exception as e:
        return f"Error calling tool: {str(e)}"


def process_tool_calls(response) -> tuple[str, list]:
    """Process tool calls from Gemini response"""
    tool_results = []
    
    for part in response.parts:
        if hasattr(part, 'function_call') and part.function_call:
            fc = part.function_call
            tool_name = fc.name
            arguments = dict(fc.args) if fc.args else {}
            
            # Execute the tool call
            result = asyncio.run(call_mcp_tool(tool_name, arguments))
            tool_results.append({
                "tool": tool_name,
                "arguments": arguments,
                "result": result
            })
            
            # Check if customer was verified
            if tool_name == "verify_customer_pin" and "Customer ID:" in result:
                st.session_state.customer_verified = True
                st.session_state.customer_info = result
    
    return tool_results


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

When using tools:
- Use search_products for natural language queries
- Use list_products with category filter for browsing
- Use get_product for specific SKU details
- Always verify customer before accessing their orders or placing new orders
- For orders, include sku, quantity, unit_price (as string), and currency (USD)
"""


def chat_with_gemini(user_message: str, max_retries: int = 3) -> str:
    """Send a message to Gemini and get a response with tool use"""
    api_key = get_gemini_api_key()
    if not api_key:
        return "⚠️ Please configure your Google API key in Streamlit secrets (GOOGLE_API_KEY) to use the chatbot."
    
    genai.configure(api_key=api_key)
    
    # Initialize model with tools - use stable model instead of experimental
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        tools=[get_tool_definitions_for_gemini()],
        system_instruction=get_system_prompt()
    )
    
    # Build conversation history - limit to last 6 messages to reduce token usage
    history = []
    for msg in st.session_state.messages[-6:]:
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [msg["content"]]})
    
    # Start chat
    chat = model.start_chat(history=history)
    
    # Retry logic with exponential backoff for rate limits
    for attempt in range(max_retries):
        try:
            # Send message and handle tool calls
            response = chat.send_message(user_message)
            
            # Process any tool calls
            max_iterations = 5
            iteration = 0
            all_tool_results = []
            
            while iteration < max_iterations:
                has_tool_call = any(
                    hasattr(part, 'function_call') and part.function_call 
                    for part in response.parts
                )
                
                if not has_tool_call:
                    break
                
                tool_results = process_tool_calls(response)
                all_tool_results.extend(tool_results)
                
                # Send tool results back to the model
                function_responses = []
                for tr in tool_results:
                    function_responses.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=tr["tool"],
                                response={"result": tr["result"]}
                            )
                        )
                    )
                
                response = chat.send_message(function_responses)
                iteration += 1
            
            # Extract final text response
            final_response = ""
            for part in response.parts:
                if hasattr(part, 'text') and part.text:
                    final_response += part.text
            
            # Add tool call info to response if any
            if all_tool_results:
                tool_info = "\n\n---\n*Tools used:*\n"
                for tr in all_tool_results:
                    tool_info += f"- `{tr['tool']}({json.dumps(tr['arguments'])})`\n"
                # Optionally append tool info (commented out for cleaner UI)
                # final_response += tool_info
            
            return final_response or "I apologize, but I couldn't generate a response. Please try again."
        
        except google_exceptions.ResourceExhausted as e:
            if attempt < max_retries - 1:
                # Exponential backoff: wait 2^attempt seconds (1, 2, 4 seconds)
                wait_time = 2 ** attempt
                time.sleep(wait_time)
                continue
            else:
                return "⚠️ **Rate Limit Exceeded**\n\nThe AI service is currently experiencing high demand. Please try again in a few moments.\n\n*Tip: You can also try clearing the chat history to reduce token usage.*"
        
        except google_exceptions.InvalidArgument as e:
            return f"⚠️ **Configuration Error**\n\nThere was an issue with the request. Please check your API key configuration.\n\n*Error: {str(e)}*"
        
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            else:
                return f"⚠️ **Error**\n\nAn unexpected error occurred. Please try again.\n\n*Error: {str(e)}*"
    
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
    st.markdown(f"**LLM:** Gemini 1.5 Flash")
    
    st.divider()
    
    # Customer status
    st.markdown("### 👤 Customer Status")
    if st.session_state.customer_verified:
        st.success("✅ Customer Verified")
        if st.session_state.customer_info:
            # Extract customer name from info
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
        if st.button("🖥️ Computers", use_container_width=True):
            st.session_state.quick_action = "Show me computers"
    with col2:
        if st.button("🖵 Monitors", use_container_width=True):
            st.session_state.quick_action = "Show me monitors"
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("🖨️ Printers", use_container_width=True):
            st.session_state.quick_action = "Show me printers"
    with col4:
        if st.button("🎧 Accessories", use_container_width=True):
            st.session_state.quick_action = "Show me accessories"
    
    if st.button("📦 My Orders", use_container_width=True):
        st.session_state.quick_action = "Show my orders"
    
    st.divider()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.customer_verified = False
        st.session_state.customer_info = None
        st.rerun()
    
    st.divider()
    
    # API Key configuration
    st.markdown("### 🔑 API Configuration")
    api_key = get_gemini_api_key()
    if api_key:
        st.success("✅ API Key configured")
    else:
        st.warning("⚠️ API Key needed")
        user_key = st.text_input(
            "Enter Google API Key:",
            type="password",
            key="api_key_input",
            help="Get your free API key at https://aistudio.google.com/apikey"
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

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle quick actions
if "quick_action" in st.session_state and st.session_state.quick_action:
    user_input = st.session_state.quick_action
    st.session_state.quick_action = None
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = chat_with_gemini(user_input)
        st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()

# Chat input
if prompt := st.chat_input("How can I help you today?"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = chat_with_gemini(prompt)
        st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

# Welcome message if no messages
if not st.session_state.messages:
    st.markdown("""
    <div style="text-align: center; padding: 40px; background: rgba(255,255,255,0.9); border-radius: 20px; margin: 20px;">
        <h2>👋 Welcome to TechSupport Pro!</h2>
        <p style="font-size: 1.1em; color: #666;">
            I'm your AI customer support assistant. I can help you with:
        </p>
        <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin: 20px;">
            <div style="background: #4CAF50; color: white; padding: 15px 25px; border-radius: 10px;">
                🔍 Browse Products
            </div>
            <div style="background: #2196F3; color: white; padding: 15px 25px; border-radius: 10px;">
                💰 Check Prices
            </div>
            <div style="background: #FF9800; color: white; padding: 15px 25px; border-radius: 10px;">
                📦 Track Orders
            </div>
            <div style="background: #9C27B0; color: white; padding: 15px 25px; border-radius: 10px;">
                🛒 Place Orders
            </div>
        </div>
        <p style="color: #888; margin-top: 20px;">
            <em>Try asking: "Show me gaming laptops" or "I need a 4K monitor"</em>
        </p>
    </div>
    """, unsafe_allow_html=True)
