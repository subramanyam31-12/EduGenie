# app.py
# Simple User Login (Replace with database for real use)
import streamlit as st
import random
import json
from gtts import gTTS
from io import BytesIO
import base64
import os
from difflib import get_close_matches
from collections import defaultdict
import time  # For tracking time spent
from ai_models import analyze_learning_style, analyze_strengths_weaknesses, generate_personalized_path  # Import the updated function

# Optional Rain Animation
try:
    from streamlit_extras.let_it_rain import rain
    extras_available = True
except ImportError:
    extras_available = False

# 🌐 Page Config
st.set_page_config(page_title="EduGenie AI", page_icon="🧠", layout="wide")

# ✨ Header
st.markdown("<h1 style='text-align: center; color: cyan;'>✨ EduGenie AI – Your Personalized Learning Companion</h1>", unsafe_allow_html=True)
if extras_available:
    rain(emoji="📚", font_size=40, falling_speed=5, animation_length="infinite")
st.markdown("---")

# 🔧 Sidebar
with st.sidebar:
    st.header("📚 Settings")
    name = st.text_input("👤 Enter Your Name:")
    subject = st.selectbox("📘 Choose Subject", ["Physics", "Biology", "Mathematics", "Chemistry"])
    st.caption("🚀 Built by Subramanyam")

    # Learning Style Questionnaire (Simple Example)
    st.subheader("🎨 Learning Style (Optional)")
    if "learning_style" not in st.session_state:
        st.session_state.learning_style = {}

    def update_learning_style(style, value):
        st.session_state.learning_style[name] = st.session_state.learning_style.get(name, {})
        st.session_state.learning_style[name]["preferred_" + style] = value

    visual_preference = st.slider("Prefer learning through visuals?", 1, 5, 3)
    update_learning_style("visual", visual_preference)
    auditory_preference = st.slider("Prefer learning through listening?", 1, 5, 3)
    update_learning_style("auditory", auditory_preference)
    reading_writing_preference = st.slider("Prefer learning through reading/writing?", 1, 5, 3)
    update_learning_style("reading_writing", reading_writing_preference)
    kinesthetic_preference = st.slider("Prefer hands-on learning?", 1, 5, 3)
    update_learning_style("kinesthetic", kinesthetic_preference)

# Initialize session state for user data and interaction tracking
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "interaction_data" not in st.session_state:
    st.session_state.interaction_data = {}
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = {}
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "inferred_learning_style" not in st.session_state:
    st.session_state.inferred_learning_style = {}
if "strengths" not in st.session_state:
    st.session_state.strengths = {}
if "weaknesses" not in st.session_state:
    st.session_state.weaknesses = {}

def record_quiz_data(name, subject, questions, user_answers, score, correct_answers):
    if name not in st.session_state.quiz_data:
        st.session_state.quiz_data[name] = {}
    if subject not in st.session_state.quiz_data[name]:
        st.session_state.quiz_data[name][subject] = {"quiz_history": []}
    st.session_state.quiz_data[name][subject]["quiz_history"].append({
        "questions": [q["question"] for q in questions],
        "user_answers": user_answers,
        "score": score,
        "correct_answers": correct_answers,
        "concepts_tested": [q.get("concept", "General") for q in questions]
    })
    # Also update the user_data for the personalized learning path (as before)
    if name not in st.session_state.user_data:
        st.session_state.user_data[name] = {}
    if subject not in st.session_state.user_data[name]:
        st.session_state.user_data[name][subject] = {"quiz_history": []}
    st.session_state.user_data[name][subject]["quiz_history"].append({
        "questions": [q["question"] for q in questions],
        "user_answers": user_answers,
        "score": score,
        "correct_answers": correct_answers,
        "concepts_tested": [q.get("concept", "General") for q in questions]
    })

def record_interaction(name, event, details=None):
    if name not in st.session_state.interaction_data:
        st.session_state.interaction_data[name] = []
    st.session_state.interaction_data[name].append({"timestamp": time.time(), "event": event, "details": details})

