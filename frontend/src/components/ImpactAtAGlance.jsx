// src/components/ImpactAtAGlance.jsx
import React, { useState, useMemo } from 'react';
import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

const styles = {
    sectionTitle: { fontSize: '2em', marginBottom: '20px' },
    kpiGrid: { display: 'flex', justifyContent: 'space-between', gap: '20px', marginBottom: '40px' },
    kpiCard: { flex: 1, padding: '20px', backgroundColor: '#374151', borderRadius: '8px', textAlign: 'center' },
    kpiValue: { fontSize: '2.5em', fontWeight: 'bold', color: '#3b82f6' }, // Accent Blue
    kpiLabel: { fontSize: '1em', color: '#9ca3af' },
    chartGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '40px' },
    dropdown: { padding: '10px', borderRadius: '5px', border: '1px solid #9ca3af', backgroundColor: '#374151', color: 'white', marginTop: '10px' },
};

// Helper function to calculate percentage
const calculatePercentage = (part, whole) => whole === 0 ? 0 : ((part / whole) * 100).toFixed(1);

const ImpactAtAGlance = ({ overallData }) => {
    const { total_interactions, active_users, voice_interactions, language_distribution } = overallData;
    const text_interactions = total_interactions - voice_interactions;
    const voice_percent = calculatePercentage(voice_interactions, total_interactions);

    // --- KPI 4 & 5 Logic ---
    const allLanguages = useMemo(() => language_distribution.map(item => item.lang), [language_distribution]);
    const [selectedLang, setSelectedLang] = useState(allLanguages[0]);

    // Data for Top Languages Pie Chart (KPI 4)
    const topLangChartData = useMemo(() => {
        const sortedLangs = [...language_distribution].sort((a, b) => b.interactions - a.interactions);
        const top5 = sortedLangs.slice(0, 5);
        const otherInteractions = sortedLangs.slice(5).reduce((sum, item) => sum + item.interactions, 0);

        return {
            labels: [...top5.map(l => l.lang), otherInteractions > 0 ? 'Other' : null].filter(Boolean),
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
            
            {/* KPI GRID (1-3) */}
            <div style={styles.kpiGrid}>
                <div style={styles.kpiCard}>
                    <div style={styles.kpiValue}>{total_interactions.toLocaleString()}</div>
                    <div style={styles.kpiLabel}>Total Interactions</div>
                </div>
                <div style={styles.kpiCard}>
                    <div style={styles.kpiValue}>{active_users.toLocaleString()}</div>
                    <div style={styles.kpiLabel}>Active Users</div>
                </div>
                <div style={styles.kpiCard}>
                    <div style={styles.kpiValue}>{voice_percent}% Voice</div>
                    <div style={styles.kpiLabel}>Voice vs Text</div>
                    <div style={{ fontSize: '0.8em', color: '#6ee7b7' }}>({voice_interactions} Voice / {text_interactions} Text)</div>
                </div>
            </div>

            {/* CHART GRID (4 & 5) */}
            <div style={styles.chartGrid}>
                {/* KPI 4: Top Languages */}
                <div style={{...styles.kpiCard, flex: 1}}>
                    <h3 style={{ marginBottom: '15px' }}>Top Languages (Total Interactions)</h3>
                    <div style={{ height: '300px', display: 'flex', justifyContent: 'center' }}>
                         <Pie data={topLangChartData} options={{ responsive: true, maintainAspectRatio: false }} />
                    </div>
                </div>

                {/* KPI 5: Voice Per Language */}
                <div style={{...styles.kpiCard, flex: 1}}>
                    <h3 style={{ marginBottom: '15px' }}>Voice vs Text for: </h3>
                    <select 
                        value={selectedLang} 
                        onChange={(e) => setSelectedLang(e.target.value)}
                        style={styles.dropdown}
                    >
                        {allLanguages.map(lang => (
                            <option key={lang} value={lang}>{lang}</option>
                        ))}
                    </select>
                    
                    <div style={{ height: '300px', display: 'flex', justifyContent: 'center', marginTop: '10px' }}>
                        <Pie data={langVoiceChartData} options={{ responsive: true, maintainAspectRatio: false }} />
                    </div>
                    <div style={{ fontSize: '0.8em', color: '#9ca3af' }}>
                        Total {selectedLang} Interactions: {selectedLangData.interactions}
                    </div>
                </div>
            </div>
        </section>
    );
};

export default ImpactAtAGlance;