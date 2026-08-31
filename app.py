import streamlit as st
import pandas as pd
import os
from pathlib import Path

# Gemini
try:
    from google import genai
except ImportError:
    genai = None

# ---------- PAGE SETUP ----------
st.set_page_config(
    page_title="UC Compass",
    page_icon="🎓",
    layout="wide"
)

# ---------- DATA LOADING ----------
BASE_DIR = Path(__file__).resolve().parent

possible_files = [
    BASE_DIR / "bay_area_modeling_table.csv",
    BASE_DIR / "data" / "bay_area_modeling_table.csv"
]

DATA_FILE = None

for file in possible_files:
    if file.exists():
        DATA_FILE = file
        break

if DATA_FILE is None:
    st.error(
        "Could not find bay_area_modeling_table.csv. "
        "Make sure the CSV is in the project folder or data folder."
    )
    st.stop()

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)
    return df

df = load_data()

# ---------- TITLE ----------
st.title("🎓 UC Compass")
st.subheader("Turn UC admissions data into a plan you can actually act on.")

st.write(
    "UC Compass uses admissions data from Bay Area high schools to help "
    "students understand admission patterns and identify concrete steps "
    "they can take to strengthen their path."
)

st.divider()

# ---------- RESEARCH QUESTION ----------
st.header("🔎 Research Question")

st.info(
    "**From 2019–2023, how did UC admission rates vary among students "
    "from Bay Area high schools, and which schools had admission rates "
    "above or below their expected rates?**"
)

st.write(
    "This question uses a specific time window, a population of interest, "
    "and a measurable metric."
)

q1, q2, q3 = st.columns(3)

with q1:
    st.metric("Time Window", "2019–2023")

with q2:
    st.metric("Population", "Bay Area UC Applicants")

with q3:
    st.metric("Metric", "Admission Rate")

st.divider()

# ---------- PROFILE ----------
st.header("👤 Build Your Student Profile")

col1, col2 = st.columns(2)

# Get only schools actually present in the dataset
school_values = (
    df["high_school"]
    .dropna()
    .astype(str)
    .drop_duplicates()
    .sort_values()
    .tolist()
)

with col1:

    if school_values:
        school = st.selectbox(
            "Current high school",
            school_values
        )
    else:
        school = st.text_input(
            "Current high school",
            placeholder="e.g. Mission San Jose High School"
        )

    graduation_year = st.selectbox(
        "Graduation year",
        [2027, 2028, 2029, 2030]
    )

with col2:

    target_campus = st.selectbox(
        "Target UC campus",
        [
            "Berkeley",
            "Davis",
            "Irvine",
            "Los Angeles",
            "Merced",
            "Riverside",
            "San Diego",
            "Santa Barbara",
            "Santa Cruz"
        ]
    )

    major = st.selectbox(
        "Intended major",
        [
            "Computer Science",
            "Engineering",
            "Physical Sciences/Math",
            "Life Sciences",
            "Social Sciences",
            "Arts & Humanities",
            "Business",
            "Public Health",
            "Architecture",
            "Undeclared"
        ]
    )

st.divider()

# ---------- ANALYSIS ----------
if st.button("Analyze My Path →", type="primary"):

    st.session_state["analyzed"] = True

