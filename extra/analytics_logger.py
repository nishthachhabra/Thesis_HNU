"""
Enhanced Analytics Logger with Separate CSV Files per User Type
Version 2.0 - With Personalization and Historical Sentiment Tracking
"""
import pandas as pd
import os
from datetime import datetime
from typing import Dict, Optional, List
import threading
import csv

class AnalyticsLogger:
    """Thread-safe CSV logger with separate files per user type and personalization"""
    
    def __init__(self, base_filename: str = 'insights'):
        self.base_filename = base_filename
        self.lock = threading.Lock()
        
        # Define file mapping
        self.file_mapping = {
            'student': f'{base_filename}_students.csv',
            'employee': f'{base_filename}_employee.csv',
            'partner': f'{base_filename}_partner.csv',
            'admin': f'{base_filename}_employee.csv'  # Admin logs go to employee file
        }
        
        # Initialize all CSV files
        for user_type, filename in self.file_mapping.items():
            if user_type != 'admin':  # Skip duplicate initialization for admin
                self._initialize_csv(filename)
        
        # Initialize personalization and sentiment tracking
        try:
            from personalization_engine import PersonalizationEngine
            from historical_sentiment_tracker import HistoricalSentimentTracker
            
            self.personalization_engine = PersonalizationEngine()
            self.sentiment_tracker = HistoricalSentimentTracker()
            print("✅ Personalization and sentiment tracking enabled")
        except ImportError as e:
            self.personalization_engine = None
            self.sentiment_tracker = None
            print(f"⚠️ Personalization features not available: {e}")
    
    def _get_filename(self, user_type: str) -> str:
        """Get appropriate filename for user type"""
        return self.file_mapping.get(user_type, f'{self.base_filename}_other.csv')
    
    def _initialize_csv(self, filename: str):
        """Initialize CSV file with headers including intent column"""
        if not os.path.exists(filename):
            columns = [
                'timestamp',
                'session_id',
                'user_id',
                'user_name',
                'user_type',
                'is_guest',
                'department',
                'degree',
                'course',
                'query',
                'language',
                'intent',
                'intent_confidence',
                'intent_description',
                'sentiment',
                'sentiment_confidence',
                'lead_score',
                'bias_level',
                'bias_score',
                'bias_patterns',
                'bias_mitigation',
                'query_length',
                'response_time_ms',
                'interaction_count',
                'sentiment_trend',
                'frustration_score',
                'personalization_applied'
            ]
            
            df = pd.DataFrame(columns=columns)
            df.to_csv(filename, index=False, encoding='utf-8', quoting=csv.QUOTE_ALL)
            print(f"✅ Created {filename} with {len(columns)} columns")
        else:
            # Validate existing file
            try:
                df = pd.read_csv(filename, encoding='utf-8', quoting=csv.QUOTE_ALL, on_bad_lines='skip')
                print(f"✅ Loaded existing {filename} with {len(df)} rows")
            except Exception as e:
                print(f"⚠️ Warning reading existing {filename}: {e}")
    
    def _sanitize_text(self, text: any) -> str:
        """Sanitize text to prevent CSV issues"""
        if text is None:
            return 'N/A'
        
        text_str = str(text)
        # Replace problematic characters
        text_str = text_str.replace('', ' ').replace('\r', ' ')
        text_str = text_str.replace('"', "'")  # Replace double quotes with single quotes
        text_str = ' '.join(text_str.split())  # Normalize whitespace
        
        # Truncate if too long
        if len(text_str) > 500:
            text_str = text_str[:497] + '...'
        
        return text_str
    
    def log_interaction(self,
                       session_id: str,
                       user_id: Optional[str],
                       user_name: str,
                       user_type: str,
                       is_guest: bool,
                       department: Optional[str],
                       degree: Optional[str],
                       query: str,
                       analytics: Dict,
                       intent: str,
                       intent_confidence: float,
                       intent_description: str,
                       response_time_ms: Optional[int] = None):
        """
        Log interaction to appropriate CSV file based on user type
        Enhanced with personalization and sentiment tracking
        
        Args:
            session_id: Session identifier
            user_id: User ID
            user_name: User's name
            user_type: Type of user (student/employee/partner/admin)
            is_guest: Whether user is guest
            department: User's department
            degree: User's degree (students only)
            query: User query text
            analytics: Analytics dictionary from sentiment analyzer
            intent: Classified intent label
            intent_confidence: Intent classification confidence
            intent_description: Human-readable intent description
            response_time_ms: Response time in milliseconds
        """
        with self.lock:
            try:
                # Get appropriate filename
                filename = self._get_filename(user_type)
                
                # Get personalization data
                interaction_count = 0
                sentiment_trend = 'neutral'
                frustration_score = 0.0
                personalization_applied = False
                
                if self.personalization_engine and user_id and user_id != 'guest':
                    try:
                        # Update personalization profile
                        self.personalization_engine.update_interaction(
                            user_id=user_id,
                            language=analytics.get('language', 'en'),
                            topic=intent
                        )
                        
                        # Get user profile for interaction count
                        profile = self.personalization_engine.get_user_profile(user_id)
                        interaction_count = profile.get('interaction_count', 0)
                        personalization_applied = True
                        
                    except Exception as e:
                        print(f"⚠️ Personalization update error: {e}")
                
                # Record sentiment history and get trend
                if self.sentiment_tracker and user_id and user_id != 'guest':
                    try:
                        # Record this interaction
                        self.sentiment_tracker.record_sentiment(
                            user_id=user_id,
                            sentiment=analytics.get('sentiment', 'neutral'),
                            confidence=analytics.get('sentiment_confidence', 0.5),
                            intent=intent,
                            query=query
                        )
                        
                        # Get sentiment trend
                        trend_data = self.sentiment_tracker.calculate_sentiment_trend(user_id)
                        sentiment_trend = trend_data.get('trend', 'neutral')
                        
                        # Get frustration score
                        frustration_score = self.sentiment_tracker.get_frustration_score(user_id)
                        
                    except Exception as e:
                        print(f"⚠️ Sentiment tracking error: {e}")
                
                # Sanitize all text fields
                new_row = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'session_id': self._sanitize_text(session_id),
                    'user_id': self._sanitize_text(user_id if user_id else 'guest'),
                    'user_name': self._sanitize_text(user_name),
                    'user_type': self._sanitize_text(user_type),
                    'is_guest': is_guest,
                    'department': self._sanitize_text(department if department else 'N/A'),
                    'degree': self._sanitize_text(degree if degree else 'N/A'),
                    'course': 'N/A',  # Can be populated later if needed
                    'query': self._sanitize_text(query),
                    'language': analytics.get('language', 'en'),
                    'intent': self._sanitize_text(intent),
                    'intent_confidence': round(intent_confidence, 3),
                    'intent_description': self._sanitize_text(intent_description),
                    'sentiment': analytics.get('sentiment', 'neutral'),
                    'sentiment_confidence': round(analytics.get('sentiment_confidence', 0.5), 3),
                    'lead_score': int(analytics.get('lead_score', 50)),
                    'bias_level': analytics.get('bias_level', 'low'),
                    'bias_score': round(analytics.get('bias_score', 0.0), 3),
                    'bias_patterns': self._sanitize_text(analytics.get('bias_patterns', 'none')),
                    'bias_mitigation': self._sanitize_text(analytics.get('bias_mitigation', 'N/A')),
                    'query_length': len(query.split()),
                    'response_time_ms': int(response_time_ms) if response_time_ms else 0,
                    'interaction_count': interaction_count,
                    'sentiment_trend': sentiment_trend,
                    'frustration_score': round(frustration_score, 3),
                    'personalization_applied': personalization_applied
                }
                
                # Write with proper quoting
                df_new = pd.DataFrame([new_row])
                df_new.to_csv(
                    filename,
                    mode='a',
                    header=False,
                    index=False,
                    encoding='utf-8',
                    quoting=csv.QUOTE_ALL
                )
                
                print(f"✅ Logged to {filename}: {user_type} - {intent_description}")
                return True
                
            except Exception as e:
                print(f"❌ Error logging interaction to {filename}: {e}")
                import traceback
                traceback.print_exc()
                return False
    
    def get_insights(self,
                    user_type: Optional[str] = None,
                    intent: Optional[str] = None,
                    limit: int = 100,
                    combine_all: bool = False) -> pd.DataFrame:
        """
        Retrieve insights with optional filtering
        
        Args:
            user_type: Filter by user type (if None and combine_all=True, loads all)
            intent: Filter by intent
            limit: Maximum number of rows
            combine_all: If True, combine all CSV files
            
        Returns:
            Filtered DataFrame
        """
        try:
            if combine_all:
                # Load and combine all CSV files
                all_dfs = []
                for ut, filename in self.file_mapping.items():
                    if ut != 'admin' and os.path.exists(filename):
                        try:
                            df_temp = pd.read_csv(
                                filename,
                                encoding='utf-8',
                                quoting=csv.QUOTE_ALL,
                                on_bad_lines='skip'
                            )
                            all_dfs.append(df_temp)
                        except Exception as e:
                            print(f"⚠️ Error reading {filename}: {e}")
                
                if not all_dfs:
                    return pd.DataFrame()
                
                df = pd.concat(all_dfs, ignore_index=True)
            else:
                # Load specific file
                if user_type:
                    filename = self._get_filename(user_type)
                else:
                    # Default to employee file
                    filename = self._get_filename('employee')
                
                if not os.path.exists(filename):
                    return pd.DataFrame()
                
                df = pd.read_csv(
                    filename,
                    encoding='utf-8',
                    quoting=csv.QUOTE_ALL,
                    on_bad_lines='skip'
                )
            
            # Apply filters
            if user_type and not combine_all:
                df = df[df['user_type'] == user_type]
            
            if intent:
                df = df[df['intent'] == intent]
            
            # Sort by timestamp (newest first) and limit
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                df = df.sort_values('timestamp', ascending=False)
            
            return df.head(limit)
            
        except Exception as e:
            print(f"❌ Error reading insights: {e}")
            import traceback
            traceback.print_exc()
            return pd.DataFrame()
    
    def get_statistics(self, user_type: Optional[str] = None) -> Dict:
        """
        Get aggregated statistics for a specific user type or all
        Enhanced with personalization metrics
        
        Args:
            user_type: Specific user type or None for all combined
            
        Returns:
            Dictionary with statistics
        """
        try:
            # Get data
            df = self.get_insights(user_type=user_type, limit=10000, combine_all=(user_type is None))
            
            if df.empty:
                return {
                    'total_queries': 0,
                    'unique_users': 0,
                    'avg_lead_score': 0,
                    'sentiment_distribution': {},
                    'intent_distribution': {},
                    'user_type_distribution': {},
                    'avg_query_length': 0,
                    'language_distribution': {},
                    'high_bias_queries': 0,
                    'avg_intent_confidence': 0,
                    'guest_vs_authenticated': {},
                    'department_distribution': {},
                    'avg_response_time': 0,
                    'avg_interaction_count': 0,
                    'sentiment_trend_distribution': {},
                    'avg_frustration_score': 0,
                    'users_needing_intervention': 0,
                    'personalization_usage': 0
                }
            
            # Calculate standard stats
            stats = {
                'total_queries': len(df),
                'unique_users': df['user_id'].nunique() if 'user_id' in df.columns else 0,
                'avg_lead_score': round(df['lead_score'].mean(), 2) if 'lead_score' in df.columns else 0,
                'sentiment_distribution': df['sentiment'].value_counts().to_dict() if 'sentiment' in df.columns else {},
                'intent_distribution': df['intent'].value_counts().head(15).to_dict() if 'intent' in df.columns else {},
                'user_type_distribution': df['user_type'].value_counts().to_dict() if 'user_type' in df.columns else {},
                'avg_query_length': round(df['query_length'].mean(), 2) if 'query_length' in df.columns else 0,
                'language_distribution': df['language'].value_counts().to_dict() if 'language' in df.columns else {},
                'high_bias_queries': len(df[df['bias_level'] == 'high']) if 'bias_level' in df.columns else 0,
                'avg_intent_confidence': round(df['intent_confidence'].mean(), 3) if 'intent_confidence' in df.columns else 0,
                'guest_vs_authenticated': df['is_guest'].value_counts().to_dict() if 'is_guest' in df.columns else {},
                'department_distribution': df['department'].value_counts().head(10).to_dict() if 'department' in df.columns else {},
                'avg_response_time': round(df['response_time_ms'].mean(), 2) if 'response_time_ms' in df.columns else 0
            }
            
            # Add personalization stats
            if 'interaction_count' in df.columns:
                stats['avg_interaction_count'] = round(df['interaction_count'].mean(), 2)
            else:
                stats['avg_interaction_count'] = 0
            
            if 'sentiment_trend' in df.columns:
                stats['sentiment_trend_distribution'] = df['sentiment_trend'].value_counts().to_dict()
            else:
                stats['sentiment_trend_distribution'] = {}
            
            if 'frustration_score' in df.columns:
                stats['avg_frustration_score'] = round(df['frustration_score'].mean(), 3)
                # Users with high frustration (>0.7)
                stats['users_needing_intervention'] = len(df[df['frustration_score'] > 0.7])
            else:
                stats['avg_frustration_score'] = 0
                stats['users_needing_intervention'] = 0
            
            if 'personalization_applied' in df.columns:
                stats['personalization_usage'] = int((df['personalization_applied'] == True).sum())
            else:
                stats['personalization_usage'] = 0
            
            return stats
            
        except Exception as e:
            print(f"❌ Error calculating statistics: {e}")
            import traceback
            traceback.print_exc()
            return {
                'total_queries': 0,
                'unique_users': 0,
                'avg_lead_score': 0,
                'sentiment_distribution': {},
                'intent_distribution': {},
                'user_type_distribution': {},
                'avg_query_length': 0,
                'language_distribution': {},
                'high_bias_queries': 0,
                'avg_intent_confidence': 0,
                'guest_vs_authenticated': {},
                'department_distribution': {},
                'avg_response_time': 0,
                'avg_interaction_count': 0,
                'sentiment_trend_distribution': {},
                'avg_frustration_score': 0,
                'users_needing_intervention': 0,
                'personalization_usage': 0
            }
    
    def get_file_info(self) -> Dict[str, Dict]:
        """Get information about all CSV files"""
        info = {}
        
        for user_type, filename in self.file_mapping.items():
            if user_type == 'admin':
                continue  # Skip admin as it's same as employee
            
            if os.path.exists(filename):
                try:
                    df = pd.read_csv(filename, encoding='utf-8', quoting=csv.QUOTE_ALL, on_bad_lines='skip')
                    file_size = os.path.getsize(filename) / 1024  # KB
                    
                    info[user_type] = {
                        'filename': filename,
                        'exists': True,
                        'row_count': len(df),
                        'size_kb': round(file_size, 2),
                        'latest_entry': df['timestamp'].max() if 'timestamp' in df.columns and not df.empty else 'N/A'
                    }
                except Exception as e:
                    info[user_type] = {
                        'filename': filename,
                        'exists': True,
                        'error': str(e)
                    }
            else:
                info[user_type] = {
                    'filename': filename,
                    'exists': False
                }
        
        return info
    
    def repair_csv(self, user_type: Optional[str] = None):
        """
        Repair corrupted CSV file(s) by removing malformed rows
        Creates backups before repair
        
        Args:
            user_type: Specific user type to repair, or None for all
        """
        try:
            files_to_repair = []
            
            if user_type:
                files_to_repair.append((user_type, self._get_filename(user_type)))
            else:
                # Repair all files
                for ut, filename in self.file_mapping.items():
                    if ut != 'admin':
                        files_to_repair.append((ut, filename))
            
            results = []
            
            for ut, filename in files_to_repair:
                if not os.path.exists(filename):
                    results.append(f"⚠️ {filename} does not exist, skipping")
                    continue
                
                # Create backup
                backup_filename = f"{filename}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                import shutil
                shutil.copy2(filename, backup_filename)
                results.append(f"✅ Backup created: {backup_filename}")
                
                # Read with error handling
                df = pd.read_csv(
                    filename,
                    encoding='utf-8',
                    quoting=csv.QUOTE_ALL,
                    on_bad_lines='skip'
                )
                
                # Write clean version
                df.to_csv(
                    filename,
                    index=False,
                    encoding='utf-8',
                    quoting=csv.QUOTE_ALL
                )
                
                results.append(f"✅ {filename} repaired. Kept {len(df)} valid rows.")
            
            return True, results
            
        except Exception as e:
            error_msg = f"❌ Error repairing CSV: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return False, [error_msg]
    
    def export_combined_csv(self, output_filename: str = None) -> str:
        """
        Export all data combined into a single CSV file
        
        Args:
            output_filename: Output filename (default: insights_combined_TIMESTAMP.csv)
            
        Returns:
            Filename of exported CSV
        """
        try:
            if output_filename is None:
                output_filename = f'insights_combined_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            # Get combined data
            df = self.get_insights(limit=100000, combine_all=True)
            
            if df.empty:
                return None
            
            # Export
            df.to_csv(output_filename, index=False, encoding='utf-8', quoting=csv.QUOTE_ALL)
            print(f"✅ Exported {len(df)} rows to {output_filename}")
            
            return output_filename
            
        except Exception as e:
            print(f"❌ Error exporting combined CSV: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_user_type_summary(self) -> pd.DataFrame:
        """Get summary statistics for each user type"""
        try:
            summary_data = []
            
            for user_type in ['student', 'employee', 'partner']:
                filename = self._get_filename(user_type)
                
                if os.path.exists(filename):
                    df = pd.read_csv(filename, encoding='utf-8', quoting=csv.QUOTE_ALL, on_bad_lines='skip')
                    
                    summary_data.append({
                        'User Type': user_type.title(),
                        'Total Queries': len(df),
                        'Unique Users': df['user_id'].nunique() if 'user_id' in df.columns else 0,
                        'Avg Lead Score': round(df['lead_score'].mean(), 2) if 'lead_score' in df.columns and not df.empty else 0,
                        'Positive Sentiment %': round(
                            (df['sentiment'] == 'positive').sum() / len(df) * 100, 1
                        ) if 'sentiment' in df.columns and not df.empty else 0,
                        'Avg Intent Confidence': round(
                            df['intent_confidence'].mean() * 100, 1
                        ) if 'intent_confidence' in df.columns and not df.empty else 0,
                        'Avg Frustration': round(
                            df['frustration_score'].mean(), 2
                        ) if 'frustration_score' in df.columns and not df.empty else 0,
                        'File Size (KB)': round(os.path.getsize(filename) / 1024, 2)
                    })
                else:
                    summary_data.append({
                        'User Type': user_type.title(),
                        'Total Queries': 0,
                        'Unique Users': 0,
                        'Avg Lead Score': 0,
                        'Positive Sentiment %': 0,
                        'Avg Intent Confidence': 0,
                        'Avg Frustration': 0,
                        'File Size (KB)': 0
                    })
            
            return pd.DataFrame(summary_data)
            
        except Exception as e:
            print(f"❌ Error creating summary: {e}")
            return pd.DataFrame()
    
    def get_users_needing_attention(self, threshold: float = 0.7) -> pd.DataFrame:
        """
        Get list of users with high frustration or declining sentiment
        
        Args:
            threshold: Frustration score threshold
            
        Returns:
            DataFrame with users needing attention
        """
        try:
            df = self.get_insights(limit=10000, combine_all=True)
            
            if df.empty or 'frustration_score' not in df.columns:
                return pd.DataFrame()
            
            # Filter users with high frustration or declining sentiment
            attention_df = df[
                (df['frustration_score'] > threshold) | 
                (df['sentiment_trend'] == 'declining')
            ]
            
            if attention_df.empty:
                return pd.DataFrame()
            
            # Group by user
            user_summary = attention_df.groupby('user_id').agg({
                'user_name': 'first',
                'user_type': 'first',
                'frustration_score': 'max',
                'sentiment_trend': 'last',
                'sentiment': 'last',
                'timestamp': 'max'
            }).reset_index()
            
            user_summary = user_summary.sort_values('frustration_score', ascending=False)
            
            return user_summary
            
        except Exception as e:
            print(f"❌ Error getting users needing attention: {e}")
            return pd.DataFrame()