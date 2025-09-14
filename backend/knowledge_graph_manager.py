
from neo4j import GraphDatabase
from config import GROQ_API_KEY, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD # Centralize Neo4j config
from groq import Groq
import json

# --- Initialize Client ---
# We check if the key exists to avoid errors on startup
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# --- Relation Extraction Tool ---
def tool_extract_relations(text: str) -> list:
    """Uses an LLM to extract (Subject, Predicate, Object) triplets."""
    if not groq_client:
        print("⚠ Groq client not initialized. Skipping relation extraction.")
        return []
    
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
        # Find the list within the returned JSON
        if isinstance(result, dict):
            for key, value in result.items():
                if isinstance(value, list):
                    return value
        return result if isinstance(result, list) else []
    except Exception as e:
        print(f"❌ LLM Relation Extraction Error: {e}")
        return []

# --- Knowledge Graph Builder Class (Upgraded & Corrected) ---
class KnowledgeGraphBuilder:
    def __init__(self, uri, user, password): # <-- CORRECTED __init_
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print("✅ Connected to Neo4j database.")

    def close(self):
        self.driver.close()

    def process_article(self, raw_text: str, article_id: str):
        """Processes raw text to extract and store relationships in the graph."""
        print(f"\n[BACKGROUND TASK] Processing article for KG: {article_id}")
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
            subject = rel.get('subject')
            predicate = rel.get('predicate')
            obj = rel.get('object')
            
            if subject and predicate and obj: # Ensure all parts exist
                tx.run("""
                    MERGE (s:Entity {name: $subject})
                    MERGE (o:Entity {name: $object})
                    MERGE (s)-[r:RELATIONSHIP {type: $predicate, source: $source}]->(o)
                """, subject=subject, predicate=predicate, object=obj, source=article_id)

# Initialize a global instance for the app to use
kg_builder = KnowledgeGraphBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)