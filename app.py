import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------
# Page Configuration
# ---------------------------------
# Set a professional dark theme for the dashboard.
st.set_page_config(
    page_title="Vahan Professional Analytics Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------
# Custom CSS for a Polished Dark Theme
# ---------------------------------
# Inject custom CSS for a superior visual experience with a new dark color scheme.
st.markdown("""
<style>
    /* Main app background - Dark Gray */
    .main {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #FAFAFA;
    }
    /* Styling for metric cards */
    div[data-testid="metric-container"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 25px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
        transition: all 0.3s ease-in-out;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 24px rgba(0,0,0,0.3);
    }
    /* Styling for Streamlit tabs */
    .stTabs [data-baseweb="tab-list"] {
		gap: 24px;
	}
	.stTabs [data-baseweb="tab"] {
		height: 50px;
        white-space: pre-wrap;
		background-color: #0E1117;
        border: 1px solid #30363D;
		border-radius: 8px 8px 0px 0px;
		gap: 1px;
		padding-top: 10px;
		padding-bottom: 10px;
        color: #A0A0A0;
    }
	.stTabs [aria-selected="true"] {
  		background-color: #161B22; /* Darker background for the active tab content */
        color: #FFFFFF;
	}
    /* General container padding */
    .block-container {
        padding: 2rem 3rem 3rem 3rem;
    }
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #161B22;
    }
    /* Change text color for markdown */
    .stMarkdown {
        color: #EAEAEA;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------
# Data Loading and Caching
# ---------------------------------
@st.cache_data
def load_data():
    """
    Loads, cleans, and prepares the vehicle registration data.
    """
    # This file path is specific to your local machine as requested.
    file_path = r'C:\Users\sahil\OneDrive\Desktop\task 2\data\processed\vahan_processed_tidy.csv'
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig')
        df.columns = df.columns.str.strip()
        df['registrations'] = pd.to_numeric(df['registrations'], errors='coerce')
        df.dropna(subset=['registrations'], inplace=True)
        df['registrations'] = df['registrations'].astype(int)
        return df
    except FileNotFoundError:
        st.error(f"🚨 **File Not Found!** Please ensure the file exists at the path: `{file_path}`")
        return None
    except Exception as e:
        st.error(f"An error occurred while loading the data: {e}")
        return None

# Helper function to convert dataframe to CSV for download
@st.cache_data
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8')

# Load the data
df = load_data()

# ---------------------------------
# Main Dashboard UI
# ---------------------------------
if df is not None:
    # --- Sidebar ---
    st.sidebar.image("https://placehold.co/300x100/0E1117/FFFFFF?text=Vahan+Analytics&font=roboto", use_column_width=True)
    st.sidebar.header("📊 Dashboard Controls")
    
    entity_types = df['entity_type'].unique()
    analysis_type = st.sidebar.selectbox(
        "Select Analysis Type",
        options=entity_types,
        index=0,
        help="Choose the main category for analysis (e.g., Maker, Vehicle Category)."
    )

    # Filter dataframe based on selected analysis type
    analysis_df = df[df['entity_type'] == analysis_type].copy()
    
    st.sidebar.header(f"Filters for {analysis_type}")
    
    # Dynamic slider for Top N selection
    num_entities = analysis_df['entity_name'].nunique()
    top_n = st.sidebar.slider(
        f"Select Top N {analysis_type}s",
        min_value=3,
        max_value=min(50, num_entities),
        value=min(15, num_entities),
        step=1,
        help="Focus the charts on the top performing entities."
    )
    
    # Search box for specific entities
    all_entities = sorted(analysis_df['entity_name'].unique())
    selected_entities = st.sidebar.multiselect(
        f"Search for specific {analysis_type}s",
        options=all_entities,
        help="Select one or more entities to isolate their data across all charts."
    )

    # Apply search filter if any entities are selected
    if selected_entities:
        display_df = analysis_df[analysis_df['entity_name'].isin(selected_entities)]
    else:
        display_df = analysis_df

    # --- Main Panel ---
    st.title(f"🚀 Vahan Professional Analytics: {analysis_type}")
    st.markdown("An interactive dashboard to explore vehicle registration trends.")
    st.markdown("---")

    # --- Key Metrics ---
    total_registrations = display_df['registrations'].sum()
    unique_entities_count = display_df['entity_name'].nunique()
    avg_registrations = display_df['registrations'].mean() if not display_df.empty else 0

    st.header("📈 Key Performance Indicators")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Registrations", f"{total_registrations:,.0f}")
    col2.metric(f"Unique {analysis_type}s Shown", f"{unique_entities_count}")
    col3.metric("Average Registrations", f"{avg_registrations:,.2f}")
    st.markdown("---")

    # Aggregate data for charts
    top_df = display_df.groupby('entity_name')['registrations'].sum().nlargest(top_n).reset_index()

    # --- Tabbed Interface for Visualizations ---
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 Top Performers", "🗺️ Market Treemap", "📊 Distribution Analysis", "🗂️ Data Explorer"])
    
    # Common layout for charts (height is now removed to be set individually)
    chart_layout = {
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'font': {'color': '#FAFAFA'},
        'title_x': 0.5,
    }

    # Check if there is data to display after filtering
    if display_df.empty:
        st.warning(f"No data available for the selected filters. Please adjust your selections in the sidebar.")
    else:
        with tab1:
            st.subheader(f"Top {top_n} Performers by Registration Volume")
            
            c1, c2 = st.columns((6, 4))
            with c1:
                fig_bar = px.bar(
                    top_df, x='registrations', y='entity_name', orientation='h',
                    title=f'Top {top_n} {analysis_type}s',
                    labels={'registrations': 'Total Registrations', 'entity_name': ''},
                    text='registrations', color='registrations',
                    color_continuous_scale=px.colors.sequential.Plasma
                )
                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, height=500, **chart_layout)
                fig_bar.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                st.plotly_chart(fig_bar, use_container_width=True)
            with c2:
                fig_donut = px.pie(
                    top_df, names='entity_name', values='registrations',
                    title=f'Share Among Top {top_n}', hole=0.6,
                    color_discrete_sequence=px.colors.qualitative.Plotly
                )
                fig_donut.update_traces(textinfo='percent+label', pull=[0.05]*len(top_df), textfont_size=14)
                fig_donut.update_layout(showlegend=False, annotations=[dict(text='Share', x=0.5, y=0.5, font_size=24, showarrow=False)], height=500, **chart_layout)
                st.plotly_chart(fig_donut, use_container_width=True)

        with tab2:
            st.subheader("Market Share Treemap")
            fig_tree = px.treemap(
                top_df,
                path=[px.Constant(f"All {analysis_type}s"), 'entity_name'],
                values='registrations',
                color='registrations',
                color_continuous_scale='Viridis',
                title=f'Market Share Treemap for Top {top_n} {analysis_type}s',
                hover_data={'registrations': ':,d'} # Format hover data
            )
            # FIX: The conflicting 'height' argument is removed from this call.
            fig_tree.update_layout(margin=dict(t=50, l=25, r=25, b=25), height=600, **chart_layout)
            st.plotly_chart(fig_tree, use_container_width=True)

        with tab3:
            st.subheader("Registration Distribution Insights")
            st.markdown("Analyze the spread of registration data. Highly skewed data can be viewed on a logarithmic scale for better clarity.")
            
            use_log_scale = st.toggle('Use Logarithmic Scale for Histogram', value=False, help="Useful for highly skewed distributions.")
            
            c1, c2 = st.columns(2)
            with c1:
                # Histogram
                fig_hist = px.histogram(
                    display_df, x="registrations", nbins=50,
                    title="Frequency of Registration Counts",
                    labels={'registrations': 'Number of Registrations'},
                    marginal="box",
                    log_x=use_log_scale
                )
                fig_hist.update_traces(marker_color='#00BFFF') # DeepSkyBlue
                fig_hist.update_layout(height=500, **chart_layout)
                st.plotly_chart(fig_hist, use_container_width=True)
            with c2:
                # Box Plot
                fig_box = px.box(
                    display_df, y="registrations",
                    title="Distribution of Registrations",
                    labels={'registrations': 'Number of Registrations'},
                    points="outliers" # Show only outliers for a cleaner plot
                )
                fig_box.update_traces(marker_color='#20B2AA') # LightSeaGreen
                fig_box.update_layout(height=500, **chart_layout)
                st.plotly_chart(fig_box, use_container_width=True)

        with tab4:
            st.subheader("Interactive Data Explorer")
            st.markdown("Explore, sort, and download the detailed data.")
            
            # Download Button
            csv_data = convert_df_to_csv(display_df)
            st.download_button(
               label="📥 Download Data as CSV",
               data=csv_data,
               file_name=f'{analysis_type}_data.csv',
               mime='text/csv',
            )
            
            st.dataframe(
                display_df.sort_values('registrations', ascending=False).reset_index(drop=True),
                use_container_width=True,
                height=600
            )

else:
    st.warning("Dashboard could not be loaded. Please check the data file and path in the script.")
