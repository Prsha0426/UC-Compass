import streamlit as st
import pandas as pd
import os
from pathlib import Path

# Try to load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Gemini
try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="UC Compass",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 UC Compass")
st.subheader("Turn UC admissions data into a plan you can actually act on.")

st.write(
    "UC Compass combines UC admissions data with Gemini to help students "
    "understand their admissions landscape and identify concrete next steps."
)

st.divider()


# ============================================================
# LOAD DATA
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = BASE_DIR / "bay_area_modeling_table.csv"

try:
    df = pd.read_csv(DATA_FILE)
    DATA_LOADED = True
except Exception as e:
    DATA_LOADED = False
    df = pd.DataFrame()
    st.error(f"Could not load admissions data: {e}")


# ============================================================
# GET ONLY SCHOOLS ACTUALLY IN THE DATA
# ============================================================

if DATA_LOADED and "high_school" in df.columns:

    schools = (
        df["high_school"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    schools = sorted([s for s in schools if s])

else:
    schools = []


# ============================================================
# SESSION STATE
# ============================================================

if "analyzed" not in st.session_state:
    st.session_state.analyzed = False

if "saved_actions" not in st.session_state:
    st.session_state.saved_actions = []

if "gemini_result" not in st.session_state:
    st.session_state.gemini_result = None


# ============================================================
# PROFILE
# ============================================================

st.header("Build Your Student Profile")

col1, col2 = st.columns(2)

with col1:

    if schools:

        school = st.selectbox(
            "Current high school",
            schools,
            index=0
        )

    else:

        school = st.text_input(
            "Current high school",
            placeholder="Enter your high school"
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


# ============================================================
# ANALYZE BUTTON
# ============================================================

if st.button("Analyze My Path →", type="primary"):

    st.session_state.analyzed = True


# ============================================================
# ANALYSIS
# ============================================================

if st.session_state.analyzed:

    st.header(f"Your {target_campus} {major} Path")

    # --------------------------------------------------------
    # Find matching rows in the REAL dataset
    # --------------------------------------------------------

    if DATA_LOADED:

        school_data = df[
            df["high_school"].astype(str).str.strip() == school
        ]

        campus_data = school_data[
            school_data["campus"].astype(str).str.contains(
                target_campus,
                case=False,
                na=False
            )
        ]

        # If campus filtering finds nothing, use all school rows
        if len(campus_data) == 0:
            campus_data = school_data

    else:
        campus_data = pd.DataFrame()


    # --------------------------------------------------------
    # Calculate statistics
    # --------------------------------------------------------

    if len(campus_data) > 0:

        row = campus_data.iloc[0]

        admit_rate = row.get("admit_rate", None)
        applicant_gpa = row.get("applicant_gpa", None)
        admit_gpa = row.get("admit_gpa", None)
        enrollees = row.get("enrollees", None)
        applicants = row.get("applicants", None)
        admits = row.get("admits", None)

    else:

        admit_rate = None
        applicant_gpa = None
        admit_gpa = None
        enrollees = None
        applicants = None
        admits = None


    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    c1, c2, c3 = st.columns(3)

    with c1:

        if pd.notna(admit_rate):
            st.metric(
                "Historical Admit Rate",
                f"{float(admit_rate):.1f}%"
            )
        else:
            st.metric(
                "Historical Admit Rate",
                "N/A"
            )

    with c2:

        if pd.notna(applicant_gpa):
            st.metric(
                "Applicant GPA",
                f"{float(applicant_gpa):.2f}"
            )
        else:
            st.metric(
                "Applicant GPA",
                "N/A"
            )

    with c3:

        if pd.notna(admit_gpa):
            st.metric(
                "Admitted GPA",
                f"{float(admit_gpa):.2f}"
            )
        else:
            st.metric(
                "Admitted GPA",
                "N/A"
            )


    # --------------------------------------------------------
    # Data explanation
    # --------------------------------------------------------

    st.divider()

    st.subheader("📊 What the data says")

    if len(campus_data) > 0:

        st.info(
            f"The dataset contains admissions information associated with "
            f"**{school}**. These statistics describe historical outcomes "
            f"and should not be interpreted as a prediction of your admission."
        )

        with st.expander("View raw data used"):

            display_columns = [
                c for c in [
                    "fall_term",
                    "campus",
                    "high_school",
                    "applicants",
                    "admits",
                    "enrollees",
                    "admit_rate",
                    "applicant_gpa",
                    "admit_gpa",
                    "enrollee_gpa"
                ]
                if c in campus_data.columns
            ]

            st.dataframe(
                campus_data[display_columns],
                use_container_width=True
            )

    else:

        st.warning(
            "No matching admissions record was found for this school "
            "and campus combination."
        )


    # ========================================================
    # ACTION PLAN
    # ========================================================

    st.divider()

    st.subheader("🚀 What You Can Do")

    st.write(
        "Admissions data is not a prediction of your future. "
        "Use it to identify areas where you can deliberately build a stronger profile."
    )


    actions = {

        " Academics":
            f"Build the strongest academic foundation possible for {major}. "
            "Prioritize rigorous courses available at your school and focus on mastering them.",

        " Projects":
            f"Build a substantial project connected to {major}. "
            "A finished project with measurable impact is stronger than a long list "
            "of disconnected activities.",

        " Research":
            f"Look for research opportunities related to {major}, including "
            "university labs, local organizations, independent research, and "
            "summer programs.",

        " Competitions":
            f"Explore competitions where you can demonstrate skills in {major}. "
            "Focus on producing something measurable rather than simply participating.",

        " Impact":
            "Use your skills to solve a real problem in your school or community. "
            "Document what changed because of your work.",

        " Leadership":
            "Take ownership of something. Build a team, lead a project, "
            "or create a program that continues beyond you."
    }


    for title, description in actions.items():

        with st.expander(title):

            st.write(description)

            is_saved = title in st.session_state.saved_actions

            if st.button(
                "✓ Added to My Plan" if is_saved else "Add this to my plan",
                key=f"action_{title}"
            ):

                if title not in st.session_state.saved_actions:

                    st.session_state.saved_actions.append(title)

                else:

                    st.session_state.saved_actions.remove(title)

                st.rerun()


    # ========================================================
    # MY PLAN
    # ========================================================

    if st.session_state.saved_actions:

        st.divider()

        st.subheader(" My Plan")

        for action in st.session_state.saved_actions:

            st.success(action)


    # ========================================================
    # GEMINI OPPORTUNITY FINDER
    # ========================================================

    st.divider()

    st.subheader(" Gemini Opportunity Finder")

    st.write(
        "Gemini analyzes your profile and suggests opportunities, "
        "projects, research directions, and competitions that fit your goals."
    )


    # --------------------------------------------------------
    # API key
    # --------------------------------------------------------

    api_key = os.getenv("GEMINI_API_KEY")


    if not api_key:

        st.warning(
            "Gemini API key not found. Make sure GEMINI_API_KEY is set "
            "in your .env file."
        )

    elif not GEMINI_AVAILABLE:

        st.error(
            "The Google Gemini package is not installed in this Python environment."
        )

    else:

        if st.button(" Find Opportunities", type="secondary"):

            with st.spinner("Gemini is analyzing your profile..."):

                try:

                    client = genai.Client(
                        api_key=api_key
                    )

                    # IMPORTANT:
                    # The previous model caused a 404.
                    # This uses the model specified by your API error.
                    model_name = "gemini-3.6-flash"


                    # ------------------------------------------------
                    # Give Gemini REAL DATA from the selected school
                    # ------------------------------------------------

                    if len(campus_data) > 0:

                        data_for_gemini = campus_data[
                            [
                                c for c in [
                                    "fall_term",
                                    "campus",
                                    "high_school",
                                    "applicants",
                                    "admits",
                                    "enrollees",
                                    "admit_rate",
                                    "applicant_gpa",
                                    "admit_gpa",
                                    "enrollee_gpa"
                                ]
                                if c in campus_data.columns
                            ]
                        ].head(20).to_string(index=False)

                    else:

                        data_for_gemini = "No matching school data found."


                    prompt = f"""
You are the AI opportunity advisor inside UC Compass.

Student profile:
High school: {school}
Graduation year: {graduation_year}
Target UC campus: {target_campus}
Intended major: {major}

Here is REAL admissions data from the UC Compass dataset:

{data_for_gemini}

Using this information, create a concise, actionable opportunity plan.

Give:

1. Three concrete project ideas related to the student's major.
2. Three research directions or research opportunities they should investigate.
3. Three competition categories they should consider.
4. Three leadership or community-impact ideas.
5. A short explanation of how the admissions data should influence their strategy.

IMPORTANT:
- Do not claim that an activity guarantees admission.
- Do not invent statistics.
- Clearly distinguish between the provided admissions data and your recommendations.
- Prioritize specific actions over generic advice.
- Make the recommendations realistic for a high-school student.
"""


                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )


                    if response and response.text:

                        st.session_state.gemini_result = response.text

                    else:

                        st.error(
                            "Gemini returned an empty response."
                        )


                except Exception as e:

                    st.error(
                        f"Gemini request failed: {e}"
                    )


        # ----------------------------------------------------
        # Display Gemini response OUTSIDE the button block
        # ----------------------------------------------------

        if st.session_state.gemini_result:

            st.markdown("###  Your Personalized Opportunities")

            st.markdown(
                st.session_state.gemini_result
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "UC Compass | Built for the UC Admissions Data Challenge 2026"
)