import streamlit as st
import anthropic
import random
import time
from datetime import datetime, timedelta

MOCK_CONVERSATIONS = [
    {
        "id": "c001", "customer": "Arif Rahman", "customer_id": "+8801711234567",
        "platform": "whatsapp", "status": "open",
        "preview": "Where is my order? I placed it 3 days ago",
        "updated": datetime.now() - timedelta(minutes=4),
        "messages": [
            {"role": "customer", "content": "Hi, I placed order #2041 three days ago. Where is it?", "time": "10:02 AM"},
            {"role": "ai", "content": "Hi Arif! Let me check order #2041 for you right away. 🔍", "time": "10:02 AM", "tool": "get_order_status"},
            {"role": "ai", "content": "Your order #2041 (Blue Denim Jacket, XL) was shipped yesterday via Sundarban Courier. Tracking: SB-88291. Expected delivery: tomorrow by 6 PM. 📦", "time": "10:02 AM"},
            {"role": "customer", "content": "Thanks! What if it doesn't arrive tomorrow?", "time": "10:05 AM"},
            {"role": "ai", "content": "No worries! If it doesn't arrive by tomorrow evening, message me and I'll escalate it to our logistics team and offer you a full refund or reship. 🤝", "time": "10:05 AM"},
        ]
    },
    {
        "id": "c002", "customer": "Nadia Islam", "customer_id": "nadia.islam",
        "platform": "instagram", "status": "escalated",
        "preview": "I received a damaged product, want refund",
        "updated": datetime.now() - timedelta(minutes=22),
        "messages": [
            {"role": "customer", "content": "I received my order but the kurta is torn at the sleeve. This is unacceptable!", "time": "9:41 AM"},
            {"role": "ai", "content": "I'm really sorry to hear that, Nadia! That's definitely not okay. Can you share a photo of the damage? I'll process a refund or replacement immediately. 🙏", "time": "9:41 AM"},
            {"role": "customer", "content": "I already sent the photo on Instagram. I want a FULL refund, not replacement.", "time": "9:44 AM"},
            {"role": "ai", "content": "Completely understood. I'm escalating this to our senior support team right now — they'll process your full refund within 24 hours. You'll get an SMS confirmation. ⚡", "time": "9:44 AM", "tool": "escalate_to_human"},
            {"role": "escalated", "content": "⚠️ Escalated to human agent — awaiting response", "time": "9:44 AM"},
        ]
    },
    {
        "id": "c003", "customer": "Karim Uddin", "customer_id": "karim.uddin.88",
        "platform": "messenger", "status": "resolved",
        "preview": "Do you have this in red color?",
        "updated": datetime.now() - timedelta(hours=1),
        "messages": [
            {"role": "customer", "content": "Do you have the Cotton Panjabi in red? I only see blue and white on the website.", "time": "8:15 AM"},
            {"role": "ai", "content": "Let me search our catalog for you! 🔍", "time": "8:15 AM", "tool": "search_products"},
            {"role": "ai", "content": "Great news! The Cotton Panjabi is available in Red (sizes M, L, XL) at ৳ 850. The red variant is actually our bestseller! Want me to send you the direct link? 🎉", "time": "8:15 AM"},
            {"role": "customer", "content": "Yes please! And can I get a discount?", "time": "8:17 AM"},
            {"role": "ai", "content": "I've sent you the link! 🔗 I can apply coupon SAVE10 for 10% off — that brings it to ৳ 765. Valid today only! Shall I reserve a size for you?", "time": "8:17 AM", "tool": "get_coupon"},
            {"role": "customer", "content": "Perfect, L please. Thanks!", "time": "8:20 AM"},
            {"role": "ai", "content": "Done! ✅ Your L size Red Cotton Panjabi is reserved. Use SAVE10 at checkout. Happy shopping! 🛒", "time": "8:20 AM"},
        ]
    },
    {
        "id": "c004", "customer": "Sumi Akter", "customer_id": "+8801822345678",
        "platform": "whatsapp", "status": "open",
        "preview": "What are your delivery charges?",
        "updated": datetime.now() - timedelta(minutes=2),
        "messages": [
            {"role": "customer", "content": "Hello, what are your delivery charges to Chittagong?", "time": "10:18 AM"},
            {"role": "ai", "content": "Hi Sumi! Delivery to Chittagong: ৳ 120 standard (3-5 days) or ৳ 200 express (next day). Free delivery on orders above ৳ 2000! 🚚", "time": "10:18 AM"},
        ]
    },
]

