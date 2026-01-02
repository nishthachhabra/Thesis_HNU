"""
HR/Admin Dashboard - Analytics & Insights for Admins
Displays queries, intents, sentiments, trends, and anomaly detection
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path
from scipy import stats
import warnings
from core.session_manager import SessionManager
warnings.filterwarnings('ignore')

# --- DATABASE CONNECTION ---
@st.cache_resource
def get_db_connection():
    # Try multiple path variations
    possible_paths = [
        Path(__file__).parent.parent / 'database' / 'hnu_users.db',
        Path('User_chat/database/hnu_users.db'),
        Path('./database/hnu_users.db'),
    ]
    
    for db_path in possible_paths:
        if db_path.exists():
            return sqlite3.connect(str(db_path))
    
    return None

def fetch_all_messages():
    """Fetch all messages from chat_messages table"""
    try:
        conn = get_db_connection()
        if conn is None:
            return pd.DataFrame()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_messages'")
        if not cursor.fetchone():
            return pd.DataFrame()
        
        cursor.execute("""
            SELECT cm.id, cm.session_id, cm.role, cm.content, cm.timestamp, 
                   cm.intent, cm.sentiment, cm.lead_score, cs.user_type, cs.created_at
            FROM chat_messages cm
            JOIN chat_sessions cs ON cm.session_id = cs.session_id
            WHERE cs.user_type IN ('student', 'employee', 'partner')
            ORDER BY cm.id DESC
        """)
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        return pd.DataFrame(data, columns=columns) if data else pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def process_dashboard_data():
    """Process all data for dashboard with caching"""
    df = fetch_all_messages()
    
    if df.empty:
        return None, None, None, None, None
    
    user_msgs = df[df['role'] == 'user'].copy()
    
    if 'created_at' in user_msgs.columns:
        user_msgs['created_at'] = pd.to_datetime(user_msgs['created_at'], errors='coerce')
        user_msgs['date'] = user_msgs['created_at'].dt.date
    
    for col in ['intent', 'sentiment', 'lead_score', 'user_type']:
        if col not in user_msgs.columns:
            user_msgs[col] = 'N/A'
    
    return user_msgs, df, None, datetime.now(), None

def detect_anomalies(sentiment_series):
    """Detect anomalies in sentiment data using Z-score"""
    sentiment_map = {'positive': 1, 'neutral': 0, 'negative': -1}
    numeric_sentiments = sentiment_series.map(sentiment_map)
    
    if len(numeric_sentiments) < 3:
        return []
    
    z_scores = np.abs(stats.zscore(numeric_sentiments.dropna()))
    anomalies = np.where(z_scores > 2.5)[0]
    return anomalies.tolist()

def predict_sentiment_trend(sentiment_series):
    """Simple trend prediction for sentiment"""
    sentiment_map = {'positive': 1, 'neutral': 0, 'negative': -1}
    numeric = sentiment_series.map(sentiment_map).dropna().values
    
    if len(numeric) < 3:
        return "Insufficient data"
    
    x = np.arange(len(numeric))
    z = np.polyfit(x, numeric, 1)
    slope = z[0]
    
    if slope > 0.1:
        return "📈 Improving"
    elif slope < -0.1:
        return "📉 Declining"
    else:
        return "➡️ Stable"

def render_admin_dashboard():
    """Main dashboard render function"""
    
    # --- STYLING ---
    st.set_page_config(
        page_title="HNU Admin Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.markdown("""
        <style>
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 25px;
            border-radius: 15px;
            color: white;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin: 10px 0;
        }
        .insight-box {
            background: #f0f4ff;
            padding: 20px;
            border-left: 5px solid #667eea;
            border-radius: 10px;
            margin: 15px 0;
        }
        .trend-positive { color: #2ecc71; font-weight: bold; }
        .trend-negative { color: #e74c3c; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)
    
    # --- SECURITY CHECK ---
    if not st.session_state.get('is_hr'):
        st.error("❌ Access Denied. Only HR personnel can access this dashboard.")
        st.info("Contact your administrator for access.")
        st.stop()
    
    # --- HEADER WITH LOGOUT ---
    header_col1, header_col2 = st.columns([9, 1])
    with header_col1:
        st.title("📊 HNU HR/Admin Dashboard")

    with header_col2:
        st.write("")  # spacing
        st.write("")
        if st.button("🚪 Logout", help="Logout"):
            SessionManager.logout_user()
            # Clear URL parameters before rerun
            if 'auth' in st.query_params:
                del st.query_params['auth']
            if 'session' in st.query_params:
                del st.query_params['session']
            st.rerun()

    st.markdown("---")
    
    # --- LOAD DATA ---
    with st.spinner("Loading dashboard data..."):
        user_msgs, all_msgs, stats_df, load_time, _ = process_dashboard_data()
    
    if user_msgs is None or user_msgs.empty:
        st.info("📊 No real data available yet. Generating sample data for demonstration...")
        
        np.random.seed(42)
        dates = pd.date_range('2024-10-01', periods=50, freq='D')
        sample_data = {
            'id': range(1, 51),
            'session_id': [f'session_{i%10}' for i in range(50)],
            'role': ['user'] * 50,
            'content': [f'Sample query {i}: How can I get help with my studies?' for i in range(50)],
            'timestamp': ['12:00:00'] * 50,
            'intent': np.random.choice(['academic_support', 'course_info', 'admission', 'technical_help', 'general_inquiry'], 50),
            'sentiment': np.random.choice(['positive', 'neutral', 'negative'], 50, p=[0.6, 0.3, 0.1]),
            'lead_score': np.random.randint(20, 100, 50),
            'user_type': np.random.choice(['student', 'employee', 'partner'], 50, p=[0.6, 0.3, 0.1]),
            'created_at': dates,
            'date': dates.date
        }
        user_msgs = pd.DataFrame(sample_data)
        st.success("✅ Sample data loaded for demonstration purposes")
    else:
        if 'date' not in user_msgs.columns:
            user_msgs['date'] = user_msgs['created_at'].dt.date
    
    # --- KEY METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📨 Total Queries", f"{len(user_msgs):,}")
    with col2:
        st.metric("👥 Active Users", user_msgs['session_id'].nunique())
    with col3:
        positive_pct = (len(user_msgs[user_msgs['sentiment'] == 'positive']) / len(user_msgs) * 100) if len(user_msgs) > 0 else 0
        st.metric("😊 Positive Sentiment", f"{positive_pct:.1f}%")
    with col4:
        frustration_pct = (len(user_msgs[user_msgs['sentiment'] == 'negative']) / len(user_msgs) * 100) if len(user_msgs) > 0 else 0
        st.metric("😤 Frustration Rate", f"{frustration_pct:.1f}%")
    
    st.markdown("---")
    
    # --- SIDEBAR FILTERS ---
    with st.sidebar:
        st.subheader("🎛️ Filters & Controls")
        
        user_types = ['All'] + sorted(user_msgs['user_type'].unique().tolist())
        selected_user_type = st.selectbox("Filter by User Type:", user_types)
        
        min_date = user_msgs['date'].min()
        max_date = user_msgs['date'].max()
        date_range = st.date_input("Date Range:", value=(min_date, max_date), max_value=max_date)
        
        sentiment_filter = st.multiselect(
            "Filter by Sentiment:",
            options=['positive', 'neutral', 'negative'],
            default=['positive', 'neutral', 'negative']
        )
        
        st.markdown("---")
        if load_time:
            st.info(f"Dashboard updated at {load_time.strftime('%H:%M:%S')}")
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
    
    # Apply filters
    filtered_data = user_msgs.copy()
    
    if selected_user_type != 'All':
        filtered_data = filtered_data[filtered_data['user_type'] == selected_user_type]
    
    if len(date_range) == 2:
        filtered_data = filtered_data[(filtered_data['date'] >= date_range[0]) & (filtered_data['date'] <= date_range[1])]
    
    filtered_data = filtered_data[filtered_data['sentiment'].isin(sentiment_filter)]
    
    st.sidebar.metric("Filtered Queries", len(filtered_data))
    
    # --- TABS ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["📈 Sentiment Analytics", "🎯 Intent Analysis", "👥 User Segmentation", 
         "🚨 Anomalies & Trends", "📋 Detailed Logs"]
    )
    
    # === TAB 1: SENTIMENT ANALYTICS ===
    with tab1:
        st.subheader("Sentiment Distribution & Trends")
        col1, col2 = st.columns(2)
        
        with col1:
            sentiment_counts = filtered_data['sentiment'].value_counts()
            fig_pie = go.Figure(data=[go.Pie(
                labels=sentiment_counts.index,
                values=sentiment_counts.values,
                marker=dict(colors=['#2ecc71', '#95a5a6', '#e74c3c'])
            )])
            fig_pie.update_layout(title="Sentiment Distribution", height=400)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            sentiment_by_type = pd.crosstab(filtered_data['user_type'], filtered_data['sentiment'])
            fig_bar = go.Figure(data=[
                go.Bar(name=col, x=sentiment_by_type.index, y=sentiment_by_type[col])
                for col in sentiment_by_type.columns
            ])
            fig_bar.update_layout(title="Sentiment by User Type", barmode='group', height=400)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            trend = predict_sentiment_trend(filtered_data['sentiment'])
            st.markdown(f"<div class='insight-box'><strong>Trend:</strong> {trend}</div>", unsafe_allow_html=True)
        with col2:
            avg_lead = filtered_data['lead_score'].mean() if 'lead_score' in filtered_data else 0
            st.markdown(f"<div class='insight-box'><strong>Avg Engagement:</strong> {avg_lead:.1f}/100</div>", unsafe_allow_html=True)
        with col3:
            most_common = filtered_data['sentiment'].mode()[0] if len(filtered_data) > 0 else 'N/A'
            st.markdown(f"<div class='insight-box'><strong>Most Common:</strong> {most_common}</div>", unsafe_allow_html=True)
    
    # === TAB 2: INTENT ANALYSIS ===
    with tab2:
        st.subheader("Intent Classification & Patterns")
        col1, col2 = st.columns(2)
        
        with col1:
            intent_counts = filtered_data['intent'].value_counts().head(10)
            fig_intent = go.Figure(data=[go.Bar(
                y=intent_counts.index,
                x=intent_counts.values,
                orientation='h',
                marker=dict(color=intent_counts.values, colorscale='Viridis')
            )])
            fig_intent.update_layout(title="Top 10 Intents", xaxis_title="Frequency", height=400)
            st.plotly_chart(fig_intent, use_container_width=True)
        
        with col2:
            intent_by_type = filtered_data['user_type'].value_counts()
            fig_type = go.Figure(data=[go.Bar(x=intent_by_type.index, y=intent_by_type.values)])
            fig_type.update_layout(title="Query Volume by User Type", height=400)
            st.plotly_chart(fig_type, use_container_width=True)
    
    # === TAB 3: USER SEGMENTATION ===
    with tab3:
        st.subheader("User Segmentation & Behavior")
        col1, col2 = st.columns(2)
        
        with col1:
            users_by_type = filtered_data.groupby('user_type')['session_id'].nunique()
            fig_users = go.Figure(data=[go.Bar(x=users_by_type.index, y=users_by_type.values)])
            fig_users.update_layout(title="Active Users by Type", height=400)
            st.plotly_chart(fig_users, use_container_width=True)
        
        with col2:
            queries_by_type = filtered_data.groupby('user_type').size()
            fig_queries = go.Figure(data=[go.Pie(labels=queries_by_type.index, values=queries_by_type.values)])
            fig_queries.update_layout(title="Query Distribution", height=400)
            st.plotly_chart(fig_queries, use_container_width=True)
    
    # === TAB 4: ANOMALIES & TRENDS ===
    with tab4:
        st.subheader("🚨 Anomaly Detection")
        col1, col2 = st.columns(2)
        
        with col1:
            anomalies = detect_anomalies(filtered_data['sentiment'])
            if anomalies:
                st.warning(f"Found {len(anomalies)} anomalies")
            else:
                st.success("✅ No anomalies detected!")
        
        with col2:
            high_engagement = len(filtered_data[filtered_data['lead_score'] > 75])
            st.metric("👑 High Engagement", high_engagement)
    
    # === TAB 5: DETAILED LOGS ===
    with tab5:
        st.subheader("📋 Detailed Query Logs")
        
        search_term = st.text_input("🔍 Search in queries:")
        display_data = filtered_data.copy()
        
        if search_term:
            display_data = display_data[display_data['content'].str.contains(search_term, case=False, na=False)]
        
        display_cols = ['date', 'user_type', 'content', 'intent', 'sentiment', 'lead_score']
        
        if not display_data.empty:
            st.dataframe(display_data[display_cols].sort_values('date', ascending=False), use_container_width=True)
            
            csv = display_data[display_cols].to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"hr_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    # --- FOOTER ---
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: #999; margin-top: 30px;'>
        <small>HNU HR Admin Dashboard | Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</small>
    </div>
    """, unsafe_allow_html=True)