import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Advanced PCA Visualization Dashboard",
    page_icon="📊",
    layout="wide"
)

@st.cache_data
def get_mongodb_data():
    """Fetch all records from MongoDB"""
    try:
        # Get MongoDB connection details from environment variables
        mongo_uri = os.getenv("MONGODB_URI")
        database_name = os.getenv("MONGODB_DATABASE")
        collection_name = os.getenv("MONGODB_COLLECTION")
        
        # Connect to MongoDB
        client = MongoClient(mongo_uri)
        db = client[database_name]
        collection = db[collection_name]
        
        # Fetch all records
        records = list(collection.find())
        
        # Convert to DataFrame
        if records:
            df = pd.DataFrame(records)
            # Convert ObjectId to string if present
            if '_id' in df.columns:
                df['_id'] = df['_id'].astype(str)
            return df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error connecting to MongoDB: {str(e)}")
        return pd.DataFrame()

def filter_data_by_range(df, x_range, y_range):
    """Filter dataframe based on coordinate range"""
    if x_range is None or y_range is None:
        return df
    
    filtered_df = df[
        (df['Xpca'] >= x_range[0]) & (df['Xpca'] <= x_range[1]) &
        (df['Ypca'] >= y_range[0]) & (df['Ypca'] <= y_range[1])
    ]
    return filtered_df

