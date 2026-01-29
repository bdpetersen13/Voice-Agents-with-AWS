import streamlit as st
import boto3
import json
from datetime import datetime, timedelta
from decimal import Decimal
import time

# Page config
st.set_page_config(
    page_title="Bella Vista Restaurant - Dashboard",
    page_icon="🍝",
    layout="wide"
)

# Initialize DynamoDB
@st.cache_resource
def init_dynamodb():
    return boto3.resource('dynamodb', region_name='us-east-1')

dynamodb = init_dynamodb()

# Helper function to convert Decimals
def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    else:
        return obj

# Fetch data functions
@st.cache_data(ttl=3)
def get_reservations():
    table = dynamodb.Table('Restaurant_Reservations')
    response = table.scan()
    return convert_decimals(response.get('Items', []))

@st.cache_data(ttl=3)
def get_waitlist():
    table = dynamodb.Table('Restaurant_Waitlist')
    response = table.scan()
    return convert_decimals(response.get('Items', []))

@st.cache_data(ttl=3)
def get_tables():
    table = dynamodb.Table('Restaurant_Tables')
    response = table.scan()
    return convert_decimals(response.get('Items', []))

@st.cache_data(ttl=3)
def get_orders():
    table = dynamodb.Table('Restaurant_Orders')
    response = table.scan()
    return convert_decimals(response.get('Items', []))

@st.cache_data(ttl=3)
def get_customers():
    table = dynamodb.Table('Restaurant_Customers')
    response = table.scan()
    return convert_decimals(response.get('Items', []))

# Main app
st.title("🍝 Bella Vista Restaurant - Live Dashboard")
st.markdown("Real-time view of reservations, waitlist, orders, and table status")

# Auto-refresh
st_autorefresh = st.empty()
with st_autorefresh:
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')} - Auto-refreshes every 3 seconds")

# Top metrics row
col1, col2, col3, col4, col5 = st.columns(5)

reservations = get_reservations()
waitlist = get_waitlist()
tables = get_tables()
orders = get_orders()
customers = get_customers()

# Today's reservations
today = datetime.now().date().strftime('%Y-%m-%d')
todays_reservations = [r for r in reservations if r.get('reservationDate') == today]
confirmed_today = [r for r in todays_reservations if r.get('status') == 'Confirmed']
seated_today = [r for r in todays_reservations if r.get('status') == 'Seated']

with col1:
    st.metric("📅 Today's Reservations", len(todays_reservations))

with col2:
    st.metric("✅ Confirmed", len(confirmed_today))

with col3:
    st.metric("🪑 Currently Seated", len(seated_today))

with col4:
    active_waitlist = [w for w in waitlist if w.get('status') in ['Waiting', 'Table Ready']]
    st.metric("⏳ Waitlist", len(active_waitlist))

with col5:
    active_orders = [o for o in orders if o.get('status') == 'In Progress']
    st.metric("🍽️ Active Orders", len(active_orders))

st.divider()

# Main content - tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📅 Reservations",
    "⏳ Waitlist",
    "🪑 Tables",
    "🍽️ Orders",
    "👥 Customers"
])

