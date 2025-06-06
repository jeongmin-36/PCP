"""Interactive Streamlit app ‑ users author **Section 1** first, then the app
parallel‑generates the remaining KOICA PCP sections (2.x – 5) using OpenAI.

Run:
> export OPENAI_API_KEY="sk‑..."
> pip install streamlit openai
> streamlit run streamlit_pcp_generator.py
"""

from __future__ import annotations

import os
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Tuple
from openai import OpenAI
import os
import streamlit as st
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))




# ------------------------------ CONFIG ---------------------------------------
MODEL = "gpt-4o" 

SUBSECTIONS: Dict[str, str] = {
    "2.1 Situation Analysis": "Explain the current social, economic, and sector‑specific context relevant to the project. Provide key statistics where possible.",
    "2.2 Country Development Strategies and Policies": "Describe national strategies, policies, or plans that align with the project objective. Reference policy names and publication years.",
    "2.3 Justification for Intervention": "Why is KOICA support necessary? Highlight problem magnitude, KOICA’s comparative advantage, and alignment with SDGs.",
    "2.4 Lessons Learned": "Summarize lessons from similar past projects (KOICA or other donors). Include at least two concrete lessons.",
    "3 Project Description": "Provide Objective, Expected Outcomes, Outputs, and Key Activities (high‑level workplan). Use a bullet list for Outputs and Activities.",
    "4 Stakeholder Analysis": "Identify target beneficiaries (with numbers) and other stakeholders with their roles and interests.",
    "5 Project Management and Implementation": "Outline governance and coordination mechanisms (steering committee, executing agency, reporting). State indicative timeline and risks."  # noqa:E501
}

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_subsection(name: str, instruction: str, section1: str, language: str) -> Tuple[str, str]:
    """Call OpenAI to create *one* subsection using Section 1 as context."""
    
    prompt = textwrap.dedent(
        f"""
        You are an international development expert preparing a KOICA bilateral Project/Program Concept Paper.
        The user already drafted SECTION 1. Using that section **only as context**, write **{name}** in {language}.

        Guidelines:
        {instruction}

        SECTION 1 (verbatim):
        {section1.strip()}
        """
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that drafts concept papers for KOICA projects."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )

    generated_text = response.choices[0].message.content
    return name, generated_text

def assemble_pcp(section1: str, generated: Dict[str, str]) -> str:
    """Concatenate Section 1 + generated subsections into full PCP markdown."""
    lines = ["# Project/Program Concept Paper\n", "## Section 1. Basic Project Information\n", section1.strip(), "\n"]
    for key in SUBSECTIONS:
        if key in generated:
            lines.append(f"## {key}\n")
            lines.append(generated[key])
            lines.append("\n")
    return "\n".join(lines)

# ------------------------------ UI ------------------------------------------

st.set_page_config(page_title="KOICA PCP Generator", page_icon="📄", layout="centered")
st.title("📄 KOICA PCP Generator (Section 1 → AI remaining)")

if not openai.api_key:
    st.error("OPENAI_API_KEY environment variable not set.")
    st.stop()

with st.form(key="section1_form"):
    st.markdown("### ✍️ Write **Section 1. Basic Project Information**")
    section1_text = st.text_area(
        "Paste or write Section 1 here (markdown supported)", height=300, key="section1"
    )
    language = st.selectbox("Output language", ["English", "한국어"], key="lang")
    submitted = st.form_submit_button("Generate Remaining Sections 🚀")

if submitted and section1_text.strip():
    st.info("Generating Sections 2–5 in parallel. This may take ~30‑60 s…")

    progress = st.progress(0)
    results: Dict[str, str] = {}
    total = len(SUBSECTIONS)

    with ThreadPoolExecutor(max_workers=min(6, total)) as executor:
        futures = {
            executor.submit(generate_subsection, name, instr, section1_text, language): name
            for name, instr in SUBSECTIONS.items()
        }
        completed = 0
        for future in as_completed(futures):
            name, text = future.result()
            results[name] = text
            completed += 1
            progress.progress(completed / total)
            st.success(f"Done: {name}")

    full_pcp = assemble_pcp(section1_text, results)

    st.markdown("---")
    st.markdown("## 📄 Generated PCP Preview")
    st.text_area("Full PCP", full_pcp, height=1000)

    st.download_button(
        "💾 Download as Markdown", data=full_pcp, file_name="pcp.md", mime="text/markdown"
    )

elif submitted:
    st.warning("Section 1 cannot be empty. Please write it first.")
