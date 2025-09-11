import React, { useState } from 'react';
// You'll need to create a `compareNarratives` function in api.js

function GroundTruthFeature() {
    const [intendedTruth, setIntendedTruth] = useState('');
    const [mediaText, setMediaText] = useState(''); // User can paste article text here
    // ... states for loading, error, and results

    const handleQuery = async (e) => {
    e.preventDefault();
    // ... set loading states ...
    try {
        // You'll need a new `queryGroundTruth` function in api.js
        const res = await queryGroundTruth(userQuery);
        setResults(res); // The response will have 'answer' and 'evidence' keys
    } catch (err) {
        setError('Failed to query the knowledge base.');
    } finally {
        setIsLoading(false);
    }
};

// In the JSX for the 'query' mode:
{mode === 'query' && (
    <div>
        <p>Ask a question to find the truth from our knowledge base.</p>
        <form onSubmit={handleQuery}>
            <input type="text" value={userQuery} onChange={(e) => setUserQuery(e.target.value)} placeholder="e.g., What is the relationship between Trump and outsourcing?"/>
            <button type="submit">Find Truth</button>
        </form>

        {results && (
            <div className="results-container">
                <h4>Answer:</h4>
                <p>{results.answer}</p>
                <h5>Evidence from Knowledge Graph:</h5>
                <ul>
                    {results.evidence.map((fact, i) => <li key={i}>{fact}</li>)}
                </ul>
            </div>
        )}
    </div>
)}

}

export default GroundTruthFeature;