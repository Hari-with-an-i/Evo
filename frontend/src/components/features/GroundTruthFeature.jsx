import React, { useState } from 'react';
import { compareNarratives, queryGroundTruth } from '../../services/api';

function GroundTruthFeature() {
    // --- STATE DEFINITIONS ---
    const [mode, setMode] = useState('compare'); // 'compare' or 'query'

    // States for Compare Mode
    const [intendedTruth, setIntendedTruth] = useState('');
    const [mediaText, setMediaText] = useState('');
    
    // States for Query Mode
    const [userQuery, setUserQuery] = useState('');

    // General states for UI feedback and results
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [results, setResults] = useState(null);
    
    // --- HANDLER FUNCTIONS ---

    const handleCompare = async (e) => {
        e.preventDefault();
        if (!intendedTruth || !mediaText) {
            setError('Please fill out both text areas for comparison.');
            return;
        }
        setIsLoading(true);
        setError('');
        setResults(null);
        try {
            const data = await compareNarratives(intendedTruth, mediaText);
            setResults(data);
        } catch (err) {
            setError('Failed to perform comparison. Please check the backend.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleQuery = async (e) => {
        e.preventDefault();
        if (!userQuery) {
            setError('Please enter a question to query the knowledge base.');
            return;
        }
        setIsLoading(true);
        setError('');
        setResults(null);
        try {
            const data = await queryGroundTruth(userQuery);
            setResults(data);
        } catch (err) {
            setError('Failed to query the knowledge base.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    // --- RENDER LOGIC ---

    return (
        <div className="feature-card">
            <h2>Ground Truth Analysis</h2>
            
            <div className="sub-tabs">
                <button onClick={() => { setResults(null); setError(''); setMode('compare'); }} className={mode === 'compare' ? 'active' : ''}>Direct Comparison</button>
                <button onClick={() => { setResults(null); setError(''); setMode('query'); }} className={mode === 'query' ? 'active' : ''}>Knowledge Base Query</button>
            </div>

            {/* --- UI for DIRECT COMPARISON Mode --- */}
            {mode === 'compare' && (
                <div className="feature-content">
                    <p>Compare your intended message with a specific article's text to find the narrative gap.</p>
                    <form onSubmit={handleCompare}>
                        <textarea value={intendedTruth} onChange={(e) => setIntendedTruth(e.target.value)} placeholder="Paste your intended message or 'ground truth' here..." />
                        <textarea value={mediaText} onChange={(e) => setMediaText(e.target.value)} placeholder="Paste the text from a news article to analyze..." />
                        <button type="submit" disabled={isLoading}>{isLoading ? 'Analyzing...' : 'Analyze Gap'}</button>
                    </form>
                    {results && (
                        <div className="results-container text-analysis">
                            <h4>Narrative Gap Analysis:</h4>
                            <p>{results.narrative_gap}</p>
                            <h4>Key Misinterpreted Points:</h4>
                            <ul>{results.misinterpreted_points?.map((point, i) => <li key={i}>{point}</li>)}</ul>
                            <h4>Counter Speech Talking Points:</h4>
                            <ul>{results.counter_speech_points?.map((point, i) => <li key={i}>{point}</li>)}</ul>
                        </div>
                    )}
                </div>
            )}

            {/* --- UI for KNOWLEDGE BASE QUERY Mode --- */}
            {mode === 'query' && (
                <div className="feature-content">
                    <p>Ask a question to find the truth from our knowledge base.</p>
                    <form onSubmit={handleQuery}>
                        <input type="text" value={userQuery} onChange={(e) => setUserQuery(e.target.value)} placeholder="e.g., What is the relationship between Trump and outsourcing?"/>
                        <button type="submit" disabled={isLoading}>{isLoading ? 'Finding Truth...' : 'Find Truth'}</button>
                    </form>
                    {results && (
                        <div className="results-container text-analysis">
                            <h4>Answer:</h4>
                            <p>{results.answer}</p>
                            {results.evidence && results.evidence.length > 0 && (
                                <>
                                    <h5>Evidence from Knowledge Graph:</h5>
                                    <ul>{results.evidence.map((fact, i) => <li key={i}><code>{fact}</code></li>)}</ul>
                                </>
                            )}
                        </div>
                    )}
                </div>
            )}

            {/* --- General UI Feedback --- */}
            {error && <p className="error-message">{error}</p>}
            {isLoading && <div className="loader"></div>}
        </div>
    );
}

export default GroundTruthFeature;