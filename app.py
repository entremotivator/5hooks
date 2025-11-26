# webhook_sender_simple.py
import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Simple Webhook Text Sender", layout="wide")

# --------------------------
# REAL WEBHOOKS (NO -test)
# --------------------------
WEBHOOK_BASE = "https://agentonline-u29564.vm.elestio.app/webhook"
WEBHOOKS = {
    "Newsletter": f"{WEBHOOK_BASE}/newsletter-trigger",
    "Landing Page": f"{WEBHOOK_BASE}/landingpage-trigger",
    "Business Letter": f"{WEBHOOK_BASE}/business-letter-trigger",
    "Email Sequence": f"{WEBHOOK_BASE}/email-sequence-trigger",
    "Invoice": f"{WEBHOOK_BASE}/invoice-trigger",
    "Business Contract": f"{WEBHOOK_BASE}/business-contract-trigger",
}

# --------------------------
# UI
# --------------------------
st.title("Simple Webhook Text Sender")

webhook_choice = st.selectbox("Select webhook", list(WEBHOOKS.keys()))
webhook_url = st.text_input("Webhook URL", value=WEBHOOKS[webhook_choice])

title = st.text_input("Title", value=f"{webhook_choice} - {datetime.utcnow().isoformat()[:19]}")

text_input = st.text_area(
    "Enter the text you want to send",
    height=300
)

send_button = st.button("Send", type="primary")

# History memory
if "history" not in st.session_state:
    st.session_state.history = []

# --------------------------
# SEND REQUEST
# --------------------------
if send_button:
    payload = {
        "title": title,
        "type": "text",
        "text": text_input,
        "category": webhook_choice,
    }

    try:
        resp = requests.post(webhook_url, json=payload, timeout=20)

        # raw response text only
        try:
            resp_body = resp.text
        except:
            resp_body = ""

        # store in history
        st.session_state.history.insert(0, {
            "timestamp": datetime.utcnow().isoformat(),
            "webhook": webhook_url,
            "status_code": resp.status_code,
            "payload": payload,
            "response": resp_body,
        })

        st.subheader("Response")
        st.code(resp_body)

        if resp.status_code < 300:
            st.success(f"Sent! Status {resp.status_code}")
        else:
            st.warning(f"Status {resp.status_code}")

    except Exception as e:
        st.error(f"Request failed: {e}")

# --------------------------
# HISTORY
# --------------------------
st.markdown("---")
st.header("History")

for i, rec in enumerate(st.session_state.history[:10]):
    with st.expander(f"{i+1}. {rec['timestamp']} → {rec['webhook']}"):
        st.code(str(rec["payload"]))
        st.code(str(rec["response"]))
