import React, { useState } from 'react';
import { searchArticles } from '../../services/api';

function SearchFeature() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSearch = async (e) => {
        e.preventDefault();
        if (!query) {
            setError('Please enter a topic to search.');
            return;
        }
        setIsLoading(true);
        setError('');
        setResults([]);
        try {
            // Assumes you have a 'searchArticles' function in your api.js
            const res = await searchArticles(query);
            setResults(res.articles || []);
        } catch (err) {
            setError('Failed to fetch articles. Please check the backend connection.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="feature-card">
            <h2>Article Search</h2>
            <p>Find credible articles on any topic.</p>
            
            {/* --- THIS IS THE FORM THAT WAS MISSING --- */}
            <form onSubmit={handleSearch} className="input-form">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Enter a topic..."
                />
                <button type="submit" disabled={isLoading}>
                    {isLoading ? 'Searching...' : 'Search'}
                </button>
            </form>

            {error && <p className="error-message">{error}</p>}
            {isLoading && <div className="loader"></div>}

            {/* This part displays the results after a successful search */}
            {results.length > 0 && (
                <div className="search-results">
                    <h4>Search Results</h4>
                    {results.map((article, index) => (
                        <div className="result-item" key={index}>
                            <a href={article.url} target="_blank" rel="noopener noreferrer">
                                {article.title}
                            </a>
                            <span>({article.source})</span>
                            <p>{article.snippet}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default SearchFeature;