# 🔊 Text-to-Speech
def speak_text(text):
    tts = gTTS(text)
    mp3_fp = BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    audio_bytes = mp3_fp.read()
    audio_base64 = base64.b64encode(audio_bytes).decode()
    audio_html = f"""
    <h5>🔊 Listen to the Answer:</h5>
    <audio controls>
        <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
    </audio>
    """
    return audio_html

# ✅ Ask a Question with Fuzzy Match
def ask_question(query, subject):
    file_path = "questions.json"
    if not os.path.exists(file_path):
        return "📂 Questions file not found. Please upload the questions.json file."

    with open(file_path, "r") as file:
        data = json.load(file)

    subject_questions = data.get(subject, [])
    questions_list = [item["question"] for item in subject_questions]

    match = get_close_matches(query.lower(), [q.lower() for q in questions_list], n=1, cutoff=0.4)

    if match:
        matched_question = match[0]
        for item in subject_questions:
            if item["question"].lower() == matched_question:
                return item["answer"]
    return "🤔 I couldn't find an exact answer, but try rephrasing or asking about a specific topic!"

# Define a basic concept hierarchy (can be expanded)
concept_hierarchy = {
    "Physics": {
        "foundational": ["Kinematics", "Laws of Motion", "Work and Energy"],
        "intermediate": ["Gravitation", "Optics"],
        "advanced": ["Electromagnetism", "Quantum Mechanics"],
    },
    "Biology": {
        "foundational": ["Cell Structure", "Basic Biochemistry"],
        "intermediate": ["Genetics", "Photosynthesis", "Respiration"],
        "advanced": ["Evolution", "Ecology"],
    },
    "Mathematics": {
        "foundational": ["Basic Algebra", "Basic Geometry"],
        "intermediate": ["Linear Equations", "Trigonometry", "Calculus Basics"],
        "advanced": ["Differential Equations", "Linear Algebra"],
    },
    "Chemistry": {
        "foundational": ["Atomic Structure", "Periodic Table", "Chemical Bonding"],
        "intermediate": ["Chemical Reactions", "Stoichiometry", "Acids and Bases"],
        "advanced": ["Organic Chemistry", "Thermodynamics"],
    },
}

# Example mapping of concepts to resources (Extend this!)
concept_resources = {
    "Kinematics": {
        "visual": ["Kinematics Diagrams", "Motion Graphs"],
        "auditory": ["Kinematics Audio Lecture"],
        "interactive": ["Kinematics Simulation"],
    },
    "Laws of Motion": {
        "visual": ["Newton's Laws Diagrams"],
        "auditory": ["Newton's Laws Explanation"],
        "interactive": ["Force and Motion Lab"],
    },
    "Cell Structure": {
        "visual": ["Cell Diagrams", "Microscope Images"],
        "auditory": ["Cell Biology Lecture"],
        "interactive": ["Virtual Cell Tour"],
    },
    "Genetics": {
        "visual": ["Punnett Squares", "DNA Structure"],
        "auditory": ["Genetics Explanation"],
        "interactive": ["DNA Replication Game"],
    },
    "Basic Algebra":{
        "visual":["Algebraic Equations","Graphing"],
        "auditory":["Algebra Basics"],
        "interactive":["Algebra practice"]
    },
    "Basic Geometry":{
        "visual":["Geometric Shapes", "Theorems"],
        "auditory":["Geometry Basics"],
        "interactive":["Geometry Tool"]
    },
    "Atomic Structure":{
        "visual":["Atomic Models","Electron Configuration"],
        "auditory":["Atomic Structure explanation"],
        "interactive":["Build an Atom"]
    },
    "Periodic Table":{
        "visual":["Periodic Table","Element Trends"],
        "auditory":["Periodic Table explanation"],
        "interactive":["Periodic Table Game"]
    }

    # Add resources for other concepts
}

def generate_quiz(subject):
    quiz_file = f"quiz_{subject.lower()}.json"
    if os.path.exists(quiz_file):
        with open(quiz_file, "r") as file:
            quiz_data = json.load(file)
        return quiz_data.get("questions", [])
    return []

def get_learning_path(subject):
    topics = {
        "Physics": ["Kinematics", "Laws of Motion", "Gravitation", "Optics"],
        "Biology": ["Cell Structure", "Genetics", "Photosynthesis", "Human Anatomy"],
        "Mathematics": ["Algebra", "Trigonometry", "Calculus", "Geometry"],
        "Chemistry": ["Periodic Table", "Chemical Reactions", "Acids & Bases", "Atomic Structure"],
    }
    return random.sample(topics.get(subject, []), 3)

