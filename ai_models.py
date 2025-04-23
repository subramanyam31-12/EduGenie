# ai_models.py
from collections import defaultdict
from sklearn.cluster import KMeans  # Example clustering algorithm
from sklearn.preprocessing import StandardScaler  # For scaling data
import numpy as np
import random
import streamlit as st  # Import for accessing session state (if needed for quick adaptation)

def analyze_learning_style(name, self_reported_style, interaction_data):
    """
    Analyzes a student's learning style based on self-reported preferences and interaction data.
    """
    if not interaction_data:
        return "Mixed"

    features = defaultdict(int)
    for event in interaction_data:
        if event["event"] == "question_displayed":
            features["questions_displayed"] += 1
        elif event["event"] == "question_answered":
            features["questions_answered"] += 1
        elif event["event"] == "text_to_speech_used":
            features["tts_usage"] += 1
        elif event["event"] == "resource_viewed" and event["details"].get("type") == "visual":
            features["visual_resource_views"] += 1
        elif event["event"] == "resource_viewed" and event["details"].get("type") == "auditory":
            features["auditory_resource_views"] += 1
        elif event["event"] == "resource_viewed" and event["details"].get("type") == "interactive":
            features["interactive_resource_views"] += 1

    inferred_style = "Mixed"
    if features["auditory_resource_views"] > features.get("visual_resource_views", 0) and features["auditory_resource_views"] > features.get("interactive_resource_views", 0) and features["tts_usage"] > 2:
        inferred_style = "Auditory-Inclined"
    elif features.get("visual_resource_views", 0) > features["auditory_resource_views"] and features.get("visual_resource_views", 0) > features.get("interactive_resource_views", 0) and self_reported_style.get("preferred_visual", 3) > 3:
        inferred_style = "Visual-Inclined"
    elif features.get("interactive_resource_views", 0) > features["auditory_resource_views"] and features.get("interactive_resource_views", 0) > features.get("visual_resource_views", 0) and self_reported_style.get("preferred_kinesthetic", 3) > 3:
        inferred_style = "Kinesthetic-Inclined"
    elif self_reported_style:
        preferences = {
            "visual": self_reported_style.get("preferred_visual", 3),
            "auditory": self_reported_style.get("preferred_auditory", 3),
            "read_write": self_reported_style.get("preferred_reading_writing", 3),
            "kinesthetic": self_reported_style.get("preferred_kinesthetic", 3),
        }
        sorted_preferences = sorted(preferences.items(), key=lambda item: item[1], reverse=True)
        top_preference = sorted_preferences[0][0].capitalize()
        if sorted_preferences[0][1] > 4:
            inferred_style = f"Primarily {top_preference.replace('Read_write', 'Reading/Writing').replace('Kinesthetic', 'Hands-on')}"

    return inferred_style

def analyze_strengths_weaknesses(name, subject, quiz_data):
    """
    Analyzes a student's strengths and weaknesses based on their quiz history.
    """
    if not quiz_data:
        return [], []

    concept_performance = defaultdict(lambda: {"correct": 0, "incorrect": 0, "total": 0})

    for quiz in quiz_data:
        if "concepts_tested" not in quiz or "correct_answers" not in quiz:
            continue
        for i, correct in quiz['correct_answers'].items():
            if i < len(quiz['concepts_tested']):
                concept = quiz['concepts_tested'][i]
                concept_performance[concept]["total"] += 1
                if correct:
                    concept_performance[concept]["correct"] += 1
                else:
                    concept_performance[concept]["incorrect"] += 1

    weak_concepts = sorted(
        [concept for concept, performance in concept_performance.items()
         if performance["total"] > 0 and performance["incorrect"] / performance["total"] > 0.5],
        key=lambda c: concept_performance[c]["incorrect"] / concept_performance[c]["total"],
        reverse=True
    )

    strong_concepts = sorted(
        [concept for concept, performance in concept_performance.items()
         if performance["total"] > 0 and performance["correct"] / performance["total"] >= 0.8],
        key=lambda c: concept_performance[c]["correct"] / concept_performance[c]["total"],
        reverse=True
    )

    return [c for c in strong_concepts], [c for c in weak_concepts]

def get_resources_for_concept(concept, learning_style, concept_resources):
    """
    Gets learning resources for a concept, considering the student's learning style.
    """
    resources = concept_resources.get(concept, {})
    relevant_resources = []

    if "Visual" in learning_style:
        relevant_resources.extend(resources.get("visual", []))
    if "Auditory" in learning_style:
        relevant_resources.extend(resources.get("auditory", []))
    if "Kinesthetic" in learning_style or "Hands-on" in learning_style:
        relevant_resources.extend(resources.get("interactive", []))
    if "Read" in learning_style or "Writing" in learning_style or "Reading/Writing" in learning_style:
        relevant_resources.extend(resources.get("reading_writing", []))

    if not relevant_resources:
        all_resources = []
        for res_type in resources:
            all_resources.extend(resources[res_type])
        return all_resources

    return random.sample(relevant_resources, min(3, len(relevant_resources)))

