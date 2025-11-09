// src/components/ImpactAtAGlance.jsx
import React, { useState, useMemo } from 'react';
import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

const styles = {
    sectionTitle: { fontSize: '2em', marginBottom: '0px', marginTop: '0px' },
    kpiGrid: { display: 'flex', justifyContent: 'space-between', gap: '10px', marginBottom: '10px' },
    kpiCard: { flex: 1, padding: '12px', backgroundColor: '#374151', borderRadius: '8px', textAlign: 'center', margin: 0 },
    kpiValue: { fontSize: '2.2em', fontWeight: 'bold', color: '#3b82f6', margin: 0 },
    kpiLabel: { fontSize: '1em', color: '#9ca3af', margin: 0 },
    chartGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', margin: 0 },
    dropdown: { padding: '8px', borderRadius: '5px', border: '1px solid #9ca3af', backgroundColor: '#374151', color: 'white', marginTop: '4px', marginBottom: '0' },
};

// Helper function to calculate percentage
const calculatePercentage = (part, whole) => whole === 0 ? 0 : ((part / whole) * 100).toFixed(1);

// Helper function to camel case a string (capitalize first letter)
const camelCase = str => str.charAt(0).toUpperCase() + str.slice(1);

const SHOW_ACTIVE_USERS = false; // Feature flag to toggle active users display

const ImpactAtAGlance = ({ overallData }) => {
    const { interactions, active_users, voice, language_distribution } = overallData;
    const text_interactions = interactions - voice;
    const voice_percent = calculatePercentage(voice, interactions);

    // --- KPI 4 & 5 Logic ---
    const allLanguages = useMemo(() => language_distribution.map(item => item.lang), [language_distribution]);
    const [selectedLang, setSelectedLang] = useState(allLanguages[0]);

    // Data for Top Languages Pie Chart (KPI 4)
    const topLangChartData = useMemo(() => {
        const sortedLangs = [...language_distribution].sort((a, b) => b.interactions - a.interactions);
        const top5 = sortedLangs.slice(0, 5);
        const otherInteractions = sortedLangs.slice(5).reduce((sum, item) => sum + item.interactions, 0);

        return {
            labels: [...top5.map(l => camelCase(l.lang)), otherInteractions > 0 ? 'Other' : null].filter(Boolean),
            datasets: [{
                data: [...top5.map(l => l.interactions), otherInteractions].filter(n => n > 0),
                backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#6366f1', '#4b5563'],
                borderWidth: 0,
            }],
        };
    }, [language_distribution]);

    // Data for Voice Per Language Pie Chart (KPI 5)
    const selectedLangData = language_distribution.find(item => item.lang === selectedLang) || { interactions: 0, voice: 0 };
    const text_for_lang = selectedLangData.interactions - selectedLangData.voice;

    const langVoiceChartData = {
        labels: ['Voice Interactions', 'Text Interactions'],
        datasets: [{
            data: [selectedLangData.voice, text_for_lang],
            backgroundColor: ['#3b82f6', '#9ca3af'],
            borderWidth: 0,
        }],
    };

    return (
        <section>
            <h2 style={styles.sectionTitle}>Lifetime Impact</h2>
            {/* NEW FLEX GRID: 3 columns */}
            <div style={{ display: 'flex', gap: '40px', width: '100%', alignItems: 'stretch', marginBottom: '40px' }}>
                {/* COLUMN 1: Vertically stacked KPI 1 & 3 */}
                <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', flex: 1, gap: '20px' }}>
                    <div style={{ ...styles.kpiCard, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
                        <div style={styles.kpiValue}>{interactions.toLocaleString()}</div>
                        <div style={styles.kpiLabel}>Total Interactions</div>
                    </div>
                    <div style={{ ...styles.kpiCard, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
                        <div style={styles.kpiValue}>{voice_percent}% Voice</div>
                        <div style={styles.kpiLabel}>Voice vs Text</div>
                        <div style={{ fontSize: '0.8em', color: '#6ee7b7' }}>({voice} Voice / {text_interactions} Text)</div>
                    </div>
                </div>
                {/* COLUMN 2: KPI 4 Pie Chart */}
                <div style={{ ...styles.kpiCard, flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                    <h3 style={{ marginBottom: '15px' }}>Top Languages (Total Interactions)</h3>
                    <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px' }}>
                        <Pie data={topLangChartData} options={{ responsive: true, maintainAspectRatio: false }} />
                    </div>
                </div>
                {/* COLUMN 3: KPI 5 Pie Chart */}
                <div style={{ ...styles.kpiCard, flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                    <h3 style={{ marginBottom: '15px' }}>Voice vs Text for:</h3>
                    <select 
                        value={selectedLang} 
                        onChange={(e) => setSelectedLang(e.target.value)}
                        style={styles.dropdown}
                    >
                        {allLanguages.map(lang => (
                            <option key={lang} value={lang}>{camelCase(lang)}</option>
                        ))}
                    </select>
                    <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '300px', marginTop: '10px' }}>
                        <Pie data={langVoiceChartData} options={{ responsive: true, maintainAspectRatio: false }} />
                    </div>
                    <div style={{ fontSize: '0.8em', color: '#9ca3af' }}>
                        Total {camelCase(selectedLang)} Interactions: {selectedLangData.interactions}
                    </div>
                </div>
            </div>
        </section>
    );
};

export default ImpactAtAGlance;