import os
import json
import pandas as pd
import streamlit as st
import plotly.express as px
import requests
from sqlalchemy import create_engine, text
# The following imports are now unnecessary:
# from dotenv import load_dotenv 

# The following line is now unnecessary:
# load_dotenv() 

# ─────────────────────────────────────────────
# CUSTOM COMPONENTS
# ─────────────────────────────────────────────

def add_item_callback(key_name):
    """Callback to add item to the list and clear the input box state."""
    input_key = f"new_{key_name}_input"
    
    # Ensure the key exists and retrieve the input value from session state
    if input_key in st.session_state:
        new_item = st.session_state[input_key]
        
        if new_item and new_item.strip():
            # 1. Add the item to the main list
            st.session_state[key_name].append(new_item.strip())
            
            # 2. Clear the input box state. This is safe in a callback.
            st.session_state[input_key] = ""

def list_input_component(key_name, label):
    """
    Creates a dedicated section in the Streamlit app for managing a list
    of text items (like competencies or responsibilities).
    """
    # Initialize the list in session state if it doesn't exist
    if key_name not in st.session_state:
        st.session_state[key_name] = []
        
    st.subheader(label)

    # 1. Input for adding new item
    col1, col2 = st.columns([0.9, 0.1])
    with col1:
        # The key is used to store the value in session state.
        st.text_input(
            f"Add an item to {label}", 
            key=f"new_{key_name}_input", 
            label_visibility="collapsed", 
            placeholder="Type new item here..."
        )
    with col2:
        # Button to add item, using the callback function
        st.button(
            "Add", 
            key=f"add_{key_name}_btn", 
            on_click=add_item_callback,
            args=(key_name,), # Pass the list's key name to the callback
            use_container_width=True
        )

    # 2. Display existing items
    if st.session_state[key_name]:
        st.markdown("##### Current Items:")
        # Display each item with a "Remove" button
        for i, item in enumerate(st.session_state[key_name]):
            item_col, remove_col = st.columns([0.9, 0.1])
            with item_col:
                # Use markdown to display the item as a bulleted list item
                st.markdown(f"- {item}")
            
            with remove_col:
                # Remove button for each item. 
                # These remove buttons are also outside the main form.
                if st.button("X", key=f"remove_{key_name}_{i}_btn", help="Remove this item", type="primary", use_container_width=True):
                    st.session_state[key_name].pop(i)
                    st.experimental_rerun() # Force rerun after removing
    else:
        st.markdown("_No items added yet._")


# ─────────────────────────────────────────────
# 1. PAGE SETUP
# ─────────────────────────────────────────────
st.set_page_config(page_title="AI Talent Match Dashboard", layout="wide")
st.title("AI-Powered Talent Match Dashboard")

# Database connection (use your own URL or env var)
# We assume DATABASE_URL is hardcoded or set elsewhere if not in .env
DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/talent_match"
if not DATABASE_URL:
    st.error("Please set DATABASE_URL in environment variables.")
    st.stop()

# Initialize the engine once
try:
    engine = create_engine(DATABASE_URL)
except Exception as e:
    st.error(f"Database connection error: {e}")
    st.stop()


def parse_ids(ids):
    """Parses comma-separated IDs into a list of integers."""
    return [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]

# ─────────────────────────────────────────────
# 2. INPUT FORM (SINGLE SCROLL PAGE)
# ─────────────────────────────────────────────

# --- Role Information Inputs (Simple inputs that don't need callbacks) ---
st.header("Configure New Vacancy")

st.subheader("Role Details")
col1, col2 = st.columns(2)

with col1:
    role_name_input = st.text_input("Role Name", "Data Analyst", help="Ex. Marketing Manager", key="role_name_input")

with col2:
    job_level_input = st.selectbox("Job Level", ["Junior", "Mid-Level", "Senior"], index=1, key="job_level_input")

role_purpose_input = st.text_area(
    "Role Purpose",
    "Analyze business data to uncover trends and insights, ensuring optimal quality and cost efficiency.",
    help="1-2 sentences to describe role outcome",
    key="role_purpose_input"
)