# TAB 1: Reservations
with tab1:
    st.subheader("Today's Reservations")

    # Filter options
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "Confirmed", "Seated", "Cancelled"],
            key="res_status_filter"
        )

    # Filter reservations
    if status_filter == "All":
        display_reservations = todays_reservations
    else:
        display_reservations = [r for r in todays_reservations if r.get('status') == status_filter]

    # Sort by time
    display_reservations.sort(key=lambda x: x.get('reservationTime', ''))

    if display_reservations:
        for res in display_reservations:
            status = res.get('status', 'Unknown')

            # Color code by status
            if status == 'Confirmed':
                bg_color = "#065f46"  # Green
                icon = "✅"
            elif status == 'Seated':
                bg_color = "#1e40af"  # Blue
                icon = "🪑"
            elif status == 'Cancelled':
                bg_color = "#7f1d1d"  # Red
                icon = "❌"
            else:
                bg_color = "#475569"  # Gray
                icon = "❓"

            with st.container():
                st.markdown(f"""
                <div style="background-color: {bg_color}; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <div style="font-size: 18px; font-weight: bold; margin-bottom: 5px;">
                                {icon} {res.get('customerName', 'Unknown')} - Party of {res.get('partySize', '?')}
                            </div>
                            <div style="font-size: 14px; opacity: 0.9;">
                                🕒 {res.get('reservationTime', 'N/A')} |
                                📞 {res.get('phone', 'N/A')} |
                                🆔 {res.get('reservationId', 'N/A')}
                            </div>
                            {f"<div style='font-size: 14px; opacity: 0.9; margin-top: 5px;'>🪑 Table: {res.get('tableId', 'Not assigned')}</div>" if res.get('tableId') else ""}
                            {f"<div style='font-size: 13px; opacity: 0.8; margin-top: 5px;'>📝 {res.get('specialRequests', '')}</div>" if res.get('specialRequests') else ""}
                            <div style="font-size: 12px; opacity: 0.7; margin-top: 5px;">
                                {f"👶 High chair needed" if res.get('highChairNeeded') else ""}
                                {" | " if res.get('highChairNeeded') and res.get('accessibilityNeeded') else ""}
                                {f"♿ Accessibility required" if res.get('accessibilityNeeded') else ""}
                                {f" | Prefers: {res.get('seatingPreference')}" if res.get('seatingPreference') else ""}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="background-color: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 5px; font-size: 12px;">
                                {status}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info(f"No {status_filter.lower()} reservations for today.")

    st.divider()

    # Upcoming reservations (next 7 days)
    st.subheader("Upcoming Reservations (Next 7 Days)")
    future_reservations = []
    for i in range(1, 8):
        future_date = (datetime.now().date() + timedelta(days=i)).strftime('%Y-%m-%d')
        future_res = [r for r in reservations if r.get('reservationDate') == future_date and r.get('status') == 'Confirmed']
        if future_res:
            future_reservations.extend(future_res)

    if future_reservations:
        for res in future_reservations[:10]:  # Show max 10
            st.markdown(f"""
            - **{res.get('reservationDate')}** at **{res.get('reservationTime')}** - {res.get('customerName')} (Party of {res.get('partySize')}) - ID: {res.get('reservationId')}
            """)
    else:
        st.info("No upcoming reservations in the next 7 days.")

# TAB 2: Waitlist
with tab2:
    st.subheader("Current Waitlist")

    if active_waitlist:
        # Sort by quoted time
        active_waitlist.sort(key=lambda x: x.get('quotedAt', ''))

        for entry in active_waitlist:
            wait_type = entry.get('type', 'Walk-in')
            status = entry.get('status', 'Waiting')

            # Color code
            if status == 'Table Ready':
                bg_color = "#15803d"  # Bright green
                icon = "✅"
            else:
                bg_color = "#b45309"  # Orange
                icon = "⏳"

            with st.container():
                st.markdown(f"""
                <div style="background-color: {bg_color}; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <div style="font-size: 18px; font-weight: bold; margin-bottom: 5px;">
                                {icon} {entry.get('customerName', 'Unknown')} - Party of {entry.get('partySize', '?')}
                            </div>
                            <div style="font-size: 14px; opacity: 0.9;">
                                📞 {entry.get('phone', 'N/A')} |
                                🆔 {entry.get('waitlistId', 'N/A')}
                            </div>
                            <div style="font-size: 14px; opacity: 0.9; margin-top: 5px;">
                                Type: {wait_type}
                                {f" | Est. Wait: {entry.get('estimatedWaitMinutes')} min" if entry.get('estimatedWaitMinutes') else ""}
                            </div>
                            {f"<div style='font-size: 14px; opacity: 0.9; margin-top: 5px;'>Requested: {entry.get('requestedTime')} on {entry.get('requestedDate')}</div>" if wait_type == 'Reservation Waitlist' else ""}
                            <div style="font-size: 12px; opacity: 0.7; margin-top: 5px;">
                                {f"👶 High chair" if entry.get('highChairNeeded') else ""}
                                {" | " if entry.get('highChairNeeded') and entry.get('accessibilityNeeded') else ""}
                                {f"♿ Accessibility" if entry.get('accessibilityNeeded') else ""}
                                {f" | {entry.get('seatingPreference')}" if entry.get('seatingPreference') else ""}
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="background-color: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 5px; font-size: 12px;">
                                {status}
                            </div>
                            <div style="font-size: 11px; opacity: 0.7; margin-top: 5px;">
                                Added: {datetime.fromisoformat(entry.get('quotedAt', datetime.now().isoformat())).strftime('%H:%M')}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.success("✅ No one currently on the waitlist!")

# TAB 3: Tables
with tab3:
    st.subheader("Table Status")

    # Group tables by location
    locations = {}
    for table in tables:
        location = table.get('location', 'Unknown')
        if location not in locations:
            locations[location] = []
        locations[location].append(table)

    # Display by location
    for location, location_tables in locations.items():
        st.markdown(f"### {location}")

        # Sort by table ID
        location_tables.sort(key=lambda x: x.get('tableId', ''))

        cols = st.columns(4)
        for idx, table in enumerate(location_tables):
            with cols[idx % 4]:
                status = table.get('status', 'Unknown')

                # Color by status
                if status == 'Available':
                    color = "green"
                    icon = "✅"
                elif status == 'Occupied':
                    color = "red"
                    icon = "🪑"
                else:
                    color = "gray"
                    icon = "❓"

                st.markdown(f"""
                <div style="border: 2px solid {color}; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 10px;">
                    <div style="font-size: 16px; font-weight: bold;">{icon} {table.get('tableId', 'Unknown')}</div>
                    <div style="font-size: 14px; margin-top: 5px;">Seats: {table.get('capacity', '?')}</div>
                    <div style="font-size: 12px; opacity: 0.8; margin-top: 3px;">
                        {f"👶" if table.get('hasHighChair') else ""}
                        {f"♿" if table.get('isAccessible') else ""}
                    </div>
                    <div style="font-size: 12px; margin-top: 5px; color: {color}; font-weight: bold;">{status}</div>
                </div>
                """, unsafe_allow_html=True)

    st.divider()

    # Table summary
    col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
    available_tables = [t for t in tables if t.get('status') == 'Available']
    with col_sum1:
        st.metric("Total Tables", len(tables))
    with col_sum2:
        st.metric("Available", len(available_tables))
    with col_sum3:
        high_chair_tables = [t for t in tables if t.get('hasHighChair')]
        st.metric("With High Chair", len(high_chair_tables))
    with col_sum4:
        accessible_tables = [t for t in tables if t.get('isAccessible')]
        st.metric("Accessible", len(accessible_tables))

# TAB 4: Orders
with tab4:
    st.subheader("Active Food Orders")

    if active_orders:
        for order in active_orders:
            with st.container():
                st.markdown(f"""
                <div style="background-color: #7c3aed; padding: 15px; border-radius: 8px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div style="flex: 1;">
                            <div style="font-size: 18px; font-weight: bold; margin-bottom: 5px;">
                                🍽️ {order.get('customerName', 'Unknown')} - Table {order.get('tableId', 'N/A')}
                            </div>
                            <div style="font-size: 14px; opacity: 0.9;">
                                🆔 Order: {order.get('orderId', 'N/A')} |
                                🕒 {datetime.fromisoformat(order.get('orderTime', datetime.now().isoformat())).strftime('%H:%M')}
                            </div>
                            <div style="font-size: 14px; margin-top: 10px;">
                                <strong>Items:</strong>
                            </div>
                """, unsafe_allow_html=True)

                # Display items
                items = order.get('items', [])
                for item in items:
                    st.markdown(f"""
                    <div style="font-size: 13px; margin-left: 10px; opacity: 0.95;">
                        • {item.get('quantity', 1)}x {item.get('name', 'Unknown')} - ${item.get('price', '0.00')}
                        {f"<br>&nbsp;&nbsp;&nbsp;<em style='font-size: 12px; opacity: 0.8;'>{item.get('specialInstructions')}</em>" if item.get('specialInstructions') else ""}
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown(f"""
                        </div>
                        <div style="text-align: right; min-width: 120px;">
                            <div style="font-size: 20px; font-weight: bold; color: #fbbf24;">
                                ${order.get('total', '0.00')}
                            </div>
                            <div style="font-size: 12px; opacity: 0.8; margin-top: 3px;">
                                Subtotal: ${order.get('subtotal', '0.00')}
                            </div>
                            <div style="font-size: 12px; opacity: 0.8;">
                                Tax: ${order.get('tax', '0.00')}
                            </div>
                            <div style="background-color: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 5px; font-size: 12px; margin-top: 10px;">
                                {order.get('status', 'Unknown')}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No active orders at the moment.")

    st.divider()

    # All orders today
    st.subheader("All Orders Today")
    todays_orders = [o for o in orders if o.get('orderDate') == today]
    if todays_orders:
        total_revenue = sum(float(o.get('total', 0)) for o in todays_orders)
        st.metric("💰 Today's Revenue", f"${total_revenue:.2f}")

        st.markdown("**Order History:**")
        for order in todays_orders[-5:]:  # Show last 5
            st.markdown(f"""
            - **{order.get('orderId')}** - {order.get('customerName')} (Table {order.get('tableId')}) - ${order.get('total')} - *{order.get('status')}*
            """)
    else:
        st.info("No orders placed today yet.")

# TAB 5: Customers
with tab5:
    st.subheader("Customer Database")

    # VIP customers
    vip_customers = [c for c in customers if c.get('vipStatus', False)]
    st.markdown(f"### ⭐ VIP Customers ({len(vip_customers)})")

    if vip_customers:
        for customer in vip_customers:
            with st.expander(f"{customer.get('name', 'Unknown')} - {customer.get('visitCount', 0)} visits"):
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.markdown(f"""
                    - **Customer ID:** {customer.get('customerId', 'N/A')}
                    - **Phone:** {customer.get('phone', 'N/A')}
                    - **Email:** {customer.get('email', 'N/A')}
                    - **Visit Count:** {customer.get('visitCount', 0)}
                    """)
                with col_c2:
                    allergies = customer.get('allergies', [])
                    preferences = customer.get('preferences', 'None')
                    st.markdown(f"""
                    - **Allergies:** {', '.join(allergies) if allergies else 'None'}
                    - **Preferences:** {preferences}
                    """)

    st.divider()

    # All customers
    st.markdown(f"### 👥 All Customers ({len(customers)})")
    for customer in customers:
        if not customer.get('vipStatus', False):
            st.markdown(f"""
            - **{customer.get('name', 'Unknown')}** - {customer.get('phone', 'N/A')} - {customer.get('visitCount', 0)} visits
            """)

# Footer
st.divider()
st.caption(f"🍝 Bella Vista Restaurant Dashboard | Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Auto-refresh every 3 seconds
time.sleep(3)
st.rerun()
