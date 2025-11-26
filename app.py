# webhook_sender_app.py
import streamlit as st
import requests
import json
from datetime import datetime

st.set_page_config(page_title="Webhook HTML/CSS Sender", layout="wide")

# --- configuration: list your webhooks here ---
WEBHOOK_BASE = "https://agentonline-u29564.vm.elestio.app/webhook-test"
WEBHOOKS = {
    "Newsletter": f"{WEBHOOK_BASE}/newsletter-trigger",
    "Landing Page": f"{WEBHOOK_BASE}/landingpage-trigger",
    "Business Letter": f"{WEBHOOK_BASE}/business-letter-trigger",
    "Email Sequence": f"{WEBHOOK_BASE}/email-sequence-trigger",
    "Invoice": f"{WEBHOOK_BASE}/invoice-trigger",
    "Business Contract": f"{WEBHOOK_BASE}/business-contract-trigger",
}

# --- helpers ---
def default_payload(html: str, title: str, metadata: dict, send_as: str, category: str):
    """
    Build JSON payload including a new 'category' field.
    """
    payload = {
        "title": title,
        "type": send_as,
        "category": category,        # ← ADDED HERE
        "html": html if send_as == "html" else None,
        "text": html if send_as == "text" else None,
        "metadata": metadata or {},
    }
    return {k: v for k, v in payload.items() if v is not None}

def pretty_json(obj):
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return str(obj)

# --- UI ---
st.title("Webhook HTML/CSS Sender")

col1, col2 = st.columns([2, 1])

with col1:
    webhook_choice = st.selectbox("Select webhook", list(WEBHOOKS.keys()))
    webhook_url = WEBHOOKS[webhook_choice]
    st.text_input("Webhook URL (editable)", value=webhook_url, key="webhook_url_input")

    send_as = st.radio("Send as", ["html", "text"], index=0)
    title = st.text_input("Title / Subject", value=f"{webhook_choice} - {datetime.utcnow().isoformat()[:19]}")

    st.markdown("### HTML / CSS Prompt")
    html_input = st.text_area(
        "Paste your HTML/CSS or prompt here",
        height=300
    )

    with st.expander("Metadata (JSON)", expanded=False):
        metadata_raw = st.text_area("metadata", height=100, value='{"source":"streamlit","author":"you"}')
        try:
            metadata = json.loads(metadata_raw)
        except:
            metadata = {}
            st.error("Invalid metadata JSON")

    with st.expander("Custom Headers (JSON)", expanded=False):
        headers_raw = st.text_area("headers", height=100, value='{"Content-Type":"application/json"}')
        try:
            custom_headers = json.loads(headers_raw)
        except:
            custom_headers = {"Content-Type": "application/json"}
            st.error("Invalid headers JSON")

with col2:
    st.markdown("### Payload Preview")

    payload = default_payload(
        html=html_input,
        title=title,
        metadata=metadata,
        send_as=send_as,
        category=webhook_choice,     # ← CATEGORY INCLUDED
    )

    st.code(pretty_json(payload), language="json")

    include_timestamp = st.checkbox("Include timestamp in metadata", True)
    if include_timestamp:
        payload.setdefault("metadata", {})
        payload["metadata"]["sent_at_utc"] = datetime.utcnow().isoformat()

    timeout_secs = st.number_input("Timeout (seconds)", 1, 60, 10)
    send_button = st.button("Send to Webhook", type="primary")

# Initialize history
if "history" not in st.session_state:
    st.session_state.history = []

# --- Send Request ---
if send_button:
    url_to_post = st.session_state.get("webhook_url_input").strip()

    try:
        resp = requests.post(url_to_post, json=payload, headers=custom_headers, timeout=timeout_secs)
        try:
            resp_body = resp.json()
        except:
            resp_body = resp.text

        st.session_state.history.insert(0, {
            "timestamp": datetime.utcnow().isoformat(),
            "webhook": url_to_post,
            "status_code": resp.status_code,
            "payload": payload,
            "response": resp_body,
        })

        if resp.status_code < 300:
            st.success(f"Success ({resp.status_code})")
        else:
            st.warning(f"Status: {resp.status_code}")

        st.subheader("Response")
        if isinstance(resp_body, (dict, list)):
            st.json(resp_body)
        else:
            st.code(str(resp_body))

    except Exception as e:
        st.error(f"Request failed: {e}")

# --- History ---
st.markdown("---")
st.header("History")
for i, rec in enumerate(st.session_state.history[:10]):
    with st.expander(f"{i+1}. {rec['timestamp']} → {rec['webhook']}"):
        st.code(pretty_json(rec["payload"]))
        st.code(pretty_json(rec.get("response", "")))