st.subheader("Employee Benchmarking")
selected_ids_input = st.text_input(
    "Select Benchmark Employee IDs (max 3, comma-separated)", "312,335,175",
    help="These employees define the target profile for matching.",
    key="selected_ids_input"
)

st.markdown("---")

# --- Job Details (Manual Input) ---
st.header("Job Details")
st.info("Define the responsibilities, inputs, outputs, and competencies for the Job Profile and matching logic.")

# The list input components are intentionally outside the main st.form
list_input_component('key_responsibilities', 'Key Responsibilities')
st.markdown("---")
list_input_component('work_inputs', 'Work Inputs')
st.markdown("---")
list_input_component('work_outputs', 'Work Outputs')
st.markdown("---")
list_input_component('qualifications', 'Qualifications/Experience')
st.markdown("---")
list_input_component('competencies', 'Core Competencies for Matching')
st.markdown("---")


# --- Main Submission Form ---
# The form only contains the submit button and the inputs defined outside of the list components.
with st.form("vacancy_form"):
    
    # Store the values from session state into local variables for the submission logic
    role_name = st.session_state.role_name_input
    job_level = st.session_state.job_level_input
    role_purpose = st.session_state.role_purpose_input
    selected_ids = st.session_state.selected_ids_input
    
    submit = st.form_submit_button("Generate Job Description & Variable score")

