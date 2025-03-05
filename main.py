import re
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

PASSWORD_REQUIREMENTS = {
    2: {
        "length": 8,
        "description": "8+ chars with uppercase & lowercase",
        "generate_prompt": "Generate an 8 character password with mix of uppercase and lowercase letters"
    },
    3: {
        "length": 10,
        "description": "10+ chars with numbers",
        "generate_prompt": "10 character password with letters and at least 1 number"
    },
    4: {
        "length": 12,
        "description": "12+ chars with special characters",
        "generate_prompt": "12 character password with letters, numbers, and !@#$%^&*"
    },
    5: {
        "length": 14,
        "description": "14+ chars no spaces",
        "generate_prompt": "14 character password with mix of characters and no spaces"
    },
    6: {
        "length": 16,
        "description": "16+ unique chars",
        "generate_prompt": "16 character password with all character types and no repeats"
    }
}

def generate_password(score):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            f"Create a password that strictly follows these rules: {PASSWORD_REQUIREMENTS[score]['generate_prompt']}. Only output the password."
        )
        return response.text.strip()
    except Exception as e:
        return f"Generation error: {str(e)}"

def validate_password(password, selected_score):
    requirements = [
        (r'[A-Z]', "Uppercase letter"),
        (r'[a-z]', "Lowercase letter")
    ]
    
    for score in range(2, selected_score + 1):
        if score == 2:
            requirements.append((rf'^.{{{PASSWORD_REQUIREMENTS[2]["length"]},}}$', "8+ characters"))
        if score == 3:
            requirements.append((r'\d', "Number"))
            requirements.append((rf'^.{{{PASSWORD_REQUIREMENTS[3]["length"]},}}$', "10+ characters"))
        if score == 4:
            requirements.append((r'[!@#$%^&*]', "Special character"))
            requirements.append((rf'^.{{{PASSWORD_REQUIREMENTS[4]["length"]},}}$', "12+ characters"))
        if score == 5:
            requirements.append((r'^\S+$', "No spaces"))
            requirements.append((rf'^.{{{PASSWORD_REQUIREMENTS[5]["length"]},}}$', "14+ characters"))
        if score == 6:
            requirements.append((r'^(?!.*(.)\1)', "No repeating characters"))
            requirements.append((rf'^.{{{PASSWORD_REQUIREMENTS[6]["length"]},}}$', "16+ characters"))

    passed = []
    failed = []
    total_checks = len(requirements)
    
    for pattern, message in requirements:
        if re.search(pattern, password):
            passed.append(f"✅ {message}")
        else:
            failed.append(f"❌ {message}")

    return {
        "score": len(passed),
        "total": total_checks,
        "passed": passed,
        "failed": failed,
        "strength": get_strength_label(len(passed)/total_checks)
    }

def get_strength_label(ratio):
    if ratio >= 1.0: return "🔒 Extremely Strong"
    if ratio >= 0.9: return "🔑 Very Strong" 
    if ratio >= 0.75: return "🛡️ Strong"
    if ratio >= 0.5: return "⚠️ Moderate"
    return "🛑 Weak"

# Streamlit UI
st.title("🔐 Score-Based Password Generator")
st.write("### Security Score Configuration")

selected_score = st.slider(
    "Select password security score",
    min_value=2,
    max_value=6,
    value=4,
    help="Higher scores enforce stricter requirements"
)

with st.expander(f"Score {selected_score} Requirements"):
    st.write(PASSWORD_REQUIREMENTS[selected_score]["description"])
    if selected_score > 2:
        st.caption("Includes all requirements from lower scores")

st.write("### 🤖 Generate Password with AI")
col1, col2 = st.columns(2)

with col1:
    if st.button("Generate Password"):
        generated = generate_password(selected_score)
        st.session_state.generated_password = generated

with col2:
    if 'generated_password' in st.session_state:
        st.success("Generated Password:")
        st.code(st.session_state.generated_password)

st.write("### 👨🏻‍🦳 Create Custom Password")
user_password = st.text_input(
    "Enter Password", 
    type="password",
    help="Enter a password to test it based on the selected score!"
)

if user_password:
    validation = validate_password(user_password, selected_score)
    
    st.progress(validation["score"]/validation["total"])
    st.subheader(f"Security Rating: {validation['strength']}")
    st.caption(f"Passed {validation['score']} of {validation['total']} requirements")

    if validation["failed"]:
        st.write("#### Critical Improvements Needed")
        for issue in validation["failed"]:
            st.error(issue)
    
    if validation["passed"]:
        st.write("#### Successful Requirements")
        for success in validation["passed"]:
            st.success(success)
