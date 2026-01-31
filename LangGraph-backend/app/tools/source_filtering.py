from langchain_core.tools import tool
from .analytics_manager import tool_filter_and_parse, CREDIBLE_SOURCES
from .news_fetcher import fetch_news_from_serpapi

@tool
def source_tool(query: str):
    """
    Use this tool to find information from CREDIBLE sources only.
    It performs a search and then filters/parses the results to ensure they are from trusted domains.
    Returns the parsed content from credible articles.
    """
    print(f"--- SOURCE VERIFICATION: {query} ---")
    try:
        # 1. Fetch
        raw_results = fetch_news_from_serpapi(keywords=query, num_results=10)
        
        # 2. Filter & Parse
        # We need to adapt the input for tool_filter_and_parse which expects 'link' key.
        # news_fetcher returns dicts with 'link' usually.
        
        credible_articles = tool_filter_and_parse(raw_results)
        
        if not credible_articles:
            return "No credible articles found for this query."
            
        # 3. Format for agent
        summary = f"Found {len(credible_articles)} credible articles:\n"
        for a in credible_articles:
            summary += f"Source: {a['source']}\nTitle: {a['title']}\nExcerpt: {a['raw_text'][:200]}...\n\n"
            
        return summary

    except Exception as e:
        return f"Error in source verification: {e}"


    def tool_filter_and_parse(articles_from_api: list) -> list[dict]:
    """
    1. Extracts Metadata
    2. Runs Agentic KG Filter
    3. Parses only the winners
    """
    print(f"🚀 Starting Multi-Agent Retrieval for {len(articles_from_api)} articles...")
    
    # Step 1: Pre-process Metadata
    metadata_map = []
    for art in articles_from_api:
        url = art.get("link") or art.get("url")
        if not url: continue
        
        domain = urllib.parse.urlparse(url).netloc.replace('www.', '')
        
        metadata_map.append({
            "domain": domain,
            "title": art.get("title", ""),
            "url": url,
            "original_data": art
        })
    
    if not metadata_map:
        return []

    # Step 2: Run The Analyst (Dynamic Filtering)
    trusted_domains = run_analyst_filter(metadata_map)
    
    # Step 3: Parse and Download
    cleaned_results = []
    
    news_config = Config()
    news_config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    news_config.request_timeout = 10

    for item in metadata_map:
        domain = item['domain']
        
        if domain in trusted_domains:
            try:
                article = Article(item['url'], config=news_config)
                article.download()
                article.parse()
                
                if len(article.text) > 50: 
                    cleaned_results.append({
                        "source": domain,
                        "url": item['url'],
                        "title": article.title,
                        "text": article.text,
                        "published_date": str(article.publish_date),
                        "kg_verdict": "RELEVANT"
                    })
            except Exception as e:
                continue
        else:
            pass

    print(f"✅ Final Corpus: {len(cleaned_results)} high-quality articles ready.")
    return cleaned_results

def run_analyst_filter(articles_metadata: list) -> set:
    """
    Builds the graph and selects sources based on Topology (Centrality & Specificity).
    """
    # 1. Build Graph
    graph_data = extract_graph_triples(articles_metadata)
    
    # If LLM failed or returned no edges, return ALL domains (Safe Fallback)
    if not graph_data.get('edges'):
        print("⚠️  Graph build failed. Falling back to accepting all sources.")
        return {a['domain'] for a in articles_metadata}

    G = nx.Graph()
    
    # 2. Populate Nodes & Edges
    for edge in graph_data['edges']:
        source = edge.get('source')
        target = edge.get('target')
        if source and target:
            G.add_edge(source, target)

    # 3. Identify the "Center of Gravity" (Main Topic)
    all_domains = {a['domain'] for a in articles_metadata}
    possible_topics = [n for n in G.nodes if n not in all_domains]
    
    if not possible_topics:
        return all_domains 

    # The concept mentioned by the most sources is the "Main Topic"
    main_topic = max(possible_topics, key=lambda n: G.degree(n))
    print(f"🎯 Analyst: Main Topic identified as '{main_topic}'")

    # 4. Selection Logic
    approved_sources = set()
    
    for domain in all_domains:
        if domain not in G.nodes:
            continue
            
        try:
            # METRIC 1: Distance (Relevance)
            distance = nx.shortest_path_length(G, source=domain, target=main_topic)
            
            # METRIC 2: Specificity (Information Density)
            specificity_degree = G.degree(domain)

            # RULE: Keep if directly connected (dist=1) OR 
            # (dist=2 AND it mentions at least 2 other entities)
            if distance <= 1:
                approved_sources.add(domain)
            elif distance <= 2 and specificity_degree >= 2:
                approved_sources.add(domain) 
                
        except nx.NetworkXNoPath:
            continue 

    print(f"⚖️  Analyst: Selected {len(approved_sources)} sources out of {len(articles_metadata)}")
    return approved_sources

def extract_graph_triples(articles_metadata: list) -> dict:
    """
    Passes article titles to LLM to extract a knowledge graph in JSON format.
    """
    if not client:
        return {"edges": []}

    print(f"🗺️  Cartographer: Mapping {len(articles_metadata)} articles...")

    context_text = ""
    for idx, item in enumerate(articles_metadata):
        # limiting to first 100 chars of title to save tokens
        context_text += f"ID:{idx} | Source:{item['domain']} | Headline:{item['title'][:100]}\n"

    system_prompt = """
    You are a Knowledge Graph Extractor. 
    1. Identify the Main Topic (Event, Person, or Technology) common to these headlines.
    2. Identify which Sources cover which sub-concepts (Entities).
    3. Output strictly valid JSON. No markdown. No comments.
    
    Structure:
    {
      "edges": [
         {"source": "domain.com", "target": "SpecificEntity", "relation": "COVERS"},
         {"source": "domain.com", "target": "BroaderTopic", "relation": "COVERS"}
      ]
    }
    """

    user_prompt = f"""
    Analyze these headlines and build the graph edges:
    
    {context_text}
    """

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}, 
            temperature=0.1
        )
        return json.loads(response.choices[0].message.content)
    
    except Exception as e:
        print(f"❌ Cartographer Error (Groq Failed): {e}")
        return {"edges": []}