# 🚀 Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["💬 Ask a Question", "📌 Learning Path", "🧪 Take Quiz", "🏆 Leaderboard", "🎮 XP & Achievements"])

# 💬 Tab 1: Ask a Question
with tab1:
    st.subheader(f"👋 Hey {name or 'Learner'}, ask a question about {subject}!")
    question = st.text_input("🧠 Type your question below:")
    if question:
        with st.spinner("Searching for an answer..."):
            answer = ask_question(question, subject)
            st.success(answer)
            st.markdown(speak_text(answer), unsafe_allow_html=True)

# 📌 Tab 2: Learning Path
with tab2:
    st.subheader("📌 Your Personalized Learning Path")
    if name:
        if st.button("Generate My Learning Path"):
            with st.spinner("Generating personalized path..."):
                personalized_path = generate_personalized_path(
                    name,
                    subject,
                    st.session_state.user_data.get(name, {}).get(subject, {}).get("quiz_history", []),
                    st.session_state.inferred_learning_style.get(name, "Mixed"),
                    concept_hierarchy,
                    concept_resources
                )
                if personalized_path:
                    st.info("Based on your progress, here's a recommended learning path:")
                    st.session_state.recommended_path = personalized_path

                    for i, path_item in enumerate(st.session_state.recommended_path, 1):
                        st.markdown(f"**{i}. {path_item['concept']}**")
                        st.markdown(f"   -   Type: {path_item['type']}")
                        if path_item['resources']:
                            st.markdown("   -   Resources:")
                            for resource in path_item['resources']:
                                # Basic example: Assuming resource names imply their type
                                resource_type = "unknown"
                                if "Diagram" in resource or "Graph" in resource or "Image" in resource:
                                    resource_type = "visual"
                                elif "Lecture" in resource or "Explanation" in resource or "Audio" in resource:
                                    resource_type = "auditory"
                                elif "Simulation" in resource or "Lab" in resource or "Game" in resource or "Tool" in resource or "Practice" in resource:
                                    resource_type = "interactive"
                                elif "Text" in resource or "Article" in resource or "Book" in resource:
                                    resource_type = "reading_writing"

                                if st.button(f"View {resource}", key=f"view_{path_item['concept']}_{i}_{resource}"):
                                    record_interaction(name, "resource_viewed", {"concept": path_item['concept'], "resource": resource, "type": resource_type})
                                    st.info(f"You are now viewing: {resource} ({resource_type})") # Replace with actual resource display

                        col1, col2 = st.columns(2)
                        with col1:
                            feedback = st.radio(f"Was this recommendation helpful?", ["Yes", "No"], key=f"path_feedback_{i}")
                            if feedback:
                                record_interaction(name, "path_feedback", {"concept": path_item['concept'], "feedback": feedback})
                                if feedback == "No":
                                    if st.button(f"Suggest Alternative for {path_item['concept']}", key=f"alt_{i}"):
                                        with st.spinner(f"Finding alternatives for {path_item['concept']}..."):
                                            alternative = get_alternative_concept(
                                                subject, path_item['concept'], st.session_state.user_data.get(name, {}).get(subject, {}).get("quiz_history", []), concept_hierarchy
                                            )
                                            if alternative:
                                                st.info(f"Alternative suggestion: {alternative}")
                                            else:
                                                st.warning("No immediate alternative found.")
                        with col2:
                            difficulty = st.selectbox("Difficulty Level", ["Too Easy", "Just Right", "Too Hard"], key=f"difficulty_{i}")
                            if difficulty and difficulty != "Just Right":
                                record_interaction(name, "path_difficulty", {"concept": path_item['concept'], "difficulty": difficulty})

                else:
                    st.warning("No learning history available yet. A general path will be shown.")
                    for i, topic in enumerate(get_learning_path(subject), 1):
                        st.markdown(f"**{i}. {topic}**")
    else:
        st.warning("Please enter your name in the sidebar to personalize your learning path.")
