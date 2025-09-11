// frontend/src/pages/Dashboard.jsx
import React, { useState } from 'react';
import SearchFeature from '../components/features/SearchFeature';
import GroundTruthFeature from '../components/features/GroundTruthFeature';
import TrendAnalysisFeature from '../components/features/TrendAnalysisFeature';

function Dashboard() {
    const [activeTab, setActiveTab] = useState('search');

    const renderFeature = () => {
        switch (activeTab) {
            case 'groundTruth':
                return <GroundTruthFeature />;
            case 'trends':
                return <TrendAnalysisFeature />;
            case 'search':
            default:
                return <SearchFeature />;
        }
    };

    return (
        <div className="dashboard">
            <header className="dashboard-header">
                <h1>Evo | Agentic Analysis Dashboard</h1>
                <nav className="tabs">
                    <button onClick={() => setActiveTab('search')} className={activeTab === 'search' ? 'active' : ''}>Search Engine</button>
                    <button onClick={() => setActiveTab('groundTruth')} className={activeTab === 'groundTruth' ? 'active' : ''}>Ground Truth Analysis</button>
                    <button onClick={() => setActiveTab('trends')} className={activeTab === 'trends' ? 'active' : ''}>Perception Trends</button>
                </nav>
            </header>
            <main className="dashboard-main">
                {renderFeature()}
            </main>
        </div>
    );
}

export default Dashboard;