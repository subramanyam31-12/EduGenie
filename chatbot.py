# chatbot.py
def get_ai_response(subject, topic, query):
    query = query.lower()

    rules = {
        "ohm": "Ohm's Law states that V = IR. Voltage equals current times resistance.",
        "photosynthesis": "Photosynthesis is the process by which green plants make food using sunlight, CO2, and water.",
        "newton": "Newton's laws describe motion. The first law is inertia, the second is F=ma, and the third is action-reaction.",
        "cell": "A cell is the basic structural and functional unit of life."
    }

    for keyword, answer in rules.items():
        if keyword in query or keyword in topic.lower():
            return f"📘 AI Tutor: {answer}"
    
    return "🤖 I'm still learning! Try asking about basic concepts in your chosen topic."
