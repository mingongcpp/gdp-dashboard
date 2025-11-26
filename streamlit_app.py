import streamlit as st
import pandas as pd
from io import StringIO

# =========================
#  Streamlit – Dictionary Classifier
# =========================

st.set_page_config(page_title="Dictionary Classifier", layout="wide")

st.title("🔍 Dictionary Classifier")

st.markdown(
    """
This app applies simple dictionary-based classification on a text column called **`Statement`**.

**Steps:**
1. Upload a CSV file containing a `Statement` column.  
2. Edit the default tactic dictionaries if you like.  
3. Run the classifier and download the annotated CSV.
"""
)

# 1️⃣ ---- DEFAULT DICTIONARIES (same as your script) ----
DEFAULT_DICTIONARIES = {
    "urgency_marketing": {
        "limited", "limited time", "limited run", "limited edition", "order now",
        "last chance", "hurry", "while supplies last", "before they're gone",
        "selling out", "selling fast", "act now", "don't wait", "today only",
        "expires soon", "final hours", "almost gone"
    },
    "exclusive_marketing": {
        "exclusive", "exclusively", "exclusive offer", "exclusive deal",
        "members only", "vip", "special access", "invitation only",
        "premium", "privileged", "limited access", "select customers",
        "insider", "private sale", "early access"
    }
}

# Keep a mutable copy in session_state
if "dictionaries" not in st.session_state:
    st.session_state["dictionaries"] = {
        k: sorted(list(v)) for k, v in DEFAULT_DICTIONARIES.items()
    }

dictionaries = st.session_state["dictionaries"]

# 2️⃣ ---- FILE UPLOAD ----
st.subheader("1. Upload your CSV")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        df = None
else:
    df = None

if df is not None:
    st.write("Preview of uploaded data:")
    st.dataframe(df.head(), use_container_width=True)

    if "Statement" not in df.columns:
        st.error("❌ No 'Statement' column found in the uploaded file. Please include a column named `Statement`.")
else:
    st.info("Upload a CSV to continue.")

# 3️⃣ ---- DICTIONARY EDITOR ----
st.subheader("2. Edit tactic dictionaries")

st.markdown("Each tactic is a **group of keywords/phrases**. Enter keywords separated by commas.")

# Existing tactic editors
for tactic in list(dictionaries.keys()):
    with st.expander(f"Tactic: `{tactic}`", expanded=False):
        current_keywords = ", ".join(dictionaries[tactic])
        new_value = st.text_area(
            f"Keywords for `{tactic}` (comma-separated)",
            value=current_keywords,
            key=f"text_{tactic}",
            height=100
        )
        # Update keywords from textarea
        dictionaries[tactic] = [
            kw.strip() for kw in new_value.split(",") if kw.strip()
        ]

# Add a new tactic
st.markdown("---")
st.markdown("**Add a new tactic**")

col_new1, col_new2 = st.columns([1, 3])
with col_new1:
    new_tactic_name = st.text_input("New tactic name", value="", placeholder="e.g., scarcity_marketing")
with col_new2:
    new_tactic_keywords = st.text_input("Keywords for new tactic (comma-separated)", value="")

if st.button("Add tactic"):
    if not new_tactic_name.strip():
        st.warning("Please provide a name for the new tactic.")
    elif new_tactic_name in dictionaries:
        st.warning("That tactic name already exists.")
    else:
        dictionaries[new_tactic_name] = [
            kw.strip()
            for kw in new_tactic_keywords.split(",")
            if kw.strip()
        ]
        st.success(f"Added tactic `{new_tactic_name}`.")
        # trigger re-render with updated state
        st.experimental_rerun()

st.session_state["dictionaries"] = dictionaries

# Convert to sets for classification logic (like original script)
dicts_for_classification = {k: set(v) for k, v in dictionaries.items()}

# 4️⃣ ---- CLASSIFICATION FUNCTION ----
def classify(text: str, dictionaries: dict) -> dict:
    """Return {tactic: {present,bool; count,int; matches,list}}."""
    text_lower = str(text).lower()
    result = {}
    for tactic, keywords in dictionaries.items():
        matches = [kw for kw in keywords if kw.lower() in text_lower]
        result[tactic] = {
            "present": bool(matches),
            "count": len(matches),
            "matches": matches,
        }
    return result

# 5️⃣ ---- RUN CLASSIFICATION ----
st.subheader("3. Run classification")

if df is not None and "Statement" in df.columns:
    if st.button("🔎 Classify statements"):
        # Apply classification
        df["classification"] = df["Statement"].apply(
            lambda s: classify(s, dicts_for_classification)
        )

        # Flatten the nested dict
        for tactic in dicts_for_classification:
            df[f"{tactic}_present"] = df["classification"].apply(
                lambda d: d[tactic]["present"]
            )
            df[f"{tactic}_count"] = df["classification"].apply(
                lambda d: d[tactic]["count"]
            )
            df[f"{tactic}_matches"] = df["classification"].apply(
                lambda d: ", ".join(d[tactic]["matches"])
            )

        st.success("✅ Classification complete!")

        st.markdown("### Classified data preview")
        st.dataframe(df, use_container_width=True)

        # 6️⃣ ---- DOWNLOAD RESULT ----
        st.markdown("### 4. Download classified CSV")

        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_bytes = csv_buffer.getvalue().encode("utf-8")

        st.download_button(
            label="⬇️ Download `classified_output.csv`",
            data=csv_bytes,
            file_name="classified_output.csv",
            mime="text/csv",
        )
else:
    st.info("Once a valid CSV (with `Statement` column) is uploaded, you can run classification here.")
