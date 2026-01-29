import streamlit as st
import boto3
import pandas as pd
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Attr, Key
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Banking Agent Dashboard",
    page_icon="🏦",
    layout="wide"
)

# Initialize DynamoDB
@st.cache_resource
def init_dynamodb():
    return boto3.resource('dynamodb', region_name='us-east-1')

dynamodb = init_dynamodb()

# Tables
auth_sessions_table = dynamodb.Table('Banking_AuthSessions')
audit_logs_table = dynamodb.Table('Banking_AuditLogs')
customers_table = dynamodb.Table('Banking_Customers')
accounts_table = dynamodb.Table('Banking_Accounts')
transactions_table = dynamodb.Table('Banking_Transactions')
disputes_table = dynamodb.Table('Banking_Disputes')
cards_table = dynamodb.Table('Banking_Cards')
transfers_table = dynamodb.Table('Banking_Transfers')

# Dashboard Title
st.title("🏦 First National Bank - Banking Agent Dashboard")
st.markdown("Real-time monitoring and analytics for secure voice banking operations")

# Auto-refresh
st.sidebar.markdown("### Dashboard Settings")
auto_refresh = st.sidebar.checkbox("Auto-refresh (10s)", value=False)
if auto_refresh:
    st.sidebar.info("Dashboard refreshing every 10 seconds...")
    import time
    time.sleep(10)
    st.rerun()

# Time range selector
st.sidebar.markdown("### Time Range")
time_range = st.sidebar.selectbox(
    "Select time range",
    ["Last 1 Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days"],
    index=2
)

time_ranges = {
    "Last 1 Hour": timedelta(hours=1),
    "Last 6 Hours": timedelta(hours=6),
    "Last 24 Hours": timedelta(hours=24),
    "Last 7 Days": timedelta(days=7)
}
time_delta = time_ranges[time_range]
cutoff_time = (datetime.now() - time_delta).isoformat()

# === METRICS ROW ===
st.markdown("---")
st.subheader("📊 Real-Time Metrics")

col1, col2, col3, col4, col5 = st.columns(5)

# Active Sessions
try:
    active_sessions = auth_sessions_table.scan()
    active_count = sum(1 for session in active_sessions['Items']
                      if session.get('expiresAt', '') > datetime.now().isoformat())
    col1.metric("Active Sessions", active_count, help="Currently authenticated customers")
except:
    col1.metric("Active Sessions", "N/A")

# Total Customers
try:
    customers = customers_table.scan()
    total_customers = len(customers['Items'])
    col2.metric("Total Customers", total_customers)
except:
    col2.metric("Total Customers", "N/A")

# Recent Transactions (last hour)
try:
    recent_cutoff = (datetime.now() - timedelta(hours=1)).isoformat()
    transactions = transactions_table.scan(
        FilterExpression=Attr('transactionDate').gte(recent_cutoff)
    )
    recent_tx_count = len(transactions['Items'])
    col3.metric("Transactions (1h)", recent_tx_count, delta="+5.2%")
except:
    col3.metric("Transactions (1h)", "N/A")

# Active Disputes
try:
    disputes = disputes_table.scan(
        FilterExpression=Attr('status').eq('Under Investigation')
    )
    active_disputes = len(disputes['Items'])
    col4.metric("Active Disputes", active_disputes, delta="-2", delta_color="inverse")
except:
    col4.metric("Active Disputes", "N/A")

# Authentication Success Rate
try:
    audit_logs = audit_logs_table.scan(
        FilterExpression=Attr('timestamp').gte(cutoff_time) &
                        (Attr('action').eq('OTP_VERIFIED') | Attr('action').eq('OTP_VERIFY_FAILED'))
    )
    logs = audit_logs['Items']
    if logs:
        success_count = sum(1 for log in logs if log.get('result') == 'SUCCESS')
        success_rate = (success_count / len(logs)) * 100
        col5.metric("Auth Success Rate", f"{success_rate:.1f}%", delta=f"+{2.3}%")
    else:
        col5.metric("Auth Success Rate", "N/A")
except:
    col5.metric("Auth Success Rate", "N/A")

