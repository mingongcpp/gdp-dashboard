import streamlit as st
import pandas as pd
from io import StringIO

# =========================================
# Streamlit App with Sidebar Navigation
# =========================================

st.set_page_config(page_title="Dictionary Classifier", layout="wide")

# --------- Initialize session state ---------
if "df" not in st.session_state:
    st.session_state["df"] = None

if "dictionaries" not in st.session_state:
    st.session_state["dictionaries"] = {
        "urgency_marketing": sorted([
            "limited", "limited time", "limited run", "limited edition", "order now",
            "last chance", "hurry", "while supplies last", "before they're gone",
            "selling out", "selling fast", "act now", "don't wait", "today only",
            "expires soon", "final hours", "almost gone"
        ]),
        "exclusive_marketing": sorted([
            "exclusive", "exclusively", "exclusive offer", "exclusive deal",
            "members only", "vip", "special access", "invitation only",
            "premium", "privileged", "limited access", "select customers",
            "insider", "private sale", "early access"
        ])
    }

# --------- Sidebar Navigation ---------
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio(
    "Go to page:",
    ["Home", "Upload Data", "Edit Dictionaries", "Run Classification", "Download Results"]
)

# =========================================
#  Classification Function
# =========================================
def classify(text: str, dictionaries: dict) -> dict:
    """Return {tactic: {present,bool; count,int; matches,list}}."""
    text_lower = str(text).lower()
    result = {}

    for tactic, keywords in dictionaries.items():
        matches = [kw for kw in keywords if kw.lower() in text_lower]
        result[tactic] = {
            "present": bool(matches),
            "count": len(matches),
            "matches": matches
        }

    return result


# =========================================
#  HOME PAGE
# =========================================
if page == "Home":
    st.title("🔍 Dictionary Classifier")
    st.markdown("""
    Welcome!  
    This app classifies text using editable keyword dictionaries.

    **Workflow:**
    1️⃣ Upload a CSV containing a `Statement` column  
    2️⃣ Edit the keyword dictionaries  
    3️⃣ Run the classifier  
    4️⃣ Download the annotated file  
    """)

# =========================================
#  UPLOAD DATA PAGE
# =========================================
elif page == "Upload Data":
    st.title("📤 Upload Your Data")

    uploaded = st.file_uploader("Upload a CSV file", type=["csv"])

    if uploaded:
        try:
            df = pd.read_csv(uploaded)
            st.session_state["df"] = df
        except Exception as e:
            st.error(f"Error reading CSV: {e}")

    if st.session_state["df"] is not None:
        df = st.session_state["df"]
        st.write("Preview of uploaded data:")
        st.dataframe(df.head(), use_container_width=True)

        if "Statement" not in df.columns:
            st.error("❌ The CSV must include a `Statement` column.")
        else:
            st.success("File successfully loaded!")

# =========================================
#  EDIT DICTIONARIES PAGE
# =========================================
elif page == "Edit Dictionaries":
    st.title("📚 Edit Dictionaries")

    dictionaries = st.session_state["dictionaries"]

    st.markdown("Edit the keywords for each tactic below (comma-separated).")

    # Existing dictionaries
    for tactic in list(dictionaries.keys()):
        with st.expander(f"Tactic: `{tactic}`"):
            current = ", ".join(dictionaries[tactic])
            new_value = st.text_area(
                f"Keywords for `{tactic}` (comma-separated)",
                value=current,
                key=f"edit_{tactic}",
                height=120
            )
            dictionaries[tactic] = [
                k.strip() for k in new_value.split(",") if k.strip()
            ]

    # Add a new tactic
    st.markdown("---")
    st.subheader("➕ Add a new tactic")

    col1, col2 = st.columns([1, 3])
    with col1:
        new_name = st.text_input("Tactic name")
    with col2:
        new_keywords = st.text_input("Keywords (comma-separated)")

    if st.button("Add tactic"):
        if not new_name.strip():
            st.warning("Enter a tactic name.")
        elif new_name in dictionaries:
            st.warning("This tactic already exists.")
        else:
            dictionaries[new_name] = [
                k.strip() for k in new_keywords.split(",") if k.strip()
            ]
            st.success(f"Added tactic `{new_name}`.")
            st.session_state["dictionaries"] = dictionaries
            st.experimental_rerun()

    st.session_state["dictionaries"] = dictionaries


# =========================================
#  RUN CLASSIFICATION PAGE
# =========================================
elif page == "Run Classification":
    st.title("⚙️ Run Classification")

    df = st.session_state["df"]
    dictionaries = {k: set(v) for k, v in st.session_state["dictionaries"].items()}

    if df is None:
        st.warning("Upload a dataset first.")
    elif "Statement" not in df.columns:
        st.error("❌ The CSV must include a `Statement` column.")
    else:
        if st.button("Run classifier"):
            df["classification"] = df["Statement"].apply(
                lambda s: classify(s, dictionaries)
            )

            # Flatten results
            for tactic in dictionaries:
                df[f"{tactic}_present"] = df["classification"].apply(lambda d: d[tactic]["present"])
                df[f"{tactic}_count"] = df["classification"].apply(lambda d: d[tactic]["count"])
                df[f"{tactic}_matches"] = df["classification"].apply(lambda d: ", ".join(d[tactic]["matches"]))

            st.session_state["df"] = df
            st.success("Classification complete!")

        if st.session_state["df"] is not None and "classification" in st.session_state["df"]:
            st.dataframe(st.session_state["df"].head(), use_container_width=True)

# =========================================
#  DOWNLOAD RESULTS PAGE
# =========================================
elif page == "Download Results":
    st.title("⬇️ Download Results")

    df = st.session_state["df"]

    if df is None or "classification" not in df:
        st.warning("You must run classification first.")
    else:
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)

        st.download_button(
            "⬇️ Download `classified_output.csv`",
            data=csv_buffer.getvalue(),
            file_name="classified_output.csv",
            mime="text/csv"
        )

        st.success("File ready for download!")
