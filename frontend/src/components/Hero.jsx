// src/components/Hero.jsx
import React from 'react';

const styles = {
    header: {
        textAlign: 'center',
        marginBottom: '30px',
    },
    title: {
        fontSize: '3em',
        color: '#f9fafb',
        marginBottom: '10px',
    },
    description: {
        fontSize: '1.2em',
        color: '#9ca3af',
        maxWidth: '800px',
        margin: '0 auto 20px',
    },
    ctaButton: {
        padding: '12px 25px',
        backgroundColor: '#3b82f6', // --accent-blue
        color: 'white',
        border: 'none',
        borderRadius: '5px',
        fontSize: '1.1em',
        cursor: 'pointer',
        textDecoration: 'none',
        fontWeight: 'bold',
        transition: 'background-color 0.2s',
        display: 'inline-block',
        marginRight: '15px',
    },
    instructions: {
        marginTop: '10px',
        color: '#d1d5db',
    }
};

const Hero = () => (
    <div style={styles.header}>
        <h1 style={styles.title}>Project SAATHI: Your Language, Your AI. 🌍</h1>
        <p style={styles.description}>A multimodal Telegram bot bridging the digital divide with vernacular language processing.</p>
        <a 
            href="https://t.me/vernacular_chat_bot"
            target="_blank" 
            rel="noopener noreferrer" 
            style={styles.ctaButton}
        >
            Chat with the Bot Now!
        </a>
        <p style={styles.instructions}>Search for @vernacular_chat_bot on Telegram or click the link above.</p>
    </div>
);

export default Hero;