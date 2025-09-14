
    kg_builder = KnowledgeGraphBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    # Process the article
    kg_builder.process_article(
        raw_text=sample_text, 
        article_id="BBC-Budget-2025-09-11"
    )

    # Close the connection
    kg_builder.close()