# 🖥️ TechSupport Pro - Customer Support Chatbot

A modern AI-powered customer support chatbot for a computer products company. Built with Streamlit, Google Gemini Flash, and MCP (Model Context Protocol) for seamless backend integration.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31+-red.svg)
![Gemini](https://img.shields.io/badge/Gemini-2.0_Flash-purple.svg)

## ✨ Features

- **🤖 AI-Powered Support**: Natural language understanding powered by Google Gemini 2.0 Flash
- **🔐 Customer Authentication**: Secure PIN-based customer verification
- **📦 Order Management**: View order history and place new orders
- **🔍 Product Search**: Search and browse products across categories
- **💰 Real-time Pricing**: Access current product prices and inventory
- **🎨 Modern UI**: Beautiful, responsive chat interface

## 🛍️ Product Categories

- **Computers**: Desktops, Laptops, Workstations, Gaming PCs, MacBooks
- **Monitors**: 24", 27", 32", Ultrawide, 4K, Curved, Portable, Touch Screen
- **Printers**: Laser, Inkjet, All-in-One, Photo, Large Format, 3D, Label
- **Accessories**: Keyboards, Mice, Webcams, Headsets, Docking Stations
- **Networking**: Routers, Switches, Access Points, Modems

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Google API Key (for Gemini)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd customer-support-chatbot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your API key:
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml and add your GOOGLE_API_KEY
```

4. Run the app:
```bash
streamlit run app.py
```

## 🧪 Demo Test Accounts

Use these test accounts to try the chatbot:

| Email | PIN |
|-------|-----|
| donaldgarcia@example.net | 7912 |
| michellejames@example.com | 1520 |
| laurahenderson@example.org | 1488 |
| spenceamanda@example.org | 2535 |
| glee@example.net | 4582 |
| williamsthomas@example.net | 4811 |

## 💬 Example Conversations

**Browse Products:**
- "Show me gaming laptops"
- "What monitors do you have under $500?"
- "I need a printer for home office"

**Get Product Details:**
- "Tell me more about the MacBook Pro Model A"
- "What's the price of SKU MON-0054?"

**Account Access:**
- "I want to verify my account. My email is donaldgarcia@example.net"
- "Show me my order history"

**Place Orders:**
- "I'd like to order 2 wireless keyboards"
- "Add a 4K monitor to my order"

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Streamlit UI  │────▶│  Gemini Flash   │────▶│   MCP Server    │
│   (Frontend)    │◀────│  (LLM Engine)   │◀────│  (Backend API)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

- **Streamlit**: Modern chat UI with real-time updates
- **Gemini Flash**: Cost-effective LLM for natural language understanding
- **MCP Server**: Backend API for products, customers, and orders

## 📁 Project Structure

```
├── app.py                 # Main Streamlit application
├── mcp_client.py          # MCP server client
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── .streamlit/
    ├── config.toml        # Streamlit theme configuration
    └── secrets.toml       # API keys (not in repo)
```

## 🔧 Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| GOOGLE_API_KEY | Google AI API key for Gemini |

### MCP Server

The chatbot connects to an MCP server that provides:
- Product catalog management
- Customer verification
- Order processing

## 📦 Deployment to Streamlit Cloud

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Add your `GOOGLE_API_KEY` in the app secrets
5. Deploy!

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.
