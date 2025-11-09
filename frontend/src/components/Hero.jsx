// src/components/Hero.jsx
import React from 'react';

const styles = {
    header: {
        textAlign: 'center',
        marginBottom: '0px',
        padding: '0px 0',
    },
    topRow: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '20px',
        marginBottom: '8px',
        flexWrap: 'wrap',
    },
    title: {
        fontSize: '2.2em',
        color: '#f9fafb',
        marginBottom: '0',
        whiteSpace: 'nowrap',
    },
    ctaButton: {
        padding: '10px 22px',
        backgroundColor: '#3b82f6',
        color: 'white',
        border: 'none',
        borderRadius: '5px',
        fontSize: '1.1em',
        cursor: 'pointer',
        textDecoration: 'none',
        fontWeight: 'bold',
        transition: 'background-color 0.2s',
        display: 'inline-block',
        marginRight: '0',
        marginTop: '30px',
        whiteSpace: 'nowrap',
    },
    infoRow: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '20px',
        width: '100%',
        fontSize: '1em',
        color: '#9ca3af',
        margin: '0 auto',
        flexWrap: 'wrap',
    },
    instructions: {
        margin: 0,
        padding: 0,
        color: '#d1d5db',
        fontSize: '0.95em',
        flex: 1,
        textAlign: 'center',
    }
};

const Hero = () => (
    <div style={styles.header}>
        <div style={styles.topRow}>
            <h1 style={styles.title}>SAATHI 🌍: </h1>
            <a 
                href="https://t.me/vernacular_chat_bot"
                target="_blank" 
                rel="noopener noreferrer" 
                style={styles.ctaButton}
            >
                Chat with the Bot Now!
            </a>
        </div>
        <div style={styles.infoRow}>
            <span style={styles.instructions}>A multimodal Telegram vernacular language bot bridging the digital divide. Search for @vernacular_chat_bot on Telegram or click the link above.</span>
        </div>
    </div>
);

export default Hero;