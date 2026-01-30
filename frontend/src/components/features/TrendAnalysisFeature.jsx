import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { analyzePerceptionTrend } from '../../services/api';

function TrendAnalysisFeature() {
    const [keywords, setKeywords] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!keywords) {
            setError('Please enter a topic to analyze.');
            return;
        }
        setIsLoading(true);
        setError('');
        setResult('');
        try {
            const data = await analyzePerceptionTrend(keywords);
            setResult(data.final_response || "No analysis generated.");
        } catch (err) {
            setError('Failed to fetch analysis. Make sure the backend is running.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="feature-card">
            <h2>Perception Trend Analysis</h2>
            <p>Track narrative evolution, analyze trends, and get strategic advice.</p>
            <form onSubmit={handleSubmit} className="input-form">
                <input
                    type="text"
                    value={keywords}
                    onChange={(e) => setKeywords(e.target.value)}
                    placeholder="Enter a topic (e.g., electric vehicle market)"
                />
                <button type="submit" disabled={isLoading}>
                    {isLoading ? 'Analyzing...' : 'Analyze Trend'}
                </button>
            </form>

            {error && <p className="error-message">{error}</p>}
            {isLoading && <div className="loader"></div>}

            {result && (
                <div className="results-container markdown-content">
                    <h3>Analysis Report for: {keywords}</h3>
                    <ReactMarkdown>{result}</ReactMarkdown>
                </div>
            )}
        </div>
    );
}

export default TrendAnalysisFeature;