# ─────────────────────────────────────────────
# 3. ON SUBMIT -> RUN SQL, DISPLAY RESULTS
# ─────────────────────────────────────────────
if submit:
    st.markdown("---") # Visual separator
    st.info("Running talent-matching and SQL logic...")
    
    # Check if necessary manual inputs were provided
    if not st.session_state.get('competencies', []):
        st.error("Please fill out the 'Core Competencies for Matching' list before generating.")
        st.stop()

    benchmarks = parse_ids(selected_ids)

    # -----------------------------------------------
    # 3A. JOB PROFILE PLACEHOLDER (Replaced AI generation with a simple placeholder)
    # -----------------------------------------------
    st.header("Job Profile")
    st.markdown(f"""
    This section previously contained an AI-generated Job Profile. 
    The core details are derived from your inputs:
    
    - **Role:** **{role_name}** ({job_level})
    - **Purpose:** *{role_purpose}*
    - **Core Competencies Used for Matching:** {', '.join(st.session_state.get('competencies', []))}
    """)
    
    st.markdown("---")


    # -----------------------------------------------
    # 3B. DATABASE & SQL LOGIC (UNCHANGED)
    # -----------------------------------------------
    
    # Insert or update new job vacancy config
    try:
        with engine.begin() as conn:
            # Note: We are not saving the detailed lists (Responsibilities, etc.) to the DB here, 
            # only the core job vacancy info and benchmarks.
            conn.execute(text("""
                INSERT INTO talent_benchmarks
                    (role_name, job_level, role_purpose, selected_talent_ids)
                VALUES (:r, :jl, :rp, :ids)
            """), {"r": role_name, "jl": job_level, "rp": role_purpose, "ids": benchmarks})
            job_vacancy_id = conn.execute(
                text("SELECT MAX(job_vacancy_id) FROM talent_benchmarks")
            ).scalar()

    except Exception as e:
        st.error(f"Database write error (talents_benchmarks table): {e}")
        st.stop()


    # Load and run Step 2 SQL
    try:
        # NOTE: Using a placeholder path as the real path is unknown/local to the user.
        # This will likely fail for the user unless they adjust the path.
        sql_file_path = "D:\Rakamin\queries\scripts.sql" 
        with open(sql_file_path, encoding="utf-8") as f:
            sql = text(f.read())
        
        # df contains multiple rows per employee (one per TGV)
        df = pd.read_sql(sql, engine, params={"job_vacancy_id": job_vacancy_id})

    except FileNotFoundError:
        st.error(f"SQL file not found: {sql_file_path}. Please check your path.")
        st.stop()
    except Exception as e:
        st.error(f"SQL query execution error: {e}")
        st.stop()


    if df.empty:
        st.warning("No data returned — check benchmark IDs or source tables.")
        # If df is empty, we stop here before trying to process it.
    
    
    # -----------------------------------------------
    # 4. RANKED TALENT LIST & DASHBOARD VISUALIZATION
    # -----------------------------------------------
    
    st.markdown("---")
    
    # --- IMPORTANT FIX: AGGREGATE TO ONE ROW PER EMPLOYEE ---
    if not df.empty:
        # 1. Create a clean DataFrame (df_final) with one row per employee
        df_final = (
            df.groupby("employee_id", as_index=False)
            .agg({
                'name': 'first',             # Keep the first name found
                'role': 'first',             # Keep the first role found
                'department': 'first',       # Keep the first department found
                'grade': 'first',            # Keep the first grade found
                'final_match_rate': 'max'    # Take the overall max/final match rate
            })
            .sort_values("final_match_rate", ascending=False)
        )
    
        # 4A. RANKED TALENT LIST
        st.header("Ranked Talent List")
        st.markdown("Display the output of your SQL logic (at minimum): `employee_id`, `name`, `final_match_rate`, and supporting fields.")
        
        # Display the top candidates from the clean, aggregated list
        df_ranked_display = df_final.head(10).copy()
        
        # Show only relevant columns for the final ranked list
        display_cols_final = [
            'name', 'final_match_rate', 'role', 'department', 'grade'
        ]
        
        # Apply the styling/formatting requested by the user
        st.dataframe(
            df_ranked_display[display_cols_final], 
            use_container_width=True,
            # --- START: CUSTOM STYLING FOR TABLE OUTPUT ---
            hide_index=True, # Hide the default Streamlit index
            column_config={
                "final_match_rate": st.column_config.ProgressColumn(
                    "Match Rate",
                    format="%d%%", # Format as percentage (assuming match rate is 0-100 or multiplied by 100)
                    min_value=0,
                    max_value=df_final['final_match_rate'].max() # Use the max value from the dataset for scaling
                ),
                "name": st.column_config.TextColumn("NAME"), # Rename column header to match screenshot
                "role": st.column_config.TextColumn("Role"), # Use 'Role' to match screenshot style
                "department": st.column_config.TextColumn("Department"),
                "grade": st.column_config.TextColumn("Job_level"), # Using grade as Job_level placeholder
            }
            # --- END: CUSTOM STYLING FOR TABLE OUTPUT ---
        )
        
        
        # 4B. DASHBOARD VISUALIZATION
        st.header("Dashboard Visualization")
        st.markdown("Provide clear, interactive visuals for each new input/job vacancy.")
        
        col_bar, col_hist = st.columns(2)
        
        with col_bar:
            # Match-rate distributions: Overall Match Rate per Employee
            # Use df_final which has one row per employee
            bar = px.bar(
                df_final.sort_values("final_match_rate", ascending=True),
                x="final_match_rate",
                y="employee_id",
                orientation="h",
                title="Overall Match Rate per Employee"
            )
            st.plotly_chart(bar, use_container_width=True)

        with col_hist:
            # Match-rate distributions: Distribution of Final Match Rates
            # Use df_final which has one row per employee
            hist = px.histogram(
                df_final, x="final_match_rate", nbins=20,
                title="Distribution of Final Match Rates"
            )
            st.plotly_chart(hist, use_container_width=True)

        # Average TGV Match Profile (Radar Chart)
        # This chart still needs the detailed, unaggregated data (df) to calculate TGV averages
        st.subheader("Benchmark vs Candidate Comparisons (Radar Plot)")
        tgv_df = (
            df.groupby(["tgv_name"], as_index=False)["tv_match_rate"].mean()
            .rename(columns={"tv_match_rate": "avg_match_rate"})
        )
        radar = px.line_polar(
            tgv_df, r="avg_match_rate", theta="tgv_name", line_close=True,
            title="Average TGV Match Profile"
        )
        st.plotly_chart(radar, use_container_width=True)
        
    else:
        st.warning("Cannot display ranked list or charts: Dataframe is empty.")