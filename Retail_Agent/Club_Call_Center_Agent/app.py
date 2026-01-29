import ast
from pathlib import Path
from typing import List, Dict, Any, Optional

import streamlit as st
from streamlit_autorefresh import st_autorefresh

# --------------- CONFIG ---------------

DEFAULT_LOG_PATH = "assistant.log"
MAX_EVENTS = 300

# Strings that indicate a tool usage line
TOOL_KEYWORDS = [
    "tooluse",
    "tool_use",
    "tool call",
    "tool_call",
    "tool:",
    "tool :",
    "tool use:",
    "tool use :",
    "toolinvocation",
]


# --------------- PARSING ---------------


def parse_timestamp_and_rest(line: str):
    """Parse a line into (timestamp_str, rest_of_line)."""
    parts = line.split(" ", 2)
    if len(parts) < 3:
        return None, line.strip()
    ts = f"{parts[0]} {parts[1]}"
    rest = parts[2].strip()
    return ts, rest


def parse_usage_dict(text: str) -> Optional[Dict[str, Any]]:
    """Extract the Python dict from a 'UsageEvent: {...}' line and parse it."""
    try:
        start = text.index("{")
    except ValueError:
        return None
    try:
        d = ast.literal_eval(text[start:])
    except Exception:
        return None
    return d


def is_tool_line(text: str) -> bool:
    """Heuristic: does this line look like tool usage?"""
    lower = text.lower()
    return any(k in lower for k in TOOL_KEYWORDS)


def extract_tool_message(text: str) -> str:
    """Try to strip leading 'Tool:' or similar; otherwise return full text."""
    stripped = text.strip()
    lower = stripped.lower()

    for prefix in ["tool:", "tool use:", "tool use", "tool call:", "tool call"]:
        if lower.startswith(prefix):
            parts = stripped.split(":", 1)
            if len(parts) == 2:
                return parts[1].strip() or stripped
    return stripped


def parse_line_to_event(line: str) -> Optional[Dict[str, Any]]:
    """Convert a single log line into a structured event."""
    line = line.rstrip("\n")
    if not line:
        return None

    stripped = line.strip()

    # Bare User/Assistant lines (NO timestamp)
    if stripped.startswith("User:"):
        msg = stripped.split("User:", 1)[1].strip()
        return {
            "type": "user",
            "time": None,
            "message": msg,
        }

    if stripped.startswith("Assistant:"):
        msg = stripped.split("Assistant:", 1)[1].strip()
        return {
            "type": "assistant",
            "time": None,
            "message": msg,
        }

    # Bare tool line without timestamp
    if is_tool_line(stripped):
        return {
            "type": "tool",
            "time": None,
            "message": extract_tool_message(stripped),
        }

    # Timestamped lines
    ts, rest = parse_timestamp_and_rest(line)

    if "User:" in rest:
        msg = rest.split("User:", 1)[1].strip()
        return {
            "type": "user",
            "time": ts,
            "message": msg,
        }

    if "Assistant:" in rest:
        msg = rest.split("Assistant:", 1)[1].strip()
        return {
            "type": "assistant",
            "time": ts,
            "message": msg,
        }

    if is_tool_line(rest):
        return {
            "type": "tool",
            "time": ts,
            "message": extract_tool_message(rest),
        }

    # Usage events
    if "UsageEvent:" in rest:
        usage_dict = parse_usage_dict(rest)
        input_tokens = output_tokens = total_tokens = None
        completion_id = None

        if usage_dict and "usageEvent" in usage_dict:
            ue = usage_dict["usageEvent"]
            completion_id = ue.get("completionId")
            total = ue.get("details", {}).get("total", {})
            inp = total.get("input", {})
            out = total.get("output", {})

            input_tokens = (inp.get("speechTokens", 0) or 0) + (
                inp.get("textTokens", 0) or 0
            )
            output_tokens = (out.get("speechTokens", 0) or 0) + (
                out.get("textTokens", 0) or 0
            )
            total_tokens = ue.get("totalTokens")

        return {
            "type": "usage",
            "time": ts,
            "completion_id": completion_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
        }

    # Completion start
    if "completionStart" in rest:
        return {"type": "event", "time": ts, "label": "Completion started"}

    # Barge-in
    if "Barge-in detected" in rest:
        return {
            "type": "event",
            "time": ts,
            "label": "Barge-in detected (caller interrupted)",
        }

    # Content markers
    if "Content start detected" in rest:
        return {"type": "event", "time": ts, "label": "Content start detected"}

    if "Content end" in rest:
        return {"type": "event", "time": ts, "label": "Content end"}

    return None


