import streamlit as st
import pandas as pd

st.set_page_config(page_title="Data Explorer", page_icon=":material/bar_chart:", layout="wide", initial_sidebar_state="expanded")

MAX_FILE_SIZE = 100 * 1024 * 1024

st.title(":material/bar_chart: Data Explorer")
st.subheader("Analyze your CSV data with ease")

with st.sidebar:
    st.markdown("### :material/upload: Upload Data")
    uploaded_file = st.file_uploader(
        "Choose a CSV file", type="csv",
        help="Upload a CSV file (max 100MB)"
    )
    
    st.markdown("### :material/info: About")
    st.info("""
        This is a simple data explorer app. Upload a CSV file to:
        - View data preview
        - See basic statistics
        - Create visualizations
        
        Supported file size: Up to 100MB
    """)

if uploaded_file is None:
    st.info("""
        ### :material/arrow_left: Getting Started
        1. Use the sidebar on the left to upload your CSV file
        2. File should be in CSV format
        3. For best performance, ensure your file is under 100MB
        4. After upload, you'll see data preview and visualization options
    """)
else:
    try:
        file_size = uploaded_file.size
        if file_size > MAX_FILE_SIZE:
            st.warning(f"""
                ### :material/alert: Large File Detected
                Your file is {file_size / 1024 / 1024:.1f}MB, which exceeds the recommended limit of 100MB.
                The app may be slower with large files.
            """)
            
        df = pd.read_csv(uploaded_file)
        
        if df.empty:
            st.warning("""
                ### :material/alert: Empty File
                The uploaded CSV file contains no data.
                Please check the file contents and try again.
            """)
        else:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                with st.container(border=True):
                    st.metric("Avg Price", f"${df['price'].mean():,.2f}")
            with col2:
                with st.container(border=True):
                    st.metric("Total Orders", f"{df['orders'].sum():,}")
            with col3:
                with st.container(border=True):
                    st.metric("Total Customers", f"{df['customers'].sum():,}")
            with col4:
                with st.container(border=True):
                    st.metric("Products", df['product'].nunique())
            
            st.markdown("### :material/table_chart: Data Preview")
            
            column_config = {}
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    column_config[col] = st.column_config.NumberColumn(
                        col, help=f"Values for {col}",
                        min_value=df[col].min(), max_value=df[col].max(),
                        step=0.01 if df[col].dtype == 'float64' else 1
                    )
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    column_config[col] = st.column_config.DatetimeColumn(col, help=f"Date/time values for {col}", format="YYYY-MM-DD HH:mm:ss")
                else:
                    column_config[col] = st.column_config.TextColumn(col, help=f"Text values for {col}")

            st.dataframe(df, column_config=column_config, hide_index=True, height=400)
            
            st.download_button(
                label=":material/download: Download data as CSV",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name='data.csv', mime='text/csv',
            )
            
            numeric_columns = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            
            if len(numeric_columns) > 0:
                st.markdown("### :material/analytics: Data Visualization")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    chart_type = st.selectbox("Select Chart Type", options=["Bar", "Line", "Scatter"])
                with col2:
                    x_axis = st.selectbox("Select X-Axis", options=df.columns.tolist())
                with col3:
                    y_axis = st.selectbox("Select Y-Axis", options=numeric_columns)
                
                chart_data = pd.DataFrame({x_axis: df[x_axis], y_axis: df[y_axis]}).set_index(x_axis)
                
                st.markdown(f"#### :material/show_chart: {y_axis} by {x_axis}")
                if chart_type == "Bar":
                    st.bar_chart(chart_data, use_container_width=True, height=500)
                elif chart_type == "Line":
                    st.line_chart(chart_data, use_container_width=True, height=500)
                else:
                    st.scatter_chart(chart_data, use_container_width=True, height=500)
            else:
                st.info("""
                    ### :material/block: No Visualizations Available
                    The uploaded file contains no numeric columns.
                    To create charts, your data should include at least one column with numbers.
                """)
            
    except pd.errors.EmptyDataError:
        st.error("""
            ### :material/alert: Invalid File
            The uploaded file appears to be empty or invalid.
            Please check the file contents and try again.
        """)
    except Exception as e:
        st.error(f"""
            ### :material/alert: Error
            An error occurred while processing the file:
            {str(e)}
        """)
