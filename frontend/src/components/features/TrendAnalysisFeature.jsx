import React, { useState } from 'react';
import { analyzePerceptionTrend } from '../../services/api';
import SentimentChart from '../SentimentChart'; // Assuming SentimentChart is in the components folder

function TrendAnalysisFeature() {
    const [keywords, setKeywords] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [error, setError] = useState('');

    const handleSubmit = async (event) => {
        event.preventDefault();
        if (!keywords) {
            setError('Please enter a topic to analyze.');
            return;
        }
        setIsLoading(true);
        setError('');
        setResults(null);
        try {
            const data = await analyzePerceptionTrend(keywords);
            console.log("DATA RECEIVED FROM API:", data); 
            setResults(data);
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

            {/* --- THIS IS THE CORRECTED PART --- */}
            {/* First, check if results exist before trying to access its properties */}
            {results && (
                <div className="results-container">
                    <h3>Analysis Report for: {results.keywords}</h3>
                    
                    <div className="chart-container">
                        <SentimentChart analyticsData={results.time_series_analytics} />
                    </div>

                    <div className="text-analysis">
                        <h4>Executive Summary</h4>
                        {/* --- FIX IS HERE: Access the .summary property --- */}
                        <p>{results.report?.executive_summary?.summary || "No executive summary was generated."}</p>
                        
                        <h4>Analysis of Trend</h4>
                        {/* --- FIX IS HERE: Access the .summary or equivalent property --- */}
                        {/* Adjust '.summary' if the key is different, but the principle is the same */}
                        <p>{results.report?.analysis_of_trend?.summary || "No trend analysis was generated."}</p>

                        <h4>Recommended Strategies</h4>
                        <div className="strategies">
                            {results.report?.mitigation_strategies?.map((strategy, index) => (
                                <div className="strategy-item" key={index}>
                                    <strong>{strategy.name}:</strong>
                                    <p>{strategy.description}</p>
                                    <em>Justification: {strategy.justification}</em>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
            {/* --- END OF CORRECTION --- */}
        </div>
    );
}

export default TrendAnalysisFeature;