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
def default_payload(html: str, title: str, metadata: dict, send_as: str):
    """
    Build the default JSON payload with common fields.
    send_as: "html" or "text"
    """
    payload = {
        "title": title,
        "type": send_as,
        "html": html if send_as == "html" else None,
        "text": html if send_as == "text" else None,
        "metadata": metadata or {},
    }
    # Remove None keys for cleanliness
    return {k: v for k, v in payload.items() if v is not None}

def pretty_json(obj):
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return str(obj)

# --- UI ---
st.title("Webhook HTML/CSS Sender")
st.markdown(
    "Choose a webhook, paste an HTML/CSS prompt (or snippet), preview the payload, and POST it."
)

col1, col2 = st.columns([2, 1])

with col1:
    webhook_choice = st.selectbox("Select webhook", list(WEBHOOKS.keys()))
    webhook_url = WEBHOOKS[webhook_choice]
    st.text_input("Webhook URL (editable)", value=webhook_url, key="webhook_url_input")

    send_as = st.radio("Send as", options=["html", "text"], index=0, help="html: JSON has 'html' field. text: JSON has 'text' field.")
    title = st.text_input("Title / Subject (optional)", value=f"{webhook_choice} - {datetime.utcnow().isoformat()[:19]}")
    st.markdown("### HTML / CSS prompt")
    html_input = st.text_area(
        "Paste your HTML/CSS or prompt here",
        height=320,
        placeholder="<div class='hero'>Hello world</div>\n<style> .hero{ font-family: Arial; } </style>",
    )

    with st.expander("Advanced: Additional metadata (JSON)", expanded=False):
        metadata_raw = st.text_area("metadata (JSON)", height=120, value='{"source":"streamlit", "author":"you"}')
        try:
            metadata = json.loads(metadata_raw) if metadata_raw.strip() else {}
        except Exception as e:
            metadata = {}
            st.error(f"Metadata JSON parse error: {e}")

    with st.expander("Advanced: Custom headers (JSON)", expanded=False):
        headers_raw = st.text_area("Custom HTTP headers (JSON)", height=120, value='{"Content-Type":"application/json"}')
        try:
            custom_headers = json.loads(headers_raw) if headers_raw.strip() else {"Content-Type":"application/json"}
        except Exception as e:
            custom_headers = {"Content-Type":"application/json"}
            st.error(f"Headers JSON parse error: {e}")

with col2:
    st.markdown("### Payload preview")
    payload = default_payload(html_input, title, metadata if 'metadata' in locals() else {}, send_as)
    st.code(pretty_json(payload), language="json")

    st.markdown("### Options")
    include_timestamp = st.checkbox("Include timestamp in payload.metadata", value=True)
    if include_timestamp:
        payload.setdefault("metadata", {})
        payload["metadata"]["sent_at_utc"] = datetime.utcnow().isoformat()

    show_response = st.checkbox("Show full response body", value=True)
    timeout_secs = st.number_input("Request timeout (seconds)", min_value=1, max_value=60, value=10)
    st.markdown("---")
    send_button = st.button("Send to webhook", type="primary")

# Initialize session history
if "history" not in st.session_state:
    st.session_state.history = []

# When Send clicked
if send_button:
    url_to_post = st.session_state.get("webhook_url_input", webhook_url).strip()
    if not url_to_post:
        st.error("Webhook URL is empty.")
    else:
        try:
            # Ensure Content-Type present
            headers = custom_headers.copy() if 'custom_headers' in locals() else {"Content-Type": "application/json"}
            # Send POST
            resp = requests.post(url_to_post, json=payload, headers=headers, timeout=timeout_secs)
            try:
                resp_body = resp.json()
            except Exception:
                resp_body = resp.text

            record = {
                "timestamp": datetime.utcnow().isoformat(),
                "webhook": url_to_post,
                "status_code": resp.status_code,
                "payload": payload,
                "response": resp_body,
                "headers": dict(resp.headers),
            }
            st.session_state.history.insert(0, record)

            # Display results
            if 200 <= resp.status_code < 300:
                st.success(f"Success — HTTP {resp.status_code}")
            else:
                st.warning(f"HTTP {resp.status_code}")

            if show_response:
                st.subheader("Response")
                if isinstance(resp_body, (dict, list)):
                    st.json(resp_body)
                else:
                    st.code(str(resp_body))
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")
            # store failure
            st.session_state.history.insert(0, {
                "timestamp": datetime.utcnow().isoformat(),
                "webhook": url_to_post,
                "status_code": "error",
                "payload": payload,
                "response": str(e),
                "headers": {},
            })

# Show history
st.markdown("---")
st.header("Recent Sends (session)")
if not st.session_state.history:
    st.info("No sends yet in this session.")
else:
    for i, rec in enumerate(st.session_state.history[:10]):
        with st.expander(f"{i+1}. {rec['timestamp']} → {rec['webhook']} (status: {rec['status_code']})", expanded=(i==0)):
            st.markdown("**Payload:**")
            st.code(pretty_json(rec["payload"]), language="json")
            st.markdown("**Response:**")
            if isinstance(rec["response"], (dict, list)):
                st.json(rec["response"])
            else:
                st.code(str(rec["response"]))
            st.markdown("**Response headers:**")
            st.code(pretty_json(rec.get("headers", {})))

st.markdown("---")
st.caption("Made with ❤️ — sends JSON payloads to the selected webhook. Adjust metadata and headers in the advanced sections.")