MOCK_PRODUCTS = [
    {"id": 101, "name": "Blue Denim Jacket", "price": "৳ 2,200", "stock": 14, "category": "Outerwear"},
    {"id": 102, "name": "Cotton Panjabi - Red", "price": "৳ 850", "stock": 8, "category": "Traditional"},
    {"id": 103, "name": "Printed Kurti Set", "price": "৳ 1,450", "stock": 0, "category": "Women"},
    {"id": 104, "name": "Casual Joggers", "price": "৳ 680", "stock": 23, "category": "Men"},
    {"id": 105, "name": "Embroidered Saree", "price": "৳ 3,800", "stock": 5, "category": "Women"},
]

MOCK_ORDERS_TODAY = [
    {"id": "#2048", "customer": "Rahim Ali", "total": "৳ 2,200", "status": "Processing"},
    {"id": "#2047", "customer": "Fatema B.", "total": "৳ 1,450", "status": "Shipped"},
    {"id": "#2046", "customer": "Jabir H.", "total": "৳ 680", "status": "Delivered"},
]


def render_shopai_tab():
    if "test_messages" not in st.session_state:
        st.session_state.test_messages = []
    if "selected_convo" not in st.session_state:
        st.session_state.selected_convo = None
    if "human_replies" not in st.session_state:
        st.session_state.human_replies = {}
    if "anthropic_key" not in st.session_state:
        st.session_state.anthropic_key = ""

    # Scoped Custom CSS
    st.markdown("""
    <style>
    .shopai-wrap {
        font-family: 'Space Grotesk', sans-serif;
    }
    .metric-card {
        background: #fff; border: 1px solid #e8e6e0; border-radius: 12px; padding: 20px 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .metric-value { font-size: 2.2rem; font-weight: 700; color: #0f0f0f; line-height: 1; }
    .metric-label { font-size: 0.78rem; font-weight: 500; color: #888; text-transform: uppercase; letter-spacing: 0.08em; margin-top: 6px; }
    .metric-delta { font-size: 0.82rem; font-weight: 500; color: #22c55e; margin-top: 4px; }
    .convo-card { background: #fff; border: 1px solid #e8e6e0; border-radius: 10px; padding: 14px 18px; margin-bottom: 10px; cursor: pointer; transition: box-shadow 0.15s; }
    .convo-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    .badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.04em; text-transform: uppercase; }
    .badge-whatsapp { background: #dcfce7; color: #15803d; }
    .badge-instagram { background: #fce7f3; color: #be185d; }
    .badge-messenger { background: #dbeafe; color: #1d4ed8; }
    .badge-resolved  { background: #f0fdf4; color: #16a34a; }
    .badge-open      { background: #fff7ed; color: #c2410c; }
    .badge-escalated { background: #fef9c3; color: #a16207; }
    .bubble-user { background: #f3f4f6; border-radius: 18px 18px 18px 4px; padding: 10px 14px; margin: 6px 0; max-width: 75%; font-size: 0.9rem; color: #1f2937; }
    .bubble-ai { background: #0f0f0f; color: #f9fafb; border-radius: 18px 18px 4px 18px; padding: 10px 14px; margin: 6px 0 6px auto; max-width: 75%; font-size: 0.9rem; text-align: right; }
    .bubble-human { background: #fef3c7; border-radius: 18px 18px 4px 18px; padding: 10px 14px; margin: 6px 0 6px auto; max-width: 75%; font-size: 0.9rem; text-align: right; }
    .section-header { font-size: 1.1rem; font-weight: 700; color: #0f0f0f; border-bottom: 2px solid #0f0f0f; padding-bottom: 8px; margin-bottom: 16px; letter-spacing: -0.01em; }
    .tool-tag { display: inline-block; background: #f0fdf4; border: 1px solid #bbf7d0; color: #15803d; border-radius: 6px; font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; padding: 2px 8px; margin: 2px; }
    .woo-panel { background: #fff; border: 1px solid #e8e6e0; border-left: 4px solid #7c3aed; border-radius: 8px; padding: 14px 16px; margin: 8px 0; font-size: 0.88rem; }
    .dot-green { display:inline-block; width:8px; height:8px; background:#22c55e; border-radius:50%; margin-right:6px; }
    .dot-yellow { display:inline-block; width:8px; height:8px; background:#f59e0b; border-radius:50%; margin-right:6px; }
    .chat-scroll { max-height: 420px; overflow-y: auto; padding: 8px; background: #f9f9f7; border-radius: 8px; border: 1px solid #e8e6e0; }
    </style>
    <div class="shopai-wrap">
    """, unsafe_allow_html=True)

    st.header("ShopAI CRM")
    
    with st.expander("System Configuration & Anthropic Keys", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**System Status**")
            st.markdown('<span class="dot-green"></span> AI Agent Online (Ready for test routing)', unsafe_allow_html=True)
            st.markdown('<span class="dot-green"></span> WooCommerce API (Mock linked)', unsafe_allow_html=True)
            st.markdown('<span class="dot-yellow"></span> Meta Webhook (Simulated callbacks)', unsafe_allow_html=True)
        with c2:
            st.markdown("**API Key**")
            st.session_state.anthropic_key = st.text_input("Anthropic API Key", type="password", value=st.session_state.anthropic_key, placeholder="sk-ant-...", help="Required for Claude-powered Test Agent")

    shop_tabs = st.tabs(["📊 Dashboard", "💬 Conversations", "🤖 Test Agent", "📦 Mock WooCommerce"])

    # ──────────────── DASHBOARD ────────────────
    with shop_tabs[0]:
        st.markdown(f"**Today · {datetime.now().strftime('%A, %d %B %Y')}**")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown('<div class="metric-card"><div class="metric-value">47</div><div class="metric-label">Conversations Today</div><div class="metric-delta">↑ 12 from yesterday</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="metric-card"><div class="metric-value">89%</div><div class="metric-label">AI Resolution Rate</div><div class="metric-delta">↑ 4% this week</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="metric-card"><div class="metric-value">2.8s</div><div class="metric-label">Avg Response Time</div><div class="metric-delta">↓ 0.4s improvement</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown('<div class="metric-card"><div class="metric-value">5</div><div class="metric-label">Needs Human Attention</div><div class="metric-delta" style="color:#f59e0b">↑ 2 escalated</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_l, col_r = st.columns([1.4, 1])
        with col_l:
            st.markdown('<div class="section-header">Platform Breakdown</div>', unsafe_allow_html=True)
            import pandas as pd
            df = pd.DataFrame({"Platform": ["WhatsApp", "Instagram", "Messenger"], "Conversations": [28, 12, 7]}).set_index("Platform")
            st.bar_chart(df, color="#0f0f0f")

        with col_r:
            st.markdown('<div class="section-header">Recent Orders</div>', unsafe_allow_html=True)
            for o in MOCK_ORDERS_TODAY:
                color = "#22c55e" if o["status"] == "Delivered" else "#f59e0b" if o["status"] == "Shipped" else "#3b82f6"
                st.markdown(f"""
                <div class="woo-panel">
                    <b>{o['id']}</b> · {o['customer']}<br>
                    <span style="color:#888;font-size:0.82rem">{o['total']}</span>
                    <span style="float:right;color:{color};font-size:0.8rem;font-weight:600">{o['status']}</span>
                </div>""", unsafe_allow_html=True)

        st.markdown('<div class="section-header" style="margin-top:20px">AI Tool Usage Today</div>', unsafe_allow_html=True)
        t_cols = st.columns(4)
        tools_used = [("get_order_status", 31, "#dbeafe"), ("search_products", 18, "#f0fdf4"), ("escalate_to_human", 5, "#fef9c3"), ("create_refund", 3, "#fce7f3")]
        for i, (tool, count, bg) in enumerate(tools_used):
            with t_cols[i]:
                st.markdown(f"""
                <div class="metric-card" style="background:{bg}">
                    <div style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;color:#555;margin-bottom:6px">{tool}</div>
                    <div class="metric-value" style="font-size:1.8rem">{count}×</div>
                    <div class="metric-label">calls today</div>
                </div>""", unsafe_allow_html=True)

    # ──────────────── CONVERSATIONS ────────────────
    with shop_tabs[1]:
        f1, f2, _ = st.columns([1, 1, 3])
        with f1:
            status_f = st.selectbox("Status", ["All", "Open", "Escalated", "Resolved"])
        with f2:
            platform_f = st.selectbox("Platform", ["All", "WhatsApp", "Instagram", "Messenger"])

        filtered = MOCK_CONVERSATIONS
        if status_f != "All":
            filtered = [c for c in filtered if c["status"] == status_f.lower()]
        if platform_f != "All":
            filtered = [c for c in filtered if c["platform"] == platform_f.lower()]

        c_list, c_det = st.columns([1, 1.6])
        with c_list:
            st.markdown(f'<div class="section-header">{len(filtered)} Conversations</div>', unsafe_allow_html=True)
            for c in filtered:
                b_plat = f'<span class="badge badge-{c["platform"]}">{c["platform"]}</span>'
                b_stat = f'<span class="badge badge-{c["status"]}">{c["status"]}</span>'
                mins_ago = int((datetime.now() - c["updated"]).total_seconds() / 60)
                time_str = f"{mins_ago}m ago" if mins_ago < 60 else f"{mins_ago//60}h ago"

                if st.button(f"{'🟢' if c['status']=='open' else '🟡' if c['status']=='escalated' else '✅'} {c['customer']} · {time_str}", key=f"b_{c['id']}", use_container_width=True):
                    st.session_state.selected_convo = c["id"]

                st.markdown(f"""<div style="padding:0 4px 8px 4px;font-size:0.8rem;color:#888;border-bottom:1px solid #f0ede8;margin-bottom:4px">
                    {b_plat} {b_stat}<br><span style="margin-top:4px;display:block">{c['preview'][:50]}…</span></div>""", unsafe_allow_html=True)

        with c_det:
            selected = next((c for c in MOCK_CONVERSATIONS if c["id"] == st.session_state.selected_convo), None)
            if not selected:
                st.markdown('<div style="height:400px;display:flex;align-items:center;justify-content:center;color:#bbb;font-size:1rem;border:1px dashed #e0ddd8;border-radius:12px">← Select a conversation</div>', unsafe_allow_html=True)
            else:
                st.markdown(f"**{selected['customer']}** &nbsp; <span class='badge badge-{selected['platform']}'>{selected['platform']}</span> <span class='badge badge-{selected['status']}'>{selected['status']}</span>", unsafe_allow_html=True)
                st.markdown(f'<div style="color:#888;font-size:0.8rem;margin-bottom:12px">{selected["customer_id"]}</div>', unsafe_allow_html=True)
                
                chat_html = '<div class="chat-scroll">'
                for m in selected["messages"]:
                    t, tool = m.get("time", ""), m.get("tool", "")
                    tool_h = f'<br><span class="tool-tag">⚙ {tool}()</span>' if tool else ""
                    if m["role"] == "customer":
                        chat_html += f'<div><div class="bubble-user">{m["content"]}{tool_h}</div><div style="font-size:0.7rem;color:#aaa;margin-bottom:4px">{t}</div></div>'
                    elif m["role"] == "ai":
                        chat_html += f'<div style="text-align:right"><div class="bubble-ai">{m["content"]}{tool_h}</div><div style="font-size:0.7rem;color:#aaa;margin-bottom:4px;text-align:right">AI · {t}</div></div>'
                    elif m["role"] == "escalated":
                        chat_html += f'<div style="text-align:center;color:#a16207;font-size:0.8rem;padding:8px;background:#fef9c3;border-radius:8px;margin:8px 0">{m["content"]}</div>'
                chat_html += '</div>'
                st.markdown(chat_html, unsafe_allow_html=True)

                if selected["status"] == "escalated":
                    st.markdown("**🧑 Human Agent Reply**")
                    human_reply = st.text_area("Type your reply", key=f"reply_{selected['id']}", height=80)
                    if st.button("📤 Send as Human Agent", key=f"send_{selected['id']}"):
                        st.success("✅ Reply sent! (In production this calls Meta Cloud API)")
                elif selected["status"] == "open":
                    st.info("🤖 AI agent is handling this conversation.")
                    st.button("👤 Take Over from AI", key=f"takeover_{selected['id']}")

    # ──────────────── TEST AGENT ────────────────
    with shop_tabs[2]:
        cc, ci = st.columns([1.6, 1])
        with ci:
            st.markdown('<div class="section-header">Agent Config</div>', unsafe_allow_html=True)
            persona = st.text_area("System Prompt", height=120, value="You are a helpful customer support agent for a Bangladeshi e-commerce clothing store.\nYou have access to order tracking, product catalog, and can process refunds. Be friendly, brief (this is WhatsApp), and use occasional emojis.\nAlways respond in the same language the customer uses.")
            if st.button("🗑️ Clear Chat"): st.session_state.test_messages = []; st.rerun()
            st.markdown('<div class="section-header" style="margin-top:16px">Try These</div>', unsafe_allow_html=True)
            for s in ["Where is my order #2041?", "Do you have kurtas in XL?", "Give me a discount code"]:
                if st.button(s, use_container_width=True):
                    st.session_state.test_messages.append({"role": "user", "content": s}); st.rerun()
        
        with cc:
            st.markdown('<div class="section-header">Chat Simulator</div>', unsafe_allow_html=True)
            for msg in st.session_state.test_messages:
                st.chat_message(msg["role"]).write(msg["content"])
            
            user_input = st.chat_input("Type a customer message to test...")
            if user_input:
                st.session_state.test_messages.append({"role": "user", "content": user_input})
                st.chat_message("user").write(user_input)

                api_key = st.session_state.anthropic_key
                if not api_key:
                    mock_res = {"order": "I've checked your order! expected tomorrow by 6 PM 📦", "deliver": "Delivery charges: ৳ 120 standard 🚚", "refund": "Full refund initiated. 💳", "discount": "Use SAVE10! 🎉"}
                    reply = next((v for k, v in mock_res.items() if k in user_input.lower()), "Thanks for reaching out! (Add your Anthropic API key in Settings for real AI)")
                    time.sleep(0.8)
                    st.session_state.test_messages.append({"role": "assistant", "content": reply})
                    st.chat_message("assistant").write(reply)
                else:
                    try:
                        client = anthropic.Anthropic(api_key=api_key)
                        tools = [
                            {"name": "get_order_status", "description": "Get order status", "input_schema": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": []}},
                            {"name": "search_products", "description": "Search the catalog", "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}
                        ]
                        api_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.test_messages]
                        with st.chat_message("assistant"):
                            with st.spinner("Agent thinking..."):
                                while True:
                                    response = client.messages.create(model="claude-3-haiku-20240307", max_tokens=600, system=persona, tools=tools, messages=api_messages)
                                    if response.stop_reason == "end_turn":
                                        final_text = next((b.text for b in response.content if hasattr(b, "text")), "")
                                        st.write(final_text); st.session_state.test_messages.append({"role": "assistant", "content": final_text})
                                        break
                                    if response.stop_reason == "tool_use":
                                        tb = next(b for b in response.content if b.type == "tool_use")
                                        st.markdown(f'<span class="tool-tag">⚙ {tb.name}()</span>', unsafe_allow_html=True)
                                        api_messages.append({"role": "assistant", "content": response.content})
                                        api_messages.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": tb.id, "content": "{'status': 'success'}"}]})
                    except Exception as e:
                        st.error(f"API Error: {e}")
                st.rerun()

    # ──────────────── MOCK WOOCOMMERCE ────────────────
    with shop_tabs[3]:
        search = st.text_input("Search products catalog")
        products = [p for p in MOCK_PRODUCTS if search.lower() in p["name"].lower()] if search else MOCK_PRODUCTS
        for p in products:
            sc = "#22c55e" if p["stock"] > 5 else "#f59e0b" if p["stock"] > 0 else "#ef4444"
            st.markdown(f"<div class='woo-panel'><b>#{p['id']} · {p['name']}</b> <span style='float:right'>{p['price']}</span><br><span style='font-size:0.8rem;color:#888'>{p['category']}</span> <span style='float:right;color:{sc}'>{p['stock']} in stock</span></div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
