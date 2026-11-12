# 💸 AI Freelance Quote & PayPal Checkout Assistant

An AI-powered billing assistant built for the **PayPal AI Hackathon**. Freelancers and small businesses can paste unstructured client emails or chat messages, and the app uses **Google Gemini** with structured outputs to extract deliverables, calculate totals, and automatically generate a live **PayPal Sandbox Checkout** link via the PayPal Orders v2 API.

## 🚀 Features
- **Natural Language Quote Extraction:** Converts messy client messages into itemized line items, quantities, and unit prices using Gemini Structured JSON Outputs (`Pydantic`).
- **Automatic Model Fallback:** Resilient multi-model routing across Gemini models to handle high-demand API spikes.
- **Instant PayPal Checkout Link:** Authenticates via OAuth 2.0 against PayPal Sandbox and generates an actionable `PAY_NOW` checkout URL via `/v2/checkout/orders`.

## 🛠️ Tech Stack
- **Frontend & Backend:** Python, Streamlit
- **AI Engine:** Google Gemini API (`google-genai`, Pydantic structured schemas)
- **Payments:** PayPal REST APIs (OAuth 2.0 & Orders v2 Sandbox)

## ⚙️ Setup & Run Locally
1. Clone this repository:
   ```bash
   git clone <YOUR_REPO_URL>
   cd <YOUR_REPO_FOLDER>
