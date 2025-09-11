import spacy
from neo4j import GraphDatabase
from config import GROQ_API_KEY, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD # Centralize Neo4j config
from groq import Groq
import json

# --- Initialize Models and Clients ---
nlp = spacy.load("en_core_web_lg")
groq_client = Groq(api_key=GROQ_API_KEY)

# --- Relation Extraction Tool ---
def tool_extract_relations(text: str) -> list:
    """Uses an LLM to extract (Subject, Predicate, Object) triplets."""
    prompt = f"""
    From the following text, extract all key factual relationships as a list of JSON objects.
    Each object should have three keys: "subject", "predicate", and "object".
    Focus on clear, simple relationships.

    TEXT:
    "{text[:4000]}"

    EXAMPLE OUTPUT:
    [
      {{"subject": "Laura Loomer", "predicate": "is an aide to", "object": "President Trump"}},
      {{"subject": "President Trump", "predicate": "considers blocking", "object": "IT outsourcing"}}
    ]
    """
    try:
        completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
            response_format={"type": "json_object"}
        )
        result = json.loads(completion.choices[0].message.content)
        # The result might be a dict with a key like "triplets", so we find the list
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, list):
                    return value
        return result if isinstance(result, list) else []
    except Exception:
        return []

# --- Knowledge Graph Builder Class (Upgraded) ---
class KnowledgeGraphBuilder:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print("✅ Connected to Neo4j database.")

    def close(self):
        self.driver.close()

    def process_article(self, raw_text: str, article_id: str):
        """Processes raw text to extract and store relationships in the graph."""
        print(f"\nProcessing article for KG: {article_id}")
        relations = tool_extract_relations(raw_text)
        if not relations:
            print(f"  > No relations extracted for {article_id}")
            return
        
        with self.driver.session(database="neo4j") as session:
            session.execute_write(self._create_relations, article_id, relations)
            print(f"  > Graph updated with {len(relations)} relations for {article_id}")

    @staticmethod
    def _create_relations(tx, article_id, relations):
        for rel in relations:
            # Create nodes and the relationship between them
            tx.run("""
                MERGE (s {name: $subject})
                MERGE (o {name: $object})
                MERGE (s)-[r:RELATIONSHIP {type: $predicate, source: $source}]->(o)
                RETURN type(r)
            """, subject=rel.get('subject'), predicate=rel.get('predicate'), object=rel.get('object'), source=article_id)

# Initialize a global instance for the app to use
kg_builder = KnowledgeGraphBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)