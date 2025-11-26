import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Dictionary Classifier", layout="wide")

# -----------------------
# Default Dictionaries
# -----------------------
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

# -----------------------
# Streamlit UI
# -----------------------
st.title("🔍 Dictionary Classifier (Streamlit Version)")

st.markdown("""
Upload a dataset, edit the keyword dictionaries, and classify each text statement.
Your CSV **must contain a column named `Statement`**.
""")


# -----------------------
# 1. File Upload
# -----------------------
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

# -----------------------
# 2. Dictionary Editor
# -----------------------
st.subheader("📚 Edit Dictionaries")

dict_text = st.text_area(
    "Dictionaries (editable JSON)",
    value=json.dumps(DEFAULT_DICTIONARIES, indent=4),
    height=300
)

try:
    dictionaries = json.loads(dict_text)
    # Ensure all keyword lists become sets
    dictionaries = {k: set(v) for k, v in dictionaries.items()}
except:
    st.error("⚠️ Dictionary JSON is invalid. Fix it before continuing.")
    st.stop()


# -----------------------
# Classification Function
# -----------------------
def classify(text: str, dictionaries: dict) -> dict:
    text_lower = str(text).lower()
    result = {}
    for tactic, keywords in dictionaries.items():
        matches = [kw for kw in keywords if kw in text_lower]
        result[tactic] = {
            "present": bool(matches),
            "count": len(matches),
            "matches": matches
        }
    return result


# -----------------------
# 3. Process the File
# -----------------------
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if "Statement" not in df.columns:
        st.error("❌ No 'Statement' column found in your file.")
        st.stop()

    st.success("File loaded successfully!")

    # Apply classification
    st.subheader("🔎 Running Classification...")
    df["classification"] = df["Statement"].apply(lambda s: classify(s, dictionaries))

    # Expand classification to flat columns
    for tactic in dictionaries:
        df[f"{tactic}_present"] = df["classification"].apply(lambda d: d[tactic]["present"])
        df[f"{tactic}_count"] = df["classification"].apply(lambda d: d[tactic]["count"])
        df[f"{tactic}_matches"] = df["classification"].apply(lambda d: ", ".join(d[tactic]["matches"]))

    # Display results
    st.subheader("📄 Classified Data Preview")
    st.dataframe(df, use_container_width=True)

    # Download button
    st.subheader("⬇️ Download Classified CSV")
    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download classified_output.csv",
        data=csv_data,
        file_name="classified_output.csv",
        mime="text/csv"
    )
else:
    st.info("➡️ Upload a CSV file to begin.")