if st.session_state.get("analyzed", False):

    st.header(f"📊 Your {target_campus} {major} Path")

    # ---------- FILTER SCHOOL DATA ----------
    school_df = df[df["high_school"] == school].copy()

    # Try to filter to the selected campus if campus exists
    if "campus" in school_df.columns:
        campus_df = school_df[
            school_df["campus"].astype(str).str.contains(
                target_campus,
                case=False,
                na=False
            )
        ]

        if not campus_df.empty:
            school_df = campus_df

    # ---------- CALCULATE METRICS ----------
    if not school_df.empty:

        applicants = school_df["applicants"].sum()
        admits = school_df["admits"].sum()

        if applicants > 0:
            admit_rate = (admits / applicants) * 100
        else:
            admit_rate = 0

        if "admit_gpa" in school_df.columns:
            gpa_values = pd.to_numeric(
                school_df["admit_gpa"],
                errors="coerce"
            ).dropna()
        else:
            gpa_values = pd.Series(dtype=float)

        if len(gpa_values) > 0:
            gpa_low = gpa_values.quantile(0.25)
            gpa_high = gpa_values.quantile(0.75)
        else:
            gpa_low = None
            gpa_high = None

        if "expected_admit_rate" in school_df.columns:
            expected_values = pd.to_numeric(
                school_df["expected_admit_rate"],
                errors="coerce"
            ).dropna()

            expected_rate = (
                expected_values.mean()
                if len(expected_values) > 0
                else None
            )
        else:
            expected_rate = None

    else:
        applicants = 0
        admits = 0
        admit_rate = 0
        gpa_low = None
        gpa_high = None
        expected_rate = None

    # ---------- METRICS ----------
    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric(
            "Admission Rate",
            f"{admit_rate:.1f}%"
        )

    with c2:
        if gpa_low is not None:
            st.metric(
                "Admitted GPA P25",
                f"{gpa_low:.2f}"
            )
        else:
            st.metric(
                "Admitted GPA P25",
                "N/A"
            )

    with c3:
        if gpa_high is not None:
            st.metric(
                "Admitted GPA P75",
                f"{gpa_high:.2f}"
            )
        else:
            st.metric(
                "Admitted GPA P75",
                "N/A"
            )

    st.divider()

    # ---------- RESEARCH FINDING ----------
    st.subheader("📈 What the data says")

    if expected_rate is not None:

        difference = admit_rate - expected_rate

        if difference > 0:
            direction = "above"
        elif difference < 0:
            direction = "below"
        else:
            direction = "approximately equal to"

        st.success(
            f"For **{school}**, the observed admission rate was "
            f"**{admit_rate:.1f}%**, compared with an expected admission "
            f"rate of **{expected_rate:.1f}%**. The observed rate was "
            f"**{abs(difference):.1f} percentage points {direction}** "
            f"the expected rate."
        )

    else:
        st.info(
            f"The dataset contains information for **{school}**, but an "
            "expected admission rate was not available for this selection."
        )

    st.caption(
        "Admission rates describe historical patterns. They should not "
        "be interpreted as a prediction of an individual student's outcome."
    )

    st.divider()

    # ---------- ACTION PLAN ----------
    st.subheader("🚀 What You Can Do")

    st.write(
        "Admissions data should not be treated as a prediction of your future. "
        "Instead, use it to identify areas where you can build a stronger profile."
    )

    actions = {
        "📚 Academics":
            f"Build the strongest academic foundation you can for {major}. "
            "Prioritize rigorous courses that are available to you.",

        "🔬 Projects":
            f"Build a substantial project connected to {major}. "
            "A finished project with measurable impact is stronger than "
            "a long list of disconnected activities.",

        "🧪 Research":
            f"Look for research opportunities related to {major}, "
            "including university labs, local organizations, and independent research.",

        "🏆 Competitions":
            f"Explore competitions where you can demonstrate skills in {major}. "
            "Aim to create something measurable rather than simply participate.",

        "🌎 Impact":
            "Use your skills to solve a real problem in your school or community. "
            "Document what changed because of your work.",

        "👥 Leadership":
            "Take ownership of something. Build a team, lead a project, "
            "or create a program that continues beyond you."
    }

    for title, description in actions.items():

        with st.expander(title):

            st.write(description)

            checkbox_key = f"plan_{title}"

            selected = st.checkbox(
                "Add this to my plan",
                key=checkbox_key
            )

            if selected:
                st.success("✓ Added to your plan")

    # ---------- PERSONAL PLAN ----------
    selected_actions = []

    for title in actions:
        if st.session_state.get(f"plan_{title}", False):
            selected_actions.append(title)

    if selected_actions:

        st.divider()

        st.subheader("📋 My Plan")

        for action in selected_actions:
            st.write(f"✅ {action}")

    # ---------- GEMINI ----------
    st.divider()

    st.subheader("🤖 Gemini Opportunity Finder")

    st.write(
        "Use Gemini to generate opportunity ideas based on your "
        "school, target UC campus, intended major, and areas you want "
        "to strengthen."
    )

    if st.button("🔎 Find My Opportunities"):

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            st.error(
                "Gemini API key not found. Make sure GEMINI_API_KEY "
                "is configured in your environment."
            )

        elif genai is None:
            st.error(
                "The Google GenAI package is not installed in this environment."
            )

        else:

            try:

                client = genai.Client(api_key=api_key)

                prompt = f"""
You are an educational opportunity advisor.

Student profile:
- High school: {school}
- Graduation year: {graduation_year}
- Target UC campus: {target_campus}
- Intended major: {major}

Generate 5 concrete opportunity categories the student should explore.

Prioritize:
1. Research
2. Engineering or STEM projects
3. Competitions
4. Leadership
5. Summer programs or internships

For each opportunity:
- Give the opportunity type
- Explain why it fits this student
- Give a concrete next step

Do not claim that the student is guaranteed admission.
Do not invent specific programs or deadlines.
"""

                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )

                st.success("Opportunities found!")

                st.markdown(response.text)

            except Exception as e:

                st.error(
                    f"Gemini request failed: {e}"
                )

else:

    st.info(
        "Enter your profile above and click **Analyze My Path →**"
    )

# ---------- FOOTER ----------
st.divider()

st.caption(
    "UC Compass | Built for the UC Admissions Data Challenge 2026"
)
