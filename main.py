import os
import streamlit as st
import textwrap
from typing import Tuple
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI

# -------------------- SETUP --------------------
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.stop("❌ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
client = OpenAI(api_key=api_key)

# -------------------- SECTION 1 INPUT --------------------
st.title("📄 KOICA Project Concept Generator")
st.markdown("Fill in the basic info for **SECTION 1**. Leave fields blank if unsure.")

with st.form("section1_form"):
    country = st.text_input("Country", placeholder="e.g., Nepal")
    title = st.text_input("Title", placeholder="e.g., Digital Agriculture Enhancement")
    location = st.text_input("Location(s)", placeholder="e.g., Provinces 3 and 4")
    duration = st.text_input("Duration", placeholder="e.g., 36 months (2027–2030)")
    budget = st.text_area("Budget (total)", placeholder="KOICA: USD 3M...\nCo-funding: USD 500K...")
    objectives = st.text_area("Objectives", placeholder="To strengthen digital capacity of farmers...")
    beneficiary = st.text_input("Beneficiary", placeholder="5,000 farmers, local gov’t")
    organization = st.text_area("Implementing Organization", placeholder="Ministry of Agriculture, etc.")

    submitted = st.form_submit_button("Generate Remaining Sections 🚀")

# -------------------- BUILD SECTION 1 --------------------
if submitted:
    section1 = f"""**SECTION 1. BASIC PROJECT INFORMATION**

- **Country**: {country}
- **Title**: {title}
- **Location(s)**: {location}
- **Duration**: {duration}
- **Budget (total)**: {budget}
- **Objectives**: {objectives}
- **Beneficiary**: {beneficiary}
- **Implementing Organization**: {organization}
"""

    st.markdown("### ✅ SECTION 1 Preview")
    st.markdown(section1)

    # -------------------- SECTION 2+ DEFINITIONS --------------------
    subsections = {
        "2.1 Development Problem": "Briefly describe the core development issue the project aims to solve.",
        "2.2 National Development Plan Alignment": "Explain how the project aligns with the country’s development strategy.",
        "2.3 KOICA Priority Alignment": "Explain how the project aligns with KOICA’s priority areas.",
        "3. Expected Results": "Summarize expected outcomes and outputs.",
        "4. Sustainability and Risk": "Describe sustainability plan and major risks.",
        "5. Lessons Learned": "Incorporate lessons from past projects or evaluations."
    }

    language = "English"

    def generate_subsection(name: str, instruction: str, section1_text: str, language: str) -> Tuple[str, str]:
        prompt = textwrap.dedent(f"""
        You are an international development expert preparing a KOICA bilateral Project/Program Concept Paper.
        The user already drafted SECTION 1. Using that section **only as context**, write **{name}** in {language}.

        Guidelines:
        {instruction}

        SECTION 1 (verbatim):
        {section1_text.strip()}
        """)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that drafts KOICA concept papers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        return name, response.choices[0].message.content

    # -------------------- GENERATE SECTIONS IN PARALLEL --------------------
    st.markdown("### 🛠 Generating sections 2–5...")
    results = []

    with st.spinner("Working..."):
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(generate_subsection, name, inst, section1, language)
                for name, inst in subsections.items()
            ]
            for future in futures:
                results.append(future.result())

    # -------------------- DISPLAY OUTPUT --------------------
    full_output = section1 + "\n\n"
    for name, content in results:
        st.markdown(f"### {name}")
        st.markdown(content)
        full_output += f"\n\n### {name}\n\n{content}"

    # -------------------- DOWNLOAD --------------------
    st.download_button(
        label="💾 Download as Markdown",
        data=full_output,
        file_name="KOICA_PCP.md",
        mime="text/markdown"
    )