def parse_log_file(
    path: str, limit: Optional[int] = MAX_EVENTS
) -> List[Dict[str, Any]]:
    """Read the log and turn it into a list of structured events."""
    events: List[Dict[str, Any]] = []

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                ev = parse_line_to_event(line)
                if ev is not None:
                    events.append(ev)
    except FileNotFoundError:
        return []

    if limit is not None and len(events) > limit:
        events = events[-limit:]

    return events


# --------------- STREAMLIT UI ---------------

st.set_page_config(page_title="Club Call Center Agent – Live Calls", layout="wide")

# Auto-refresh every 3 seconds
st_autorefresh(interval=3000, key="log_viewer_autorefresh")

st.title("☎️ Club Call Center Agent – Live Call Monitoring")

with st.sidebar:
    st.header("Settings")
    log_path = st.text_input("Log file path", value=DEFAULT_LOG_PATH)
    show_events = st.checkbox(
        "Show event markers (Content start/end etc.)", value=False
    )

    st.markdown("---")
    st.markdown("### Call Center Services")
    st.markdown("""
    **Agent handles:**
    - 🕒 Store hours queries
    - 📦 Inventory checks
    - 🚗 Curbside order status
    - 📅 Appointment scheduling
    - 🎂 Specialty orders (cakes)
    - ✅ Appointment verification
    """)

log_file = Path(log_path)
if not log_file.exists():
    st.error(f"Log file not found at: `{log_file.resolve()}`")
    st.stop()

events = parse_log_file(str(log_file), limit=MAX_EVENTS)

if not events:
    st.warning("No parsed conversation events yet. Waiting for calls...")
    st.stop()

usage_events = [e for e in events if e["type"] == "usage"]
chat_events = [e for e in events if e["type"] in ("user", "assistant", "event", "tool")]

# ---- SUMMARY ----
st.markdown("### 📊 Call Center Metrics")

cols = st.columns(4)
with cols[0]:
    st.metric("Total Events", len(events))

with cols[1]:
    tool_events = [e for e in chat_events if e["type"] == "tool"]
    st.metric("Tool Calls", len(tool_events))

with cols[2]:
    latest_usage = usage_events[-1] if usage_events else None
    if latest_usage:
        st.metric("Total Tokens", latest_usage.get("total_tokens") or "–")
    else:
        st.metric("Total Tokens", "–")

with cols[3]:
    caller_interactions = [e for e in chat_events if e["type"] == "user"]
    st.metric("Caller Messages", len(caller_interactions))

st.markdown("---")

# ---- MAIN CONVERSATION VIEW ----
st.markdown("### 💬 Live Call Transcripts")