def get_next_concepts(subject, strengths, weaknesses, concept_hierarchy):
    """
    Suggests the next concepts to learn based on strengths, weaknesses, and the concept hierarchy.
    """
    suggested_concepts = set()

    for strong_concept in strengths:
        for level_name, level_concepts in concept_hierarchy.get(subject, {}).items():
            if strong_concept in level_concepts:
                levels_list = list(concept_hierarchy.get(subject, {}).keys())
                current_level_index = levels_list.index(level_name)
                if current_level_index < len(levels_list) - 1:
                    next_level_name = levels_list[current_level_index + 1]
                    next_level_concepts = concept_hierarchy.get(subject, {}).get(next_level_name, [])
                    potential_next = [c for c in next_level_concepts if c not in strengths and c not in weaknesses and c not in suggested_concepts]
                    if potential_next:
                        suggested_concepts.add(random.choice(potential_next))
                        if len(suggested_concepts) >= 1:
                            return list(suggested_concepts)

    if not suggested_concepts and weaknesses:
        foundational_level = concept_hierarchy.get(subject, {}).get("foundational", [])
        related_foundational = [c for c in foundational_level if c not in strengths and c not in weaknesses and c not in suggested_concepts]
        if related_foundational:
            suggested_concepts.add(random.choice(related_foundational))
            if len(suggested_concepts) >= 1:
                return list(suggested_concepts)

    all_concepts = set()
    for levels in concept_hierarchy.get(subject, {}).values():
        all_concepts.update(levels)
    learned_concepts = set()
    for quiz in st.session_state.user_data.get(st.session_state.get("name"), {}).get(subject, {}).get("quiz_history", []):
        learned_concepts.update(quiz.get("concepts_tested", []))
    unseen_concepts = list(all_concepts - learned_concepts - suggested_concepts)
    if unseen_concepts:
        suggested_concepts.add(random.choice(unseen_concepts))

    return list(suggested_concepts)[:1]

def get_alternative_concept(subject, rejected_concept, quiz_history, concept_hierarchy):
    """
    Suggests an alternative learning concept based on a rejected recommendation.
    """
    name = st.session_state.get("name") # Get current user's name
    strengths, weaknesses = analyze_strengths_weaknesses(name, subject, quiz_history)

    for level_name, level_concepts in concept_hierarchy.get(subject, {}).items():
        if rejected_concept in level_concepts:
            alternatives = [
                c for c in level_concepts if c != rejected_concept and c not in strengths and c not in weaknesses
            ]
            if alternatives:
                return random.choice(alternatives)

    if weaknesses:
        foundational_level = concept_hierarchy.get(subject, {}).get("foundational", [])
        related_foundational = [c for c in foundational_level if c not in strengths and c not in weaknesses and c != rejected_concept]
        if related_foundational:
            return random.choice(related_foundational)

    all_concepts = set()
    for levels in concept_hierarchy.get(subject, {}).values():
        all_concepts.update(levels)
    learned_concepts = set()
    for quiz in quiz_history:
        learned_concepts.update(quiz.get("concepts_tested", []))
    unseen_concepts = list(all_concepts - learned_concepts - {rejected_concept})
    if unseen_concepts:
        return random.choice(unseen_concepts)

    return None

def generate_personalized_path(name, subject, quiz_history, learning_style, concept_hierarchy, concept_resources):
    """
    Generates a personalized learning path for a student.
    """
    if not quiz_history:
        default_path = []
        foundational_concepts = concept_hierarchy.get(subject, {}).get("foundational", [])
        if foundational_concepts:
            for concept in foundational_concepts[:3]:
                default_path.append({
                    "concept": concept,
                    "type": "foundational",
                    "resources": get_resources_for_concept(concept, learning_style, concept_resources),
                })
        return default_path

    strengths, weaknesses = analyze_strengths_weaknesses(name, subject, quiz_history)
    recommended_path = []
    seen_concepts = set()

    # 1. Prioritize Weak Concepts
    if weaknesses:  # Check if weaknesses is not empty
        for weak_concept in weaknesses[:2]:
            if weak_concept not in seen_concepts:
                recommended_path.append({
                    "concept": weak_concept,
                    "type": "weakness",
                    "resources": get_resources_for_concept(weak_concept, learning_style, concept_resources),
                })
                seen_concepts.add(weak_concept)

    # 2. Introduce New Concepts
    next_concepts = get_next_concepts(subject, strengths, weaknesses, concept_hierarchy)
    for next_concept in next_concepts:
        if next_concept not in seen_concepts:
            recommended_path.append({
                "concept": next_concept,
                "type": "new",
                "resources": get_resources_for_concept(next_concept, learning_style, concept_resources),
            })
            seen_concepts.add(next_concept)
            if len(recommended_path) >= 3:
                break

    # 3. Reinforce Strong Concepts
    if len(recommended_path) < 3:
        for strong_concept in strengths[:(3 - len(recommended_path))]:
            if strong_concept not in seen_concepts:
                recommended_path.append({
                    "concept": strong_concept,
                    "type": "strength",
                    "resources": get_resources_for_concept(strong_concept, learning_style, concept_resources),
                })
                seen_concepts.add(strong_concept)

    return recommended_path[:3]