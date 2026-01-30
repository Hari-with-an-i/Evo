import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { searchArticles } from '../../services/api';

function SearchFeature() {
    const [query, setQuery] = useState('');
    const [result, setResult] = useState('');
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
        setResult('');
        try {
            const res = await searchArticles(query);
            // The brain returns { final_response: "..." }
            setResult(res.final_response || "No results found.");
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
            <p>Find credible articles on any topic (Powered by Evo Brain).</p>

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

            {result && (
                <div className="search-results markdown-content">
                    <h4>Search Results</h4>
                    <ReactMarkdown>{result}</ReactMarkdown>
                </div>
            )}
        </div>
    );
}

export default SearchFeature;