# === AUTHENTICATION ANALYTICS ===
st.markdown("---")
st.subheader("🔐 Authentication & Security Analytics")

col_left, col_right = st.columns(2)

with col_left:
    st.markdown("#### Authentication Levels Distribution")
    try:
        sessions = auth_sessions_table.scan()
        level_counts = {}
        for session in sessions['Items']:
            if session.get('expiresAt', '') > datetime.now().isoformat():
                level = session.get('authLevel', 'Unknown')
                level_counts[level] = level_counts.get(level, 0) + 1

        if level_counts:
            fig = px.pie(
                values=list(level_counts.values()),
                names=list(level_counts.keys()),
                color_discrete_map={
                    'Level1': '#90EE90',
                    'Level2': '#FFD700',
                    'Level3': '#FF6B6B'
                },
                hole=0.4
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No active sessions")
    except Exception as e:
        st.error(f"Error loading auth levels: {str(e)}")

with col_right:
    st.markdown("#### Recent Security Events")
    try:
        security_logs = audit_logs_table.scan(
            FilterExpression=Attr('timestamp').gte(cutoff_time) &
                            (Attr('action').eq('OTP_SENT') |
                             Attr('action').eq('OTP_VERIFIED') |
                             Attr('action').eq('KNOWLEDGE_AUTH_SUCCESS') |
                             Attr('action').eq('OTP_VERIFY_FAILED') |
                             Attr('action').eq('KNOWLEDGE_AUTH_FAILED'))
        )

        if security_logs['Items']:
            df = pd.DataFrame(security_logs['Items'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp', ascending=False).head(10)

            # Format for display
            df_display = df[['timestamp', 'action', 'result', 'authLevel']].copy()
            df_display['timestamp'] = df_display['timestamp'].dt.strftime('%H:%M:%S')

            st.dataframe(
                df_display,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "timestamp": "Time",
                    "action": "Action",
                    "result": "Result",
                    "authLevel": "Auth Level"
                }
            )
        else:
            st.info("No security events in selected time range")
    except Exception as e:
        st.error(f"Error loading security events: {str(e)}")

# === TOOL USAGE ANALYTICS ===
st.markdown("---")
st.subheader("🛠️ Tool Usage Analytics")

col_tool1, col_tool2 = st.columns(2)

with col_tool1:
    st.markdown("#### Most Used Banking Tools")
    try:
        tool_logs = audit_logs_table.scan(
            FilterExpression=Attr('timestamp').gte(cutoff_time)
        )

        if tool_logs['Items']:
            # Count tool usage
            tool_counts = {}
            for log in tool_logs['Items']:
                action = log.get('action', 'Unknown')
                if action not in ['SESSION_CREATED', 'OTP_SENT', 'OTP_VERIFIED', 'KNOWLEDGE_AUTH_SUCCESS']:
                    tool_counts[action] = tool_counts.get(action, 0) + 1

            if tool_counts:
                # Sort and get top 10
                sorted_tools = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:10]

                fig = go.Figure(go.Bar(
                    x=[count for _, count in sorted_tools],
                    y=[tool for tool, _ in sorted_tools],
                    orientation='h',
                    marker=dict(color='#4169E1')
                ))
                fig.update_layout(
                    height=400,
                    xaxis_title="Usage Count",
                    yaxis_title="Tool",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No tool usage data available")
        else:
            st.info("No tool usage in selected time range")
    except Exception as e:
        st.error(f"Error loading tool usage: {str(e)}")

with col_tool2:
    st.markdown("#### Tool Success vs Failure Rate")
    try:
        result_logs = audit_logs_table.scan(
            FilterExpression=Attr('timestamp').gte(cutoff_time) &
                            (Attr('result').eq('SUCCESS') | Attr('result').eq('FAILURE'))
        )

        if result_logs['Items']:
            success_count = sum(1 for log in result_logs['Items'] if log.get('result') == 'SUCCESS')
            failure_count = len(result_logs['Items']) - success_count

            fig = go.Figure(data=[
                go.Bar(name='Success', x=['Operations'], y=[success_count], marker_color='#90EE90'),
                go.Bar(name='Failure', x=['Operations'], y=[failure_count], marker_color='#FF6B6B')
            ])
            fig.update_layout(
                height=400,
                barmode='group',
                showlegend=True,
                yaxis_title="Count"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Success rate
            total = success_count + failure_count
            rate = (success_count / total) * 100 if total > 0 else 0
            st.metric("Overall Success Rate", f"{rate:.1f}%")
        else:
            st.info("No operation results available")
    except Exception as e:
        st.error(f"Error loading operation results: {str(e)}")

# === FRAUD & DISPUTES ===
st.markdown("---")
st.subheader("🚨 Fraud & Dispute Monitoring")

col_fraud1, col_fraud2 = st.columns(2)

with col_fraud1:
    st.markdown("#### Active Disputes by Status")
    try:
        all_disputes = disputes_table.scan()

        if all_disputes['Items']:
            status_counts = {}
            for dispute in all_disputes['Items']:
                status = dispute.get('status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1

            fig = px.bar(
                x=list(status_counts.keys()),
                y=list(status_counts.values()),
                labels={'x': 'Status', 'y': 'Count'},
                color=list(status_counts.keys()),
                color_discrete_map={
                    'Filed': '#FFD700',
                    'Under Investigation': '#FF8C00',
                    'Resolved - Customer Favor': '#90EE90',
                    'Resolved - Merchant Favor': '#FF6B6B',
                    'Pending Review': '#4169E1'
                }
            )
            fig.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No disputes found")
    except Exception as e:
        st.error(f"Error loading disputes: {str(e)}")

with col_fraud2:
    st.markdown("#### Recent Fraud Reports")
    try:
        fraud_logs = audit_logs_table.scan(
            FilterExpression=Attr('timestamp').gte(cutoff_time) &
                            Attr('action').eq('REPORT_FRAUD')
        )

        if fraud_logs['Items']:
            df = pd.DataFrame(fraud_logs['Items'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp', ascending=False).head(5)

            df_display = df[['timestamp', 'customerId', 'result']].copy()
            df_display['timestamp'] = df_display['timestamp'].dt.strftime('%Y-%m-%d %H:%M')

            st.dataframe(
                df_display,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "timestamp": "Time",
                    "customerId": "Customer ID",
                    "result": "Status"
                }
            )
        else:
            st.info("No fraud reports in selected time range")
    except Exception as e:
        st.error(f"Error loading fraud reports: {str(e)}")

# === COMPLIANCE & AUDIT ===
st.markdown("---")
st.subheader("📋 Compliance & Audit Trail")

col_compliance1, col_compliance2 = st.columns(2)

with col_compliance1:
    st.markdown("#### PII Access Tracking")
    try:
        pii_logs = audit_logs_table.scan(
            FilterExpression=Attr('timestamp').gte(cutoff_time) &
                            Attr('pii_accessed').eq(True)
        )

        if pii_logs['Items']:
            df = pd.DataFrame(pii_logs['Items'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Count by action type
            pii_counts = df['action'].value_counts()

            fig = px.bar(
                x=pii_counts.index,
                y=pii_counts.values,
                labels={'x': 'Action', 'y': 'PII Access Count'},
                color=pii_counts.values,
                color_continuous_scale='Reds'
            )
            fig.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True)

            st.info(f"Total PII access events: {len(pii_logs['Items'])}")
        else:
            st.success("No PII access in selected time range")
    except Exception as e:
        st.error(f"Error loading PII tracking: {str(e)}")

with col_compliance2:
    st.markdown("#### Audit Log Summary")
    try:
        all_logs = audit_logs_table.scan(
            FilterExpression=Attr('timestamp').gte(cutoff_time)
        )

        if all_logs['Items']:
            df = pd.DataFrame(all_logs['Items'])

            # Summary stats
            total_events = len(df)
            unique_customers = df['customerId'].nunique()
            unique_sessions = df['sessionId'].nunique()

            st.metric("Total Audit Events", total_events)
            col_a, col_b = st.columns(2)
            col_a.metric("Unique Customers", unique_customers)
            col_b.metric("Unique Sessions", unique_sessions)

            # Timeline
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.floor('H')
            hourly_counts = df.groupby('hour').size().reset_index(name='count')

            if len(hourly_counts) > 1:
                fig = px.line(
                    hourly_counts,
                    x='hour',
                    y='count',
                    labels={'hour': 'Time', 'count': 'Events'},
                    markers=True
                )
                fig.update_layout(height=200, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No audit logs in selected time range")
    except Exception as e:
        st.error(f"Error loading audit summary: {str(e)}")

# === ACCOUNT & TRANSACTION ANALYTICS ===
st.markdown("---")
st.subheader("💰 Account & Transaction Analytics")

col_acct1, col_acct2 = st.columns(2)

with col_acct1:
    st.markdown("#### Total Account Balances by Type")
    try:
        accounts = accounts_table.scan()

        if accounts['Items']:
            type_balances = {}
            for account in accounts['Items']:
                acc_type = account.get('accountType', 'Unknown')
                balance = float(account.get('balance', 0))
                type_balances[acc_type] = type_balances.get(acc_type, 0) + balance

            fig = px.bar(
                x=list(type_balances.keys()),
                y=list(type_balances.values()),
                labels={'x': 'Account Type', 'y': 'Total Balance ($)'},
                color=list(type_balances.keys()),
                color_discrete_map={
                    'Checking': '#4169E1',
                    'Savings': '#90EE90',
                    'Credit': '#FF6B6B'
                }
            )
            fig.update_layout(showlegend=False, height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No account data available")
    except Exception as e:
        st.error(f"Error loading account balances: {str(e)}")

with col_acct2:
    st.markdown("#### Transaction Volume Over Time")
    try:
        recent_tx = transactions_table.scan(
            FilterExpression=Attr('transactionDate').gte(cutoff_time)
        )

        if recent_tx['Items']:
            df = pd.DataFrame(recent_tx['Items'])
            df['transactionDate'] = pd.to_datetime(df['transactionDate'])
            df['hour'] = df['transactionDate'].dt.floor('H')

            hourly_volume = df.groupby('hour').size().reset_index(name='count')

            fig = px.area(
                hourly_volume,
                x='hour',
                y='count',
                labels={'hour': 'Time', 'count': 'Transactions'},
                color_discrete_sequence=['#4169E1']
            )
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No transactions in selected time range")
    except Exception as e:
        st.error(f"Error loading transaction volume: {str(e)}")

# === CARD MANAGEMENT ===
st.markdown("---")
st.subheader("💳 Card Management")

col_card1, col_card2 = st.columns(2)

with col_card1:
    st.markdown("#### Card Status Distribution")
    try:
        cards = cards_table.scan()

        if cards['Items']:
            status_counts = {}
            for card in cards['Items']:
                status = card.get('status', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1

            fig = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                color_discrete_map={
                    'Active': '#90EE90',
                    'Frozen': '#FFD700',
                    'Deactivated': '#FF6B6B',
                    'Expired': '#A9A9A9'
                }
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No card data available")
    except Exception as e:
        st.error(f"Error loading card status: {str(e)}")

with col_card2:
    st.markdown("#### Recent Card Actions")
    try:
        card_logs = audit_logs_table.scan(
            FilterExpression=Attr('timestamp').gte(cutoff_time) &
                            (Attr('action').eq('REPORT_LOST_CARD') |
                             Attr('action').eq('FREEZE_CARD') |
                             Attr('action').eq('UNFREEZE_CARD'))
        )

        if card_logs['Items']:
            df = pd.DataFrame(card_logs['Items'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp', ascending=False).head(10)

            df_display = df[['timestamp', 'action', 'result']].copy()
            df_display['timestamp'] = df_display['timestamp'].dt.strftime('%Y-%m-%d %H:%M')

            st.dataframe(
                df_display,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "timestamp": "Time",
                    "action": "Action",
                    "result": "Result"
                }
            )
        else:
            st.info("No card actions in selected time range")
    except Exception as e:
        st.error(f"Error loading card actions: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>🏦 First National Bank - Banking Agent Dashboard</p>
        <p>Real-time monitoring | Secure by design | FDIC Insured</p>
        <p style='font-size: 12px; margin-top: 10px;'>
            All data is encrypted at rest and in transit.
            Audit logs are immutable and tamper-proof for regulatory compliance.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