for ev in chat_events:
    etype = ev["type"]
    time_str = ev.get("time") or ""

    if etype == "user":
        st.markdown(
            f"""
<div style="padding: 10px 14px; margin-bottom: 10px; border-radius: 10px; background-color: #1e3a8a; border-left: 4px solid #3b82f6;">
  <div style="font-size: 0.75rem; opacity: 0.8; color: #93c5fd;">📞 Caller{(" • " + time_str) if time_str else ""}</div>
  <div style="margin-top: 6px; color: #e0e7ff; font-size: 0.95rem;">{ev['message']}</div>
</div>
""",
            unsafe_allow_html=True,
        )

    elif etype == "assistant":
        st.markdown(
            f"""
<div style="padding: 10px 14px; margin-bottom: 10px; border-radius: 10px; background-color: #0f172a; border-left: 4px solid #64748b;">
  <div style="font-size: 0.75rem; opacity: 0.8; color: #94a3b8;">🎙️ Agent{(" • " + time_str) if time_str else ""}</div>
  <div style="margin-top: 6px; color: #cbd5e1; font-size: 0.95rem;">{ev['message']}</div>
</div>
""",
            unsafe_allow_html=True,
        )

    elif etype == "tool":
        # Highlight different tool types with colors
        tool_msg = ev['message'].lower()

        if 'store' in tool_msg or 'hours' in tool_msg:
            bg_color = "#1e3a8a"  # Blue for hours
            icon = "🕒"
            label = "Store Hours"
        elif 'inventory' in tool_msg or 'stock' in tool_msg:
            bg_color = "#065f46"  # Green for inventory
            icon = "📦"
            label = "Inventory Check"
        elif 'curbside' in tool_msg or 'order' in tool_msg:
            bg_color = "#7c2d12"  # Orange for curbside
            icon = "🚗"
            label = "Curbside Order"
        elif 'appointment' in tool_msg or 'schedule' in tool_msg:
            bg_color = "#831843"  # Pink for appointments
            icon = "📅"
            label = "Appointment"
        elif 'cake' in tool_msg or 'specialty' in tool_msg:
            bg_color = "#581c87"  # Purple for cakes
            icon = "🎂"
            label = "Specialty Order"
        elif 'verify' in tool_msg or 'member' in tool_msg:
            bg_color = "#064e3b"  # Dark green for verification
            icon = "✅"
            label = "Member Verification"
        else:
            bg_color = "#374151"  # Default gray
            icon = "🔧"
            label = "Tool"

        st.markdown(
            f"""
<div style="padding: 8px 12px; margin-bottom: 8px; border-radius: 8px; background-color: {bg_color}; border-left: 3px solid rgba(255,255,255,0.3);">
  <div style="font-size: 0.75rem; opacity: 0.85; color: #d1d5db;">{icon} {label}{(" • " + time_str) if time_str else ""}</div>
  <div style="font-size: 0.88rem; margin-top: 4px; color: #f3f4f6; font-family: monospace;">{ev['message']}</div>
</div>
""",
            unsafe_allow_html=True,
        )

    elif etype == "event" and show_events:
        st.markdown(
            f"""
<div style="font-size: 0.72rem; opacity: 0.5; margin: 4px 0; color: #6b7280;">
  ⚡ Event: {ev.get('label', 'Event')}{(" • " + time_str) if time_str else ""}
</div>
""",
            unsafe_allow_html=True,
        )

# ---- USAGE (DROPDOWN) ----
if usage_events:
    st.markdown("---")
    with st.expander("📈 Token Usage Analytics (last 10 calls)"):
        for ev in usage_events[-10:]:
            time_str = ev.get("time") or ""
            st.markdown(
                f"""
<div style="padding: 8px 12px; margin-bottom: 8px; border-radius: 8px; background-color: #0c1222; border: 1px solid #1e293b;">
  <div style="font-size: 0.8rem; opacity: 0.7; color: #94a3b8;">Call Metrics{(" • " + time_str) if time_str else ""}</div>
  <div style="font-size: 0.88rem; margin-top: 6px; color: #e2e8f0;">
    <b style="color: #60a5fa;">Total: {ev.get('total_tokens') or '–'} tokens</b><br/>
    <span style="color: #86efac;">Input: {ev.get('input_tokens') or 0}</span> •
    <span style="color: #fbbf24;">Output: {ev.get('output_tokens') or 0}</span><br/>
    <span style="font-size: 0.75rem; opacity: 0.6;">Completion ID: <code>{ev.get('completion_id') or '-'}</code></span>
  </div>
</div>
""",
                unsafe_allow_html=True,
            )

# ---- FOOTER ----
st.markdown(
    """
<hr style="margin-top: 2.5rem; margin-bottom: 1rem; border: 0; border-top: 1px solid #374151;" />
<div style="font-size: 0.8rem; opacity: 0.65; color: #9ca3af; text-align: center;">
    <b>Denver Warehouse Club - Call Center Agent</b><br/>
    Real-time monitoring of voice calls • Handles hours, inventory, orders, and appointments<br/>
    Auto-refreshes every 3 seconds • Data from <code>assistant.log</code>
</div>
""",
    unsafe_allow_html=True,
)
