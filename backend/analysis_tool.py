import spacy
from collections import Counter

# Load the spaCy model once when the module is imported.
# This is efficient as it avoids reloading the large model on every API call.
print("🧠 Loading spaCy model 'en_core_web_lg'...")
try:
    nlp = spacy.load("en_core_web_lg")
    print("✅ spaCy model loaded successfully.")
except OSError:
    print("❌ Model not found. Please run: python -m spacy download en_core_web_lg")
    nlp = None

def tool_spacy_analysis(raw_text: str) -> dict:
    """
    Parses a news article using spaCy to extract entities, topics, 
    and the specific sentences where key entities are found.
    (This function is adapted from your notebook)
    """
    if not nlp:
        return {"error": "spaCy model is not loaded."}
        
    # Process the text with the spaCy pipeline
    doc = nlp(raw_text)

    # --- Extract Named Entities ---
    people = sorted(list(set([ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"])))
    locations = sorted(list(set([ent.text.strip() for ent in doc.ents if ent.label_ in ["GPE", "LOC"]])))
    organizations = sorted(list(set([ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"])))

    # --- Extract Topics/Keywords ---
    topics = [chunk.text.strip() for chunk in doc.noun_chunks if chunk.root.pos_ == "NOUN" and chunk.text.strip() not in people]
    topics.extend(organizations)
    topic_counts = Counter(topics)
    top_topics = [topic for topic, count in topic_counts.most_common(10)]

    # --- Extract Sentences Containing These Entities ---
    relevant_sentences = set()
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "GPE", "LOC", "ORG"]:
            relevant_sentences.add(ent.sent.text.strip().replace('\n', ' '))
    
    # --- Structure the final output ---
    structured_output = {
        "people": people,
        "locations": locations,
        "organizations": organizations,
        "topics": sorted(list(set(top_topics))),
        "relevant_sentences": sorted(list(relevant_sentences))
    }
    
    return structured_output