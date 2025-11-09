import React, { useState } from 'react';
import { useDashboardData } from './hooks/useDashboardData';
import Hero from './components/Hero'; 
import ImpactAtAGlance from './components/ImpactAtAGlance'; 
import WeeklyTrends from './components/WeeklyTrends'; 

const styles = {
    container: {
        backgroundColor: '#1f2937', 
        minHeight: '100vh',
        color: '#f9fafb',
        padding: '20px',
        maxWidth: '1200px', /* Limit width for better reading */
        margin: '0 auto',
    },
    divider: {
        borderTop: '1px solid #374151', 
        margin: '40px 0',
    }
};

function App() {
    const { data, isLoading, error } = useDashboardData();

    if (isLoading) {
        return <div style={styles.container}>Loading Dashboard...</div>;
    }

    if (error) {
        return <div style={styles.container}>ERROR: {error}</div>;
    }

    return (
        <div style={styles.container}>
            {/* Hero Section */}
            {/* <Hero /> */}
            
            {/*<div style={styles.divider} />*/}

            {/* Overall Stats */}
            <ImpactAtAGlance overallData={data.overall} />

            {/*<div style={styles.divider} />*/}
            
            {/* Weekly Trends with Slider */}
            <WeeklyTrends weeklyData={data.weekly} />
            
        </div>
    );
}

export default App;