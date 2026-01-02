"""
Admin Dashboard for HNU Enhanced Chatbot
Beautiful visualizations with Plotly for comprehensive analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Optional
import traceback


class AdminDashboard:
    """Admin dashboard with beautiful Plotly visualizations"""
    
    def __init__(self, analytics_logger):
        """
        Initialize admin dashboard
        
        Args:
            analytics_logger: AnalyticsLogger instance with data
        """
        self.analytics_logger = analytics_logger
    
    def render_dashboard(self):
        """Render the complete admin dashboard"""
        
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 30px; border-radius: 20px; margin-bottom: 30px; text-align: center;'>
            <h1 style='color: white; margin: 0;'>📊 Admin Analytics Dashboard</h1>
            <p style='color: #e2e8f0; margin: 10px 0 0 0; font-size: 1.1rem;'>
                Comprehensive insights & ML-powered analytics
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # View selector
        view_mode = st.radio(
            "📌 Select View:",
            ["📈 Overview", "📝 Recent Queries", "👥 User Analytics", 
             "😊 Sentiment Analysis", "🎯 Lead Scoring", "🧠 Intent Analysis"],
            horizontal=True,
            key="admin_view_selector"
        )
        
        try:
            # Load data
            stats = self.analytics_logger.get_statistics()
            df = self.analytics_logger.get_insights(limit=1000)
            
            # Render selected view
            if view_mode == "📈 Overview":
                self.render_overview(stats, df)
            elif view_mode == "📝 Recent Queries":
                self.render_recent_queries(df)
            elif view_mode == "👥 User Analytics":
                self.render_user_analytics(df)
            elif view_mode == "😊 Sentiment Analysis":
                self.render_sentiment_analysis(df)
            elif view_mode == "🎯 Lead Scoring":
                self.render_lead_scoring(df)
            elif view_mode == "🧠 Intent Analysis":
                self.render_intent_analysis(df)
        
        except Exception as e:
            st.error(f"❌ Error loading dashboard: {e}")
            st.error(traceback.format_exc())
            
            # Debug info
            with st.expander("🔍 Debug Information"):
                st.write("**CSV File Path:**", self.analytics_logger.csv_file)
                st.write("**File Exists:**", self.analytics_logger.csv_file_exists())
                
                try:
                    df_test = pd.read_csv(self.analytics_logger.csv_file)
                    st.write("**Rows in CSV:**", len(df_test))
                    st.write("**Columns:**", df_test.columns.tolist())
                    st.dataframe(df_test.head(3))
                except Exception as e2:
                    st.error(f"Cannot read CSV: {e2}")
    
    def render_overview(self, stats: dict, df: pd.DataFrame):
        """Render overview dashboard"""
        
        st.markdown("## 📈 System Overview")
        
        # Key metrics in cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📊 Total Queries",
                value=stats.get('total_queries', 0),
                delta=f"+{stats.get('queries_today', 0)} today"
            )
        
        with col2:
            st.metric(
                label="👥 Unique Users",
                value=stats.get('unique_users', 0),
                delta=f"+{stats.get('new_users_today', 0)} new"
            )
        
        with col3:
            st.metric(
                label="🎯 Avg Lead Score",
                value=f"{stats.get('avg_lead_score', 0):.1f}/100",
                delta=f"{stats.get('lead_score_change', 0):+.1f}"
            )
        
        with col4:
            st.metric(
                label="🧠 Intent Confidence",
                value=f"{stats.get('avg_intent_confidence', 0)*100:.0f}%",
                delta=f"{stats.get('intent_confidence_change', 0):+.1f}%"
            )
        
        st.markdown("---")
        
        # Charts in 2 columns
        col1, col2 = st.columns(2)
        
        with col1:
            # Sentiment distribution
            st.markdown("### 😊 Sentiment Distribution")
            sentiment_dist = stats.get('sentiment_distribution', {})
            
            if sentiment_dist:
                fig_sentiment = go.Figure(data=[go.Pie(
                    labels=list(sentiment_dist.keys()),
                    values=list(sentiment_dist.values()),
                    marker=dict(colors=['#10b981', '#6b7280', '#ef4444']),
                    hole=0.4
                )])
                fig_sentiment.update_layout(
                    showlegend=True,
                    height=300,
                    margin=dict(l=20, r=20, t=20, b=20)
                )
                st.plotly_chart(fig_sentiment, use_container_width=True)
            else:
                st.info("No sentiment data yet")
        
        with col2:
            # User type distribution
            st.markdown("### 👥 User Type Distribution")
            user_dist = stats.get('user_type_distribution', {})
            
            if user_dist:
                fig_users = go.Figure(data=[go.Pie(
                    labels=list(user_dist.keys()),
                    values=list(user_dist.values()),
                    marker=dict(colors=['#3b82f6', '#10b981', '#f59e0b', '#ef4444']),
                    hole=0.4
                )])
                fig_users.update_layout(
                    showlegend=True,
                    height=300,
                    margin=dict(l=20, r=20, t=20, b=20)
                )
                st.plotly_chart(fig_users, use_container_width=True)
            else:
                st.info("No user type data yet")
        
        st.markdown("---")
        
        # Activity timeline
        if not df.empty:
            st.markdown("### 📅 Activity Timeline (Last 7 Days)")
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['date'] = df['timestamp'].dt.date
            
            # Last 7 days
            last_7_days = df[df['date'] >= (datetime.now().date() - timedelta(days=7))]
            
            if not last_7_days.empty:
                daily_counts = last_7_days.groupby('date').size().reset_index(name='queries')
                
                fig_timeline = px.line(
                    daily_counts,
                    x='date',
                    y='queries',
                    title='Daily Query Volume',
                    markers=True
                )
                fig_timeline.update_traces(
                    line=dict(color='#667eea', width=3),
                    marker=dict(size=10)
                )
                fig_timeline.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Number of Queries",
                    height=350
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
            else:
                st.info("No data in the last 7 days")
        
        # Language distribution
        st.markdown("---")
        st.markdown("### 🌐 Language Distribution")
        
        lang_dist = stats.get('language_distribution', {})
        
        if lang_dist:
            fig_lang = go.Figure(data=[go.Bar(
                x=list(lang_dist.keys()),
                y=list(lang_dist.values()),
                marker=dict(color='#8b5cf6')
            )])
            fig_lang.update_layout(
                xaxis_title="Language",
                yaxis_title="Count",
                height=300
            )
            st.plotly_chart(fig_lang, use_container_width=True)
        else:
            st.info("No language data yet")
    
    def render_recent_queries(self, df: pd.DataFrame):
        """Render recent queries view"""
        
        st.markdown("## 📝 Recent Queries")
        
        if df.empty:
            st.info("No queries logged yet")
            return
        
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            user_types = ["All"] + df['user_type'].unique().tolist()
            filter_user_type = st.selectbox("👥 User Type", user_types, key="filter_user_type_queries")
        
        with col2:
            sentiments = ["All"] + df['sentiment'].unique().tolist()
            filter_sentiment = st.selectbox("😊 Sentiment", sentiments, key="filter_sentiment_queries")
        
        with col3:
            languages = ["All"] + df['language'].unique().tolist()
            filter_language = st.selectbox("🌐 Language", languages, key="filter_language_queries")
        
        with col4:
            limit = st.number_input("📊 Show Records", min_value=10, max_value=500, value=50, step=10)
        
        # Apply filters
        filtered_df = df.copy()
        
        if filter_user_type != "All":
            filtered_df = filtered_df[filtered_df['user_type'] == filter_user_type]
        
        if filter_sentiment != "All":
            filtered_df = filtered_df[filtered_df['sentiment'] == filter_sentiment]
        
        if filter_language != "All":
            filtered_df = filtered_df[filtered_df['language'] == filter_language]
        
        # Sort by timestamp (most recent first)
        filtered_df = filtered_df.sort_values('timestamp', ascending=False).head(limit)
        
        # Display count
        st.info(f"📊 Showing {len(filtered_df)} of {len(df)} total queries")
        
        # Display dataframe
        display_cols = ['timestamp', 'user_name', 'user_type', 'query', 
                       'sentiment', 'lead_score', 'intent_description', 'language']
        
        # Check which columns exist
        available_cols = [col for col in display_cols if col in filtered_df.columns]
        
        st.dataframe(
            filtered_df[available_cols],
            use_container_width=True,
            height=500
        )
        
        # Download button
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name=f"queries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    def render_user_analytics(self, df: pd.DataFrame):
        """Render user analytics view"""
        
        st.markdown("## 👥 User Analytics")
        
        if df.empty:
            st.info("No user data yet")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Most active users
            st.markdown("### 🏆 Most Active Users")
            user_counts = df['user_name'].value_counts().head(10)
            
            fig_users = px.bar(
                x=user_counts.values,
                y=user_counts.index,
                orientation='h',
                title='Top 10 Users by Query Count'
            )
            fig_users.update_traces(marker_color='#667eea')
            fig_users.update_layout(
                xaxis_title="Number of Queries",
                yaxis_title="User",
                height=400
            )
            st.plotly_chart(fig_users, use_container_width=True)
        
        with col2:
            # Average lead score by user type
            st.markdown("### 🎯 Lead Score by User Type")
            avg_lead = df.groupby('user_type')['lead_score'].mean().sort_values(ascending=False)
            
            fig_lead = go.Figure(data=[go.Bar(
                x=avg_lead.index,
                y=avg_lead.values,
                marker=dict(
                    color=avg_lead.values,
                    colorscale='RdYlGn',
                    showscale=True
                )
            )])
            fig_lead.update_layout(
                xaxis_title="User Type",
                yaxis_title="Average Lead Score",
                height=400
            )
            st.plotly_chart(fig_lead, use_container_width=True)
        
        st.markdown("---")
        
        # Department analysis (if available)
        if 'department' in df.columns:
            st.markdown("### 🏛️ Queries by Department")
            dept_df = df[df['department'] != 'N/A']
            
            if not dept_df.empty:
                dept_counts = dept_df['department'].value_counts()
                
                fig_dept = px.pie(
                    values=dept_counts.values,
                    names=dept_counts.index,
                    title='Department Distribution'
                )
                fig_dept.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_dept, use_container_width=True)
        
        # Guest vs Authenticated
        st.markdown("---")
        st.markdown("### 🔐 Guest vs Authenticated Users")
        
        guest_counts = df['is_guest'].value_counts()
        
        fig_guest = go.Figure(data=[go.Bar(
            x=['Authenticated', 'Guest'],
            y=[guest_counts.get(False, 0), guest_counts.get(True, 0)],
            marker=dict(color=['#10b981', '#6b7280'])
        )])
        fig_guest.update_layout(
            xaxis_title="User Type",
            yaxis_title="Count",
            height=300
        )
        st.plotly_chart(fig_guest, use_container_width=True)
    
    def render_sentiment_analysis(self, df: pd.DataFrame):
        """Render sentiment analysis view"""
        
        st.markdown("## 😊 Sentiment Analysis")
        
        if df.empty:
            st.info("No sentiment data yet")
            return
        
        # Sentiment trends over time
        st.markdown("### 📈 Sentiment Trends Over Time")
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        sentiment_over_time = df.groupby(['date', 'sentiment']).size().unstack(fill_value=0)
        
        if not sentiment_over_time.empty:
            fig_sentiment_trend = go.Figure()
            
            colors = {'positive': '#10b981', 'neutral': '#6b7280', 'negative': '#ef4444'}
            
            for sentiment in sentiment_over_time.columns:
                fig_sentiment_trend.add_trace(go.Scatter(
                    x=sentiment_over_time.index,
                    y=sentiment_over_time[sentiment],
                    mode='lines+markers',
                    name=sentiment.title(),
                    line=dict(color=colors.get(sentiment, '#3b82f6'), width=2),
                    marker=dict(size=8)
                ))
            
            fig_sentiment_trend.update_layout(
                xaxis_title="Date",
                yaxis_title="Number of Queries",
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig_sentiment_trend, use_container_width=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Sentiment by user type
            st.markdown("### 👥 Sentiment by User Type")
            sentiment_by_type = pd.crosstab(df['user_type'], df['sentiment'])
            
            fig_sent_type = go.Figure()
            
            for sentiment in sentiment_by_type.columns:
                fig_sent_type.add_trace(go.Bar(
                    name=sentiment.title(),
                    x=sentiment_by_type.index,
                    y=sentiment_by_type[sentiment],
                    marker=dict(color=colors.get(sentiment, '#3b82f6'))
                ))
            
            fig_sent_type.update_layout(
                barmode='stack',
                xaxis_title="User Type",
                yaxis_title="Count",
                height=350
            )
            st.plotly_chart(fig_sent_type, use_container_width=True)
        
        with col2:
            # Sentiment confidence
            st.markdown("### 🎯 Sentiment Confidence")
            avg_confidence = df.groupby('sentiment')['sentiment_confidence'].mean().sort_values(ascending=False)
            
            fig_conf = go.Figure(data=[go.Bar(
                x=avg_confidence.index,
                y=avg_confidence.values * 100,
                marker=dict(color='#8b5cf6')
            )])
            fig_conf.update_layout(
                xaxis_title="Sentiment",
                yaxis_title="Average Confidence (%)",
                height=350
            )
            st.plotly_chart(fig_conf, use_container_width=True)
        
        # Recent negative queries
        st.markdown("---")
        st.markdown("### 😞 Recent Negative Sentiment Queries")
        
        negative_df = df[df['sentiment'] == 'negative'].sort_values('timestamp', ascending=False).head(10)
        
        if not negative_df.empty:
            display_cols = ['timestamp', 'user_name', 'query', 'sentiment_confidence']
            available_cols = [col for col in display_cols if col in negative_df.columns]
            
            st.dataframe(
                negative_df[available_cols],
                use_container_width=True
            )
        else:
            st.success("✅ No negative sentiment queries!")
    
    def render_lead_scoring(self, df: pd.DataFrame):
        """Render lead scoring view"""
        
        st.markdown("## 🎯 Lead Scoring Analysis")
        
        if df.empty:
            st.info("No lead scoring data yet")
            return
        
        # Lead score distribution
        st.markdown("### 📊 Lead Score Distribution")
        
        fig_hist = px.histogram(
            df,
            x='lead_score',
            nbins=20,
            title='Lead Score Distribution'
        )
        fig_hist.update_traces(marker_color='#667eea')
        fig_hist.update_layout(
            xaxis_title="Lead Score",
            yaxis_title="Frequency",
            height=350
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
        st.markdown("---")
        
        # High-value leads
        st.markdown("### 🌟 High-Value Leads (Score > 70)")
        
        high_leads = df[df['lead_score'] > 70].sort_values('lead_score', ascending=False)
        
        if not high_leads.empty:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("High-Value Leads", len(high_leads))
            
            with col2:
                conversion_rate = (len(high_leads) / len(df)) * 100
                st.metric("Conversion Rate", f"{conversion_rate:.1f}%")
            
            with col3:
                avg_score = high_leads['lead_score'].mean()
                st.metric("Avg Score", f"{avg_score:.1f}/100")
            
            st.markdown("#### 📋 High-Value Lead Details")
            display_cols = ['timestamp', 'user_name', 'user_type', 'query', 'lead_score', 'sentiment']
            available_cols = [col for col in display_cols if col in high_leads.columns]
            
            st.dataframe(
                high_leads[available_cols].head(20),
                use_container_width=True,
                height=300
            )
        else:
            st.info("No high-value leads yet")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Lead score by user type
            st.markdown("### 👥 Lead Score by User Type")
            avg_lead_by_type = df.groupby('user_type')['lead_score'].mean().sort_values(ascending=False)
            
            fig_lead_type = px.bar(
                x=avg_lead_by_type.index,
                y=avg_lead_by_type.values,
                title='Average Lead Score by User Type'
            )
            fig_lead_type.update_traces(marker_color='#10b981')
            fig_lead_type.update_layout(
                xaxis_title="User Type",
                yaxis_title="Average Lead Score",
                height=350
            )
            st.plotly_chart(fig_lead_type, use_container_width=True)
        
        with col2:
            # Lead score by sentiment
            st.markdown("### 😊 Lead Score by Sentiment")
            lead_by_sentiment = df.groupby('sentiment')['lead_score'].mean().sort_values(ascending=False)
            
            fig_lead_sent = px.bar(
                x=lead_by_sentiment.index,
                y=lead_by_sentiment.values,
                title='Average Lead Score by Sentiment'
            )
            fig_lead_sent.update_traces(marker_color='#f59e0b')
            fig_lead_sent.update_layout(
                xaxis_title="Sentiment",
                yaxis_title="Average Lead Score",
                height=350
            )
            st.plotly_chart(fig_lead_sent, use_container_width=True)
    
    def render_intent_analysis(self, df: pd.DataFrame):
        """Render intent analysis view"""
        
        st.markdown("## 🧠 Intent Recognition Analysis")
        
        if df.empty or 'intent' not in df.columns:
            st.info("No intent data yet")
            return
        
        # Top intents
        st.markdown("### 🎯 Top Detected Intents")
        
        intent_counts = df['intent'].value_counts()
        
        fig_intents = px.bar(
            x=intent_counts.values,
            y=intent_counts.index,
            orientation='h',
            title='Intent Distribution'
        )
        fig_intents.update_traces(marker_color='#8b5cf6')
        fig_intents.update_layout(
            xaxis_title="Count",
            yaxis_title="Intent",
            height=400
        )
        st.plotly_chart(fig_intents, use_container_width=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Intent by user type
            st.markdown("### 👥 Intent by User Type")
            intent_by_type = pd.crosstab(df['user_type'], df['intent'])
            
            fig_intent_type = go.Figure()
            
            for intent in intent_by_type.columns:
                fig_intent_type.add_trace(go.Bar(
                    name=intent,
                    x=intent_by_type.index,
                    y=intent_by_type[intent]
                ))
            
            fig_intent_type.update_layout(
                barmode='stack',
                xaxis_title="User Type",
                yaxis_title="Count",
                height=350
            )
            st.plotly_chart(fig_intent_type, use_container_width=True)
        
        with col2:
            # Intent confidence
            st.markdown("### 🎯 Intent Confidence")
            avg_intent_conf = df.groupby('intent')['intent_confidence'].mean().sort_values(ascending=False)
            
            fig_conf = px.bar(
                x=avg_intent_conf.index,
                y=avg_intent_conf.values * 100,
                title='Average Confidence by Intent'
            )
            fig_conf.update_traces(marker_color='#3b82f6')
            fig_conf.update_layout(
                xaxis_title="Intent",
                yaxis_title="Confidence (%)",
                height=350
            )
            st.plotly_chart(fig_conf, use_container_width=True)
        
        # Low confidence predictions
        st.markdown("---")
        st.markdown("### ⚠️ Low Confidence Intent Predictions (< 50%)")
        
        low_conf = df[df['intent_confidence'] < 0.5].sort_values('intent_confidence', ascending=True)
        
        if not low_conf.empty:
            st.warning(f"Found {len(low_conf)} queries with low intent confidence")
            
            display_cols = ['timestamp', 'query', 'intent_description', 'intent_confidence']
            available_cols = [col for col in display_cols if col in low_conf.columns]
            
            st.dataframe(
                low_conf[available_cols].head(20),
                use_container_width=True
            )
        else:
            st.success("✅ All intent predictions have high confidence!")
        
        # Intent trends over time
        st.markdown("---")
        st.markdown("### 📈 Intent Trends Over Time")
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        intent_over_time = df.groupby(['date', 'intent']).size().unstack(fill_value=0)
        
        if not intent_over_time.empty:
            fig_intent_trend = go.Figure()
            
            for intent in intent_over_time.columns:
                fig_intent_trend.add_trace(go.Scatter(
                    x=intent_over_time.index,
                    y=intent_over_time[intent],
                    mode='lines+markers',
                    name=intent,
                    line=dict(width=2),
                    marker=dict(size=6)
                ))
            
            fig_intent_trend.update_layout(
                xaxis_title="Date",
                yaxis_title="Count",
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig_intent_trend, use_container_width=True)