def main():
    st.title("📊 Advanced PCA Visualization Dashboard")
    # Instructions
    with st.expander("ℹ️ How to use this dashboard"):
        st.markdown("""
        **Interactive Features:**
        1. **Area Selection**: Use multiple selection modes to filter data - selected area automatically filters the table
        2. **Search**: Filter records using the search box
        3. **Download**: Export filtered data as CSV
        
        **Chart Selection Modes:**
        - 📦 **Box Select**: Click and drag to draw a rectangle around points 
        - 🎯 **Lasso Select**: Use the lasso tool in the toolbar to draw custom shapes around points
        - 🔘 **Point Select**: Click individual points to select them (creates bounding box)
        - 🔄 **Pan**: Use pan mode to navigate the chart without selecting
        - 🔍 **Zoom**: Use zoom tools to focus on specific areas (default mode)
        
        **Plotly Toolbar:**
        - Use the toolbar above the chart to switch between selection modes
        - Hover over toolbar icons for tooltips explaining each tool
        - Double-click the chart to reset zoom to original view
        """)
    
    # Initialize session state for zoom ranges
    if 'x_range' not in st.session_state:
        st.session_state.x_range = None
    if 'y_range' not in st.session_state:
        st.session_state.y_range = None
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Refresh data button
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()     

    
    # Load data
    with st.spinner("Loading data from MongoDB..."):
        df = get_mongodb_data()
    
    if df.empty:
        st.error("No data found or connection failed. Please check your MongoDB configuration.")
        st.info("Make sure to set these environment variables in your .env file:")
        st.code("""
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=your_database_name
MONGODB_COLLECTION=your_collection_name
        """)
        return
    
    # Check if required columns exist
    if 'Xpca' not in df.columns or 'Ypca' not in df.columns:
        st.error("Required columns 'Xpca' and 'Ypca' not found in the data.")
        st.info("Available columns:")
        st.write(df.columns.tolist())
        return
    

    
    # Add data summary to sidebar after data is loaded
    with st.sidebar:
        st.subheader("📋 Data Summary")
        st.metric("Total Records", len(df))
        
        # Current zoom info
        if st.session_state.x_range and st.session_state.y_range:
            st.subheader("🔍 Current Zoom")
            st.text(f"X: {st.session_state.x_range[0]:.2f} to {st.session_state.x_range[1]:.2f}")
            st.text(f"Y: {st.session_state.y_range[0]:.2f} to {st.session_state.y_range[1]:.2f}")
    
    # Scatterplot - Full width
    st.subheader("🎯 Interactive PCA Scatterplot")
    
    # Reset zoom button above chart
    if st.button("🔄 Reset Zoom", key="reset_zoom_top"):
        st.session_state.x_range = None
        st.session_state.y_range = None
        st.rerun()
    
    # Create Plotly scatterplot
    fig = px.scatter(
        df, 
        x='Xpca', 
        y='Ypca',
        title="PCA Coordinates Scatterplot",
        labels={'Xpca': 'X PCA', 'Ypca': 'Y PCA'},
        opacity=0.7
    )
    
    # Update layout for better interactivity
    fig.update_layout(
        height=600,
        dragmode='zoom',  # Enable zoom as default tool
        selectdirection='d',  # 'd' for diagonal selection
        title_x=0.5,
        title_font_size=16
    )
    
    # Update traces for better selection visibility
    fig.update_traces(
        marker=dict(size=4),
        selected=dict(marker=dict(opacity=1.0, size=6)),
        unselected=dict(marker=dict(opacity=0.3, size=3))
    )
    
    # Display the chart with selection events
    event = st.plotly_chart(
        fig, 
        use_container_width=True, 
        key="pca_chart",
        on_select="rerun",
        selection_mode=['box', 'lasso', 'points']
    )
    
    # Handle selection events
    if event and event.selection and event.selection.box:
        # Extract box selection coordinates
        box_data = event.selection.box[0]  # Get first box selection
        
        if 'x' in box_data and 'y' in box_data:
            # Extract selection coordinates from box and ensure proper min/max order
            x_coords = box_data['x']
            y_coords = box_data['y']
            
            # Ensure we have min/max in correct order
            x_range = [min(x_coords), max(x_coords)]
            y_range = [min(y_coords), max(y_coords)]
            
            # Update session state
            st.session_state.x_range = x_range
            st.session_state.y_range = y_range
            
            st.success(f"🎯 Selected area: X: {x_range[0]:.4f} to {x_range[1]:.4f}, Y: {y_range[0]:.4f} to {y_range[1]:.4f}")
    
    elif event and event.selection and event.selection.points:
        # Handle point selections - get bounding box of selected points
        points = event.selection.points
        if points:
            x_coords = [point['x'] for point in points]
            y_coords = [point['y'] for point in points]
            
            x_range = [min(x_coords), max(x_coords)]
            y_range = [min(y_coords), max(y_coords)]
            
            # Add small buffer if single point selected
            if len(points) == 1:
                x_buffer = 0.1
                y_buffer = 0.1
                x_range = [x_range[0] - x_buffer, x_range[1] + x_buffer]
                y_range = [y_range[0] - y_buffer, y_range[1] + y_buffer]
            
            # Update session state
            st.session_state.x_range = x_range
            st.session_state.y_range = y_range
            
            st.success(f"🎯 Selected {len(points)} point(s): X: {x_range[0]:.2f} to {x_range[1]:.2f}, Y: {y_range[0]:.2f} to {y_range[1]:.2f}")
    
    elif event and event.selection and event.selection.lasso:
        # Handle lasso selections - get bounding box of lasso area
        lasso_data = event.selection.lasso[0]
        if 'x' in lasso_data and 'y' in lasso_data:
            x_coords = lasso_data['x']
            y_coords = lasso_data['y']
            
            x_range = [min(x_coords), max(x_coords)]
            y_range = [min(y_coords), max(y_coords)]
            
            # Update session state
            st.session_state.x_range = x_range
            st.session_state.y_range = y_range
            
            st.success(f"🎯 Lasso selected area: X: {x_range[0]:.2f} to {x_range[1]:.2f}, Y: {y_range[0]:.2f} to {y_range[1]:.2f}")
    

    
    # Show current filter status
    if st.session_state.x_range and st.session_state.y_range:
        st.info(f"📍 Active filter: X: {st.session_state.x_range[0]:.2f} to {st.session_state.x_range[1]:.2f}, Y: {st.session_state.y_range[0]:.2f} to {st.session_state.y_range[1]:.2f}")
    

    
    # Filter data based on current zoom
    if st.session_state.x_range and st.session_state.y_range:
        filtered_df = filter_data_by_range(df, st.session_state.x_range, st.session_state.y_range)
        st.subheader(f"📊 Records in Current Zoom ({len(filtered_df)} records)")
    else:
        filtered_df = df
        st.subheader("📊 All Records")
    
    # Add search functionality
    search_term = st.text_input("🔍 Search records:", placeholder="Enter search term...")
    
    # Apply search filter
    display_df = filtered_df.copy()
    if search_term:
        # Search across all text columns
        text_columns = filtered_df.select_dtypes(include=['object']).columns
        if len(text_columns) > 0:
            mask = filtered_df[text_columns].astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            display_df = filtered_df[mask]
            st.info(f"Found {len(display_df)} records matching '{search_term}'")
    
    # Display the table
    if not display_df.empty:
        # Column selection
        all_columns = display_df.columns.tolist()
        default_columns = ['Xpca', 'Ypca'] + [col for col in all_columns if col not in ['Xpca', 'Ypca', '_id']][:5]
        selected_columns = st.multiselect(
            "Select columns to display:",
            all_columns,
            default=default_columns[:7]
        )
        
        if selected_columns:
            # Display table with sorting
            st.dataframe(
                display_df[selected_columns].sort_values('Xpca'),
                use_container_width=True,
                height=400
            )
            
            # Statistics for filtered data
            if len(selected_columns) >= 2:
                stats_col1, stats_col2, stats_col3 = st.columns(3)
                with stats_col1:
                    st.metric("Filtered Records", len(display_df))
                with stats_col2:
                    if 'Xpca' in selected_columns:
                        st.metric("Avg X", f"{display_df['Xpca'].mean():.2f}")
                with stats_col3:
                    if 'Ypca' in selected_columns:
                        st.metric("Avg Y", f"{display_df['Ypca'].mean():.2f}")
            
            # Download button
            csv = display_df[selected_columns].to_csv(index=False)
            st.download_button(
                label="📥 Download filtered data as CSV",
                data=csv,
                file_name=f"pca_data_filtered_{len(display_df)}_records.csv",
                mime="text/csv"
            )
        else:
            st.warning("Please select at least one column to display.")
    else:
        st.warning("No records found with current filters.")

if __name__ == "__main__":
    main() 