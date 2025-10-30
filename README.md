# AI-Powered Talent Match Dashboard
## Project Overview
This project implements an intelligent system designed to identify and rank internal talent for a specific job vacancy. It operates by defining a target role based on manual inputs and the performance/psychological profiles of benchmark employees.

The system performs the following key functions:
1. **Job Profile Configuration**: Allows HR/Hiring Managers to define core role requirements (Responsibilities, Competencies, etc.) and select high-performing benchmark employee IDs.
2. **SQL Logic & Matching**: Executes complex SQL logic to calculate a `final_match_rate` for all candidates against the desired profile, incorporating various data sources (performance, competencies, psychometrics).
3. **Interactive Dashboard**: Visualizes the ranked talent list and provides interactive charts (bar plots, histograms, radar plots) to explain the matching results.
## Prerequisites
Before running the application, ensure you have the following installed:
1. **Python 3.8+**
2. **PostgreSQL** (or another compatible database system) running locally or remotely.
3. **Access to the raw data** (tables: `employees`, `profiles_psych`, `papi_scores`, `strengths`, `performance_yearly`, `competencies_yearly`).
## Installation and Setup
### 1. Database Setup
The application connects to a PostgreSQL database.
1. **Create the Database**: Create a database named `talent_match`.
2. **Schema and Data Loading**: Ensure your database has the necessary tables (`employees`, `profiles_psych`, etc.) populated with the employee data, mirroring the structure used for your SQL logic.
3. **Create talent_benchmarks Table**: The Streamlit application requires a table to store new job configuration entries. Run the following SQL to create it:
```qy
CREATE TABLE IF NOT EXISTS talent_benchmarks (
    job_vacancy_id SERIAL PRIMARY KEY,
    role_name VARCHAR(255) NOT NULL,
    job_level VARCHAR(50) NOT NULL,
    role_purpose TEXT,
    selected_talent_ids INTEGER[] NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Python Environment
1. **Clone the Repository (If applicable)**:
```qy
# git clone <repository_url>
# cd <project_directory>
```

2. **Create and Activate a Virtual Environment**:
```qy
python -m venv venv
source venv/bin/activate  # On Linux/macOS
.\venv\Scripts\activate   # On Windows
```

3. **Install Dependencies**: You will need the following libraries. Assuming you used `psycopg2` for the PostgreSQL connection:
```qy
pip install streamlit pandas plotly sqlalchemy psycopg2-binary
```
*(Note: The AI-related libraries like `dotenv` and `requests` are no longer required, as the AI component was removed from `app.py`.)*
### 3. Configuration
The database connection string is defined directly within `app.py`. You must update the `DATABASE_URL` variable in `app.py` to match your credentials:
- File: `app.py`
- Line (approx): 110
- Variable: `DATABASE_URL`
```qy
# app.py (Line 110)
DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/talent_match"
```

### 4. Running the Application
1. **Ensure your database is running.**
2. **Ensure your virtual environment is active.**
3. **Run the Streamlit app:**
```qy
streamlit run app.py
```
4. The application will open in your web browser, typically at `http://localhost:8501`.

## Usage Instructions
1. **Configure New Vacancy**: Enter the role name, job level, purpose, and the comma-separated IDs of the benchmark employees.
2. **Define Job Details**: Use the interactive components to add `Key Responsibilities`, `Work Inputs/Outputs`, `Qualifications`, and `Core Competencies`.
3. **Generate**: Click "**Generate Job Description & Variable score**".
4. The app will save the configuration, run the `scripts.sql` query (ensure this file is in the specified location!), and display the **Ranked Talent List and Dashboard Visualization**.
