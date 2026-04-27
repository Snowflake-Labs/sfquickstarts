"""
Snowflake Intelligence - SnowMail
Gmail-style email viewer with split-pane layout
"""

import streamlit as st
import streamlit.components.v1 as components
from snowflake.snowpark.context import get_active_session
import pandas as pd
from datetime import datetime
import time

# Page config
st.set_page_config(
    page_title="SnowMail",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Gmail-like styling
st.markdown("""
<style>
    .stApp {
        background-color: #f5f7fa;
    }
    .main .block-container {
        padding-top: 1rem;
        padding-left: 0;
        padding-right: 0;
        max-width: 100%;
    }
    section[data-testid="stSidebar"] {
        display: none;
    }
    /* Custom button styling for email list */
    div[data-testid="column"] .stButton button {
        background: white !important;
        border: none !important;
        padding: 14px 16px !important;
        width: 100% !important;
        text-align: left !important;
        color: #202124 !important;
        font-size: 13px !important;
        border-radius: 0 !important;
        border-bottom: 1px solid #f0f0f0 !important;
        margin: 0 !important;
        transition: background 0.1s !important;
    }
    div[data-testid="column"] .stButton button:hover {
        background-color: #f5f5f5 !important;
        box-shadow: inset 4px 0 0 #29B5E8 !important;
    }
    div[data-testid="column"] .stButton button[kind="primary"] {
        background-color: #e8f4f8 !important;
        box-shadow: inset 4px 0 0 #29B5E8 !important;
        font-weight: 500 !important;
    }
    /* Action buttons styling */
    .action-btn button {
        background: #29B5E8 !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 8px 20px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        width: auto !important;
        min-width: 140px !important;
    }
    .action-btn button:hover {
        background: #1e8bb5 !important;
    }
    .delete-btn button {
        background: white !important;
        color: #d93025 !important;
        border: 1px solid #dadce0 !important;
        border-radius: 6px !important;
        padding: 8px 20px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        width: auto !important;
        min-width: 100px !important;
    }
    .delete-btn button:hover {
        background: #fef7f6 !important;
        border-color: #d93025 !important;
    }
    /* Refresh button styling */
    button[key="btn_refresh"] {
        background: white !important;
        color: #29B5E8 !important;
        border: 1px solid #29B5E8 !important;
        border-radius: 6px !important;
        padding: 10px 16px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.2s !important;
    }
    button[key="btn_refresh"]:hover {
        background: #f0f9fd !important;
        border-color: #1e8bb5 !important;
        color: #1e8bb5 !important;
    }
    /* Bulk delete button styling */
    button[key="btn_bulk_delete"] {
        background: #d93025 !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 16px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        transition: all 0.2s !important;
    }
    button[key="btn_bulk_delete"]:hover {
        background: #b92319 !important;
    }
    /* Pagination button styling */
    button[key="btn_prev_page"],
    button[key="btn_next_page"] {
        background: white !important;
        color: #5f6368 !important;
        border: 1px solid #dadce0 !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
        font-weight: 500 !important;
        font-size: 13px !important;
        transition: all 0.2s !important;
    }
    button[key="btn_prev_page"]:not([disabled]):hover,
    button[key="btn_next_page"]:not([disabled]):hover {
        background: #f5f5f5 !important;
        border-color: #29B5E8 !important;
        color: #29B5E8 !important;
    }
    button[key="btn_prev_page"][disabled],
    button[key="btn_next_page"][disabled] {
        opacity: 0.4 !important;
        cursor: not-allowed !important;
    }
</style>
""", unsafe_allow_html=True)

# Get Snowflake session
session = get_active_session()

# Initialize session state
if 'selected_email_id' not in st.session_state:
    st.session_state['selected_email_id'] = None
if 'selected_email_ids' not in st.session_state:
    st.session_state['selected_email_ids'] = set()
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = 1
if 'emails_per_page' not in st.session_state:
    st.session_state['emails_per_page'] = 10

# Header
st.markdown("""
<div style="padding: 16px 24px; background: white; border-bottom: 1px solid #e0e0e0; margin-bottom: 0;">
    <h1 style="margin: 0; font-size: 26px; color: #29B5E8; font-family: Lato, sans-serif; font-weight: 700;">
        ❄️ SnowMail
    </h1>
</div>
""", unsafe_allow_html=True)

# Query emails from table (granted during deployment)
try:
    emails_query = """
    SELECT 
        EMAIL_ID,
        RECIPIENT_EMAIL,
        SUBJECT,
        CREATED_AT,
        LENGTH(HTML_CONTENT) as HTML_SIZE
    FROM TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.EMAIL_PREVIEWS
    ORDER BY CREATED_AT DESC
    LIMIT 500
    """

    emails_df = session.sql(emails_query).to_pandas()
    
    if len(emails_df) == 0:
        st.info("📭 Your SnowMail inbox is empty. Use the Cortex Agent to generate and send email reports, or run Script 02 to load sample emails.")
    else:
        # Format timestamps
        emails_df['CREATED_AT'] = pd.to_datetime(emails_df['CREATED_AT'])
        emails_df['Time'] = emails_df['CREATED_AT'].dt.strftime('%b %d, %I:%M %p')
        emails_df['Full_Time'] = emails_df['CREATED_AT'].dt.strftime('%b %d, %Y, %I:%M %p')
        
        # Calculate pagination
        total_emails = len(emails_df)
        emails_per_page = st.session_state['emails_per_page']
        total_pages = (total_emails + emails_per_page - 1) // emails_per_page  # Ceiling division
        
        # Ensure current page is valid
        if st.session_state['current_page'] > total_pages:
            st.session_state['current_page'] = max(1, total_pages)
        
        # Get emails for current page
        start_idx = (st.session_state['current_page'] - 1) * emails_per_page
        end_idx = min(start_idx + emails_per_page, total_emails)
        paginated_emails_df = emails_df.iloc[start_idx:end_idx]
        
        # Create two-column layout
        col_list, col_detail = st.columns([1.5, 2.5])
        
        # LEFT PANE: Email List
        with col_list:
            # List header with selection controls
            selected_count = len(st.session_state['selected_email_ids'])
            showing_range = f"{start_idx + 1}-{end_idx}" if total_emails > 0 else "0"
            
            st.markdown('<div style="background: white; padding: 16px 16px 8px 16px; border-bottom: 2px solid #e0e0e0;">', unsafe_allow_html=True)
            
            # Header row
            header_col1, header_col2 = st.columns([2, 1])
            with header_col1:
                if selected_count > 0:
                    st.markdown(f"**📬 Inbox** ({total_emails} total) • **{selected_count} selected**")
                else:
                    st.markdown(f"**📬 Inbox** ({total_emails} total)")
            
            # Showing range
            st.caption(f"Showing {showing_range} of {total_emails}")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Pagination controls
            st.markdown('<div style="background: white; padding: 12px 16px; border-bottom: 1px solid #f0f0f0;">', unsafe_allow_html=True)
            pg_col1, pg_col2, pg_col3 = st.columns([1, 2, 1])
            
            with pg_col1:
                if st.button("◀ Prev", key="btn_prev_page", disabled=(st.session_state['current_page'] == 1)):
                    st.session_state['current_page'] -= 1
                    st.experimental_rerun()
            
            with pg_col2:
                st.markdown(f"<div style='text-align: center; padding-top: 8px;'><small>Page {st.session_state['current_page']} of {total_pages}</small></div>", unsafe_allow_html=True)
            
            with pg_col3:
                if st.button("Next ▶", key="btn_next_page", disabled=(st.session_state['current_page'] >= total_pages)):
                    st.session_state['current_page'] += 1
                    st.experimental_rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Selection controls and refresh button
            st.markdown('<div style="background: white; padding: 12px 16px; border-bottom: 1px solid #f0f0f0;">', unsafe_allow_html=True)
            
            # Select/Deselect all checkbox (for current page)
            col1, col2 = st.columns([1, 2])
            with col1:
                page_email_ids = set(paginated_emails_df['EMAIL_ID'].tolist())
                page_selected_count = len(page_email_ids & st.session_state['selected_email_ids'])
                select_all = st.checkbox(
                    "Select Page" if page_selected_count != len(page_email_ids) else "Deselect Page",
                    key="select_all_checkbox",
                    value=(page_selected_count == len(page_email_ids) and len(page_email_ids) > 0)
                )
                if select_all and page_selected_count != len(page_email_ids):
                    st.session_state['selected_email_ids'].update(page_email_ids)
                    st.experimental_rerun()
                elif not select_all and page_selected_count == len(page_email_ids):
                    st.session_state['selected_email_ids'] -= page_email_ids
                    st.experimental_rerun()
            
            with col2:
                if st.button("🔄 Check for New Mail", key="btn_refresh", use_container_width=True):
                    st.session_state['last_refresh'] = datetime.now()
                    st.session_state['current_page'] = 1  # Reset to first page on refresh
                    st.experimental_rerun()
            
            # Show last refresh time if available
            if 'last_refresh' in st.session_state:
                refresh_time = st.session_state['last_refresh'].strftime('%I:%M:%S %p')
                st.markdown(f'<div style="text-align: center; font-size: 11px; color: #5f6368; margin-top: 4px;">Last checked: {refresh_time}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Bulk delete button (shown when emails are selected)
            if selected_count > 0:
                st.markdown('<div style="background: white; padding: 8px 16px; border-bottom: 1px solid #f0f0f0;">', unsafe_allow_html=True)
                if st.button(f"🗑️ Delete Selected ({selected_count})", key="btn_bulk_delete", use_container_width=True):
                    try:
                        # Delete selected emails
                        emails_to_delete = list(st.session_state['selected_email_ids'])
                        email_ids_str = "', '".join(emails_to_delete)
                        delete_query = f"""
                        DELETE FROM TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.EMAIL_PREVIEWS
                        WHERE EMAIL_ID IN ('{email_ids_str}')
                        """
                        session.sql(delete_query).collect()
                        
                        # Clear selections
                        st.success(f"✅ {selected_count} email{'s' if selected_count > 1 else ''} deleted!")
                        st.session_state['selected_email_ids'] = set()
                        if st.session_state['selected_email_id'] in emails_to_delete:
                            st.session_state['selected_email_id'] = None
                        
                        time.sleep(1)
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to delete: {str(e)}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Create container for email list
            st.markdown('<div style="background: white;">', unsafe_allow_html=True)
            
            # Email list with checkboxes (showing current page only)
            for page_idx, (df_idx, row) in enumerate(paginated_emails_df.iterrows()):
                email_id = row['EMAIL_ID']
                is_selected = (st.session_state['selected_email_id'] == email_id)
                is_checked = email_id in st.session_state['selected_email_ids']
                
                # Truncate subject and recipient
                subject = row['SUBJECT'][:45] + "..." if len(row['SUBJECT']) > 45 else row['SUBJECT']
                recipient = row['RECIPIENT_EMAIL'][:25] + "..." if len(row['RECIPIENT_EMAIL']) > 25 else row['RECIPIENT_EMAIL']
                
                # Create two-column layout for checkbox and email button
                email_col1, email_col2 = st.columns([0.15, 0.85])
                
                with email_col1:
                    # Use page + index for unique keys per page
                    checkbox_key = f"check_p{st.session_state['current_page']}_idx{page_idx}"
                    checkbox = st.checkbox(
                        "",
                        key=checkbox_key,
                        value=is_checked,
                        label_visibility="collapsed"
                    )
                    if checkbox != is_checked:
                        if checkbox:
                            st.session_state['selected_email_ids'].add(email_id)
                        else:
                            st.session_state['selected_email_ids'].discard(email_id)
                        st.experimental_rerun()
                
                with email_col2:
                    button_label = f"**{subject}**\nTo: {recipient} • {row['Time']}"
                    if st.button(button_label, key=f"btn_p{st.session_state['current_page']}_idx{page_idx}", type="primary" if is_selected else "secondary"):
                        st.session_state['selected_email_id'] = email_id
                        st.experimental_rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # RIGHT PANE: Email Detail
        with col_detail:
            if st.session_state['selected_email_id']:
                # Get selected email
                selected_email = emails_df[emails_df['EMAIL_ID'] == st.session_state['selected_email_id']].iloc[0]
                
                # Email header
                st.markdown(f"""
                <div style="background: white; padding: 24px; border-bottom: 1px solid #e0e0e0;">
                    <div style="font-size: 20px; font-weight: 500; color: #202124; margin-bottom: 20px;">
                        {selected_email['SUBJECT']}
                    </div>
                    <div style="display: flex; align-items: center; gap: 14px;">
                        <div style="width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(135deg, #29B5E8 0%, #11567F 100%); display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 16px; flex-shrink: 0;">
                            NC
                        </div>
                        <div style="flex: 1;">
                            <div style="font-size: 14px; font-weight: 600; color: #202124;">
                                NovaConnect Intelligence Agent
                            </div>
                            <div style="font-size: 13px; color: #5f6368; margin-top: 2px;">
                                to {selected_email['RECIPIENT_EMAIL']}
                            </div>
                        </div>
                        <div style="font-size: 12px; color: #5f6368; flex-shrink: 0;">
                            {selected_email['Full_Time']}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Action buttons
                st.markdown('<div style="background: white; padding: 16px 24px; border-bottom: 1px solid #e0e0e0;">', unsafe_allow_html=True)
                
                btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([1.5, 1.5, 1.2, 3])
                
                with btn_col1:
                    st.markdown('<div class="action-btn">', unsafe_allow_html=True)
                    if st.button("📧 View Email", key="btn_view"):
                        st.session_state['email_view_mode'] = 'rendered'
                        st.experimental_rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with btn_col2:
                    st.markdown('<div class="action-btn">', unsafe_allow_html=True)
                    if st.button("</> HTML Source", key="btn_html"):
                        st.session_state['email_view_mode'] = 'html'
                        st.experimental_rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with btn_col3:
                    st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
                    # Determine what to delete
                    selected_count = len(st.session_state['selected_email_ids'])
                    delete_label = f"🗑️ Delete ({selected_count})" if selected_count > 0 else "🗑️ Delete"
                    
                    if st.button(delete_label, key="btn_delete"):
                        try:
                            # Delete selected emails or current email
                            emails_to_delete = list(st.session_state['selected_email_ids']) if selected_count > 0 else [st.session_state['selected_email_id']]
                            
                            # Create IN clause for SQL
                            email_ids_str = "', '".join(emails_to_delete)
                            delete_query = f"""
                            DELETE FROM TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.EMAIL_PREVIEWS
                            WHERE EMAIL_ID IN ('{email_ids_str}')
                            """
                            session.sql(delete_query).collect()
                            
                            # Clear selections and show success message
                            deleted_count = len(emails_to_delete)
                            st.success(f"✅ {deleted_count} email{'s' if deleted_count > 1 else ''} deleted successfully!")
                            st.session_state['selected_email_id'] = None
                            st.session_state['selected_email_ids'] = set()
                            
                            # Wait a moment to show the message, then reload
                            time.sleep(1)
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to delete email(s): {str(e)}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Fetch HTML content
                html_query = f"""
                SELECT HTML_CONTENT
                FROM TELCO_OPERATIONS_AI.DEFAULT_SCHEMA.EMAIL_PREVIEWS
                WHERE EMAIL_ID = '{st.session_state['selected_email_id']}'
                """
                html_result = session.sql(html_query).collect()
                
                if html_result:
                    html_content = html_result[0]['HTML_CONTENT']
                    
                    # Display content
                    st.markdown('<div style="background: white; padding: 0;">', unsafe_allow_html=True)
                    
                    if st.session_state.get('email_view_mode', 'rendered') == 'rendered':
                        components.html(html_content, height=700, scrolling=True)
                    else:
                        st.markdown('<div style="padding: 20px;">', unsafe_allow_html=True)
                        st.code(html_content, language="html", line_numbers=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.error("Email content not found")
            
            else:
                # No email selected
                st.markdown("""
                <div style="background: white; padding: 120px 40px; text-align: center; min-height: 700px; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                    <div style="font-size: 64px; margin-bottom: 24px; opacity: 0.3;">📧</div>
                    <div style="font-size: 18px; color: #5f6368; font-weight: 500;">
                        Select an email to view
                    </div>
                    <div style="font-size: 14px; color: #80868b; margin-top: 8px;">
                        Choose a message from the inbox to read
                    </div>
                </div>
                """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"""
    **Error loading emails**
    
    {str(e)}
    
    Make sure the EMAIL_PREVIEWS table exists and you have the correct permissions.
    """)
