import time
import streamlit as st
import requests
from pydantic import BaseModel
from google import genai
from google.genai import types

# --- PAGE SETUP ---
st.set_page_config(page_title="AI PayPal Invoice Generator", page_icon="💸")
st.title("💸 AI Freelance Quote & PayPal Checkout")
st.write("Paste messy client notes below. AI will structure the quote and create a real PayPal Sandbox payment link.")

# --- SIDEBAR CREDENTIALS ---
with st.sidebar:
    st.header("🔑 API Credentials")
    gemini_key = st.text_input("Gemini API Key", type="password")
    paypal_client_id = st.text_input("PayPal Sandbox Client ID", type="password")
    paypal_secret = st.text_input("PayPal Sandbox Secret", type="password")

# --- AI STRUCTURED OUTPUT SCHEMA ---
class InvoiceItem(BaseModel):
    name: str
    description: str
    quantity: int
    unit_price: float

class QuoteExtraction(BaseModel):
    client_email: str
    project_title: str
    items: list[InvoiceItem]

# --- PAYPAL HELPER FUNCTIONS ---
PAYPAL_BASE = "https://api-m." + "sandbox.paypal.com"

def get_paypal_token(client_id, secret):
    url = PAYPAL_BASE + "/v1/oauth2/token"
    res = requests.post(
        url,
        auth=(client_id.strip(), secret.strip()),
        data={"grant_type": "client_credentials"}
    )
    res.raise_for_status()
    return res.json()["access_token"]

def create_and_send_invoice(token, quote: QuoteExtraction):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    total_amount = sum(item.quantity * item.unit_price for item in quote.items)

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "description": f"{quote.project_title} (For: {quote.client_email})"[:127],
                "amount": {
                    "currency_code": "USD",
                    "value": f"{total_amount:.2f}"
                }
            }
        ],
        "application_context": {
            "brand_name": "AI Freelance Quote Assistant",
            "user_action": "PAY_NOW",
            "return_url": "https://example.com",
            "cancel_url": "https://example.com"
        }
    }

    res = requests.post(
        PAYPAL_BASE + "/v2/checkout/orders",
        headers=headers,
        json=payload
    )
    res.raise_for_status()
    data = res.json()

    for link in data.get("links", []):
        if link.get("rel") == "approve":
            return link["href"]

    return "https://www." + "://paypal.com" + data["id"]

# --- MAIN APP UI ---
sample_text = (
    "Hey! Can you build a 3-page landing site for my bakery? Let's say $400 for the design "
    "and $600 for development. Also add 2 hours of SEO setup at $75/hr. "
    "Send the bill to client-test@example.com."
)
user_notes = st.text_area("Client Message / Project Notes:", value=sample_text, height=150)

if st.button("✨ Generate Quote & PayPal Link", type="primary"):
    if not (gemini_key and paypal_client_id and paypal_secret):
        st.error("Please enter all 3 API keys in the left sidebar first!")
    else:
        try:
            with st.spinner("1/3 Analyzing project scope with Gemini AI..."):
                client = genai.Client(api_key=gemini_key.strip())
                prompt = f"Extract invoice line items, prices, and client email from this text. If no email is found, use buyer@example.com:\n\n{user_notes}"
                config = types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=QuoteExtraction,
                )

                models_to_try = [
                    "gemini-3.8-flash",
                    "gemini-3.5-flash",
                    "gemini-3.5-flash-lite",
                    "gemini-3.0-flash",
                    "gemini-3.8-flash"
                ]
                response = None
                last_err = None
                for model_id in models_to_try:
                    try:
                        response = client.models.generate_content(
                            model=model_id,
                            contents=prompt,
                            config=config,
                        )
                        break
                    except Exception as model_err:
                        last_err = model_err
                        if any(code in str(model_err) for code in ["503", "429", "404"]):
                            time.sleep(2)
                            continue
                        raise model_err
                if response is None:
                    raise last_err

                quote = QuoteExtraction.model_validate_json(response.text)

            st.subheader(f"📋 Extracted Quote: {quote.project_title}")
            total = sum(i.quantity * i.unit_price for i in quote.items)
            for i in quote.items:
                st.write(f"- **{i.name}** (x{i.quantity}): ${i.unit_price:.2f} each — *{i.description}*")
            st.info(f"**Total Amount:** ${total:.2f} | **Client:** {quote.client_email}")

            with st.spinner("2/3 Authenticating with PayPal Sandbox..."):
                token = get_paypal_token(paypal_client_id, paypal_secret)

            with st.spinner("3/3 Creating Live Sandbox Checkout Link..."):
                invoice_link = create_and_send_invoice(token, quote)

            st.success("🎉 PayPal Sandbox Checkout Link Created!")
            st.markdown(f"**Click to Open PayPal Sandbox Checkout:** [{invoice_link}]({invoice_link})")
            st.balloons()

        except Exception as e:
            st.error(f"Something went wrong: {e}")
