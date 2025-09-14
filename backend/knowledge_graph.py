import spacy
from collections import Counter
from neo4j import GraphDatabase

# --- Your spaCy function (as you provided) ---
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
    """
    if not nlp:
        return {"error": "spaCy model is not loaded."}
    doc = nlp(raw_text)
    people = sorted(list(set([ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"])))
    locations = sorted(list(set([ent.text.strip() for ent in doc.ents if ent.label_ in ["GPE", "LOC"]])))
    organizations = sorted(list(set([ent.text.strip() for ent in doc.ents if ent.label_ == "ORG"])))
    topics_nouns = [chunk.text.strip() for chunk in doc.noun_chunks if chunk.root.pos_ == "NOUN" and len(chunk.text.strip()) > 3]
    topic_counts = Counter(topics_nouns)
    top_topics = [topic for topic, count in topic_counts.most_common(10)]
    return {
        "people": people,
        "locations": locations,
        "organizations": organizations,
        "topics": sorted(list(set(top_topics))),
    }

# --- The Knowledge Graph Builder ---

class KnowledgeGraphBuilder:
    def __init__(self, uri, user, password):
        # Connect to the Neo4j database
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print("✅ Connected to Neo4j database.")

    def close(self):
        self.driver.close()

    def process_article(self, raw_text: str, article_id: str):
        """
        Processes raw text, runs spaCy analysis, and populates the knowledge graph.
        'article_id' can be a URL or a unique title.
        """
        print(f"\nProcessing article: {article_id}")
        
        # 1. Get structured data from your spaCy function
        analysis = tool_spacy_analysis(raw_text)
        if "error" in analysis:
            print(f"Skipping article due to error: {analysis['error']}")
            return

        # 2. Use a database session to run queries
        with self.driver.session(database="neo4j") as session:
            session.execute_write(self._create_graph_from_analysis, article_id, analysis)

    @staticmethod
    def _create_graph_from_analysis(tx, article_id, analysis):
        # Create or find the central Article node
        tx.run("MERGE (a:Article {id: $id})", id=article_id)

        # Process and link each entity type
        for person in analysis.get("people", []):
            tx.run("""
                MATCH (a:Article {id: $article_id})
                MERGE (p:Person {name: $name})
                MERGE (p)-[:MENTIONED_IN]->(a)
            """, article_id=article_id, name=person)

        for org in analysis.get("organizations", []):
            tx.run("""
                MATCH (a:Article {id: $article_id})
                MERGE (o:Organization {name: $name})
                MERGE (o)-[:MENTIONED_IN]->(a)
            """, article_id=article_id, name=org)

        for loc in analysis.get("locations", []):
            tx.run("""
                MATCH (a:Article {id: $article_id})
                MERGE (l:Location {name: $name})
                MERGE (l)-[:MENTIONED_IN]->(a)
            """, article_id=article_id, name=loc)
        
        for topic in analysis.get("topics", []):
            tx.run("""
                MATCH (a:Article {id: $article_id})
                MERGE (t:Topic {name: $name})
                MERGE (a)-[:DISCUSSES]->(t)
            """, article_id=article_id, name=topic)
        
        print(f"  > Graph updated for article: {article_id}")

# --- Example Usage ---
if __name__ == "__main__":
    # Get your connection details from the Neo4j Desktop app
    NEO4J_URI = "neo4j://127.0.0.1:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "Evo12345" # <-- IMPORTANT: Change this!

    # Sample article text
    sample_text = """
    Sixty years ago, on this day, the town of Khem Karan in Punjab was at the heart of a war. The year was 1965, and Pakistan had thrust yet another conflict upon India with Operation Gibraltar—its second failed attempt to seize Kashmir through infiltration, after the first in 1947. Days after the commencement of Operation Gibraltar, Pakistan was advancing with the aim of capturing Amritsar.

The offensive began across the western frontier, and Punjab also became a battleground. The fields of Asal Uttar in Khem Karan saw a tank battle—the biggest the world had seen since the Battle of Kursk on the Eastern Front between Nazi Germany and the Soviet Union in World War II.

The battle remains one of India's most decisive victories against Pakistan.

Pakistan, armed by the US, had placed great faith in its American M47 and M48 Patton tanks, among the most advanced in the world at the time. But hundreds of these tanks were reduced to wrecks in the fields of Khem Karan.

Despite Pakistan's advantage in armour, firepower, and mobility compared to India's ageing Sherman tanks and limited Centurion tanks, the outcome demonstrated that it is the soldier behind the gun who matters more than the weapon itself. Indian troops displayed remarkable battle skills, strategy, and bravery to turn the tide.

After three days of fierce fighting, the battlefield was littered with destroyed Pakistani tanks.

What turned the tide at Asal Uttar was not just the bravery of Indian soldiers but the way Indian commanders used the land to their advantage.

The clash also produced one of the most remarkable acts of individual bravery, revered not only in Indian military history but also globally. In the Battle of Asal Uttar (meaning the real reply), Abdul Hamid etched his name as one of India's bravest sons. In the battle, Hamid stood atop his jeep, manoeuvring through the sugarcane fields of Punjab with a recoilless (RCL) gun, and single-handedly took down at least half a dozen American-made Pakistani Patton tanks.

Military historians say that the battle was the moment when Pakistan's war plans began to unravel.

Pakistan's prized 1st Armoured Division, meant to spearhead a drive into Indian Punjab, was crippled beyond recovery.
    """

    # Initialize the builder
    kg_builder = KnowledgeGraphBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    # Process the article
    kg_builder.process_article(
        raw_text=sample_text, 
        article_id="Test"
    )

    # Close the connection
    kg_builder.close()