# 🧪 Tab 3: Quiz
with tab3:
    st.subheader(f"🧪 Test Your Knowledge in {subject}")
    questions = generate_quiz(subject)

    if questions:
        if not st.session_state.submitted:
            for i, q in enumerate(questions):
                st.markdown(f"**Q{i+1}. {q['question']}**")
                st.session_state.user_answers[i] = st.radio(f"Choose your answer:", q["options"], key=f"q{i}")
            if st.button("Submit Quiz"):
                st.session_state.submitted = True
                correct_answers = {}
                score = 0
                current_questions = generate_quiz(subject) # Ensure we have the current questions
                if current_questions:
                    for i, q in enumerate(current_questions):
                        if i in st.session_state.user_answers and st.session_state.user_answers[i] == q["answer"]:
                            score += 1
                            correct_answers[i] = True
                        else:
                            correct_answers[i] = False
                    percentage = round(score / len(current_questions) * 100)
                    st.success(f"🎯 Your Score: {score}/{len(current_questions)} ({percentage}%)")
                    st.info(f"Your overall performance in {subject}.")
                    record_quiz_data(name, subject, current_questions, st.session_state.user_answers, score, correct_answers)
                    record_interaction(name, "quiz_submitted", {"subject": subject, "score": score})

                    st.subheader("Detailed Results:")
                    for i, q in enumerate(current_questions):
                        st.markdown(f"**Q{i+1}. {q['question']}**")
                        if correct_answers[i]:
                            st.markdown(f"<span style='color:green'>✅ Correct!</span>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<span style='color:red'>❌ Incorrect.</span> Your answer: **{st.session_state.user_answers.get(i, 'Not answered')}**. Correct answer: **{q['answer']}**", unsafe_allow_html=True)
                        if "explanation" in q:
                            with st.expander("Explanation"):
                                st.write(q["explanation"])
                                st.markdown(speak_text(q["explanation"]), unsafe_allow_html=True)
                else:
                    st.error("⚠️ Could not retrieve current quiz questions.")
        else:
            if st.button("Retake Quiz"):
                st.session_state.submitted = False
                st.session_state.user_answers = {}
    else:
        st.error("⚠️ Quiz file not found or empty.")
# 🏆 Tab 4: Leaderboard
with tab4:
    st.subheader("🏆 Top Learners (Coming Soon)")
    st.info("Leaderboard and scores will be available once user logins are implemented.")

# 🎮 Tab 5: XP & Achievements + Data Download
with tab5:
    st.subheader("🎮 Your XP, Achievements & Data")
    
    st.markdown("📥 Download your progress data below:")

    if name:
        export_data = {
            "name": name,
            "subject": subject,
            "learning_style": st.session_state.learning_style.get(name, {}),
            "quiz_data": st.session_state.quiz_data.get(name, {}).get(subject, {}),
            "user_data": st.session_state.user_data.get(name, {}).get(subject, {}),
            "interaction_data": st.session_state.interaction_data.get(name, [])
        }

        json_data = json.dumps(export_data, indent=4)
        b64 = base64.b64encode(json_data.encode()).decode()
        href = f'<a href="data:file/json;base64,{b64}" download="{name}_edu_data.json">📥 Click here to download your data</a>'
        st.markdown(href, unsafe_allow_html=True)
    else:
        st.warning("Please enter your name in the sidebar to enable data download.")

# --- AI Analysis ---
st.sidebar.subheader("🧠 AI Learning Analysis")
if name and subject:
    user_quiz_history = st.session_state.quiz_data.get(name, {}).get(subject, {}).get("quiz_history", [])
    user_interaction_data = st.session_state.interaction_data.get(name, [])
    user_learning_style = st.session_state.learning_style.get(name)

    if user_interaction_data and user_learning_style:
        inferred_style = analyze_learning_style(name, user_learning_style, user_interaction_data)
        st.session_state.inferred_learning_style[name] = inferred_style
        st.sidebar.markdown(f"**Inferred Learning Style (AI):** {inferred_style}")

    if user_quiz_history:
        strengths, weaknesses = analyze_strengths_weaknesses(name, subject, user_quiz_history)
        st.session_state.strengths[name] = strengths
        st.session_state