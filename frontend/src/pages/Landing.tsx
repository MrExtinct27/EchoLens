import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Icon } from '../components/Icons';

function Landing() {
  const navigate = useNavigate();

  const features = [
    {
      icon: 'microphone',
      title: 'AI-Powered Transcription',
      description: 'Automatically transcribe customer support calls using OpenAI\'s advanced speech recognition technology.',
    },
    {
      icon: 'bot',
      title: 'Intelligent Analysis',
      description: 'Extract sentiment, topics, and insights from conversations using Groq LLM with structured JSON output.',
    },
    {
      icon: 'cloud',
      title: 'AWS Cloud Integration',
      description: 'Seamlessly pull your customer recordings directly from AWS S3 storage for automated processing and analysis.',
    },
    {
      icon: 'alertTriangle',
      title: 'Risk Detection',
      description: 'Automatically identify high-risk topics and potential escalations with explainable risk scoring.',
    },
    {
      icon: 'trendingUp',
      title: 'Trend Analysis',
      description: 'Monitor weekly trends, identify growing issues, and track performance metrics over time.',
    },
    {
      icon: 'lightbulb',
      title: 'Executive Insights',
      description: 'Get AI-generated executive summaries that transform raw data into actionable business insights.',
    },
  ];

  return (
    <div className="landing-page" style={{ minHeight: '100vh', position: 'relative' }}>
      <div className="landing-hero">
        <div className="hero-content">
          <div className="hero-badge">
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center' }}>
              <Icon name="sparkles" size={16} color="currentColor" />
              Powered by AI
            </span>
          </div>
          <h1 className="hero-title">
            <span className="gradient-text">EchoLens</span>
          </h1>
          <p className="hero-tagline">
            Conversation <span className="tagline-highlight analytics-word">analytics</span>, made <span className="tagline-highlight actionable-word">actionable</span>.
          </p>
          <p className="hero-description">
            Automatically transcribe, analyze, and gain insights from customer support calls.
            Make data-driven decisions with AI-powered analytics and executive summaries.
          </p>
          <button 
            className="btn-explore"
            onClick={() => navigate('/dashboard')}
          >
            Explore Product
            <span className="btn-arrow">→</span>
          </button>
        </div>
      </div>

      <div className="features-section">
        <div className="section-header">
          <h2 className="section-title">Everything You Need</h2>
          <p className="section-subtitle">Comprehensive conversation analytics platform powered by EchoLens</p>
        </div>
        <div className="features-grid">
          {features.map((feature, index) => (
            <div 
              key={index} 
              className="feature-card"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="feature-icon" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem' }}>
                <Icon name={feature.icon} size={48} color="var(--blue-400)" />
              </div>
              <h3 className="feature-title">{feature.title}</h3>
              <p className="feature-description">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>

      <footer className="landing-footer" style={{
        padding: '4rem 2rem',
        textAlign: 'center',
        background: 'linear-gradient(180deg, rgba(10, 22, 40, 0) 0%, rgba(10, 22, 40, 0.8) 100%)',
        borderTop: '1px solid rgba(66, 153, 225, 0.1)',
        marginTop: '4rem'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '0 1rem' }}>
          <p style={{
            fontSize: '1.25rem',
            fontWeight: 700,
            background: 'linear-gradient(135deg, #48bb78 0%, #38a169 50%, #2f855a 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            marginBottom: '2rem',
            lineHeight: '1.2',
            whiteSpace: 'nowrap',
            letterSpacing: '0.5px',
            animation: 'fadeInUp 0.8s ease-out'
          }}>
            Building the future of conversation intelligence, one line of code at a time 🚀
          </p>
          
          <div style={{
            marginTop: '2.5rem',
            paddingTop: '2rem',
            borderTop: '1px solid rgba(66, 153, 225, 0.2)'
          }}>
            <p style={{
              fontSize: '1.125rem',
              color: 'var(--text-secondary)',
              marginBottom: '1.5rem',
              fontWeight: 500
            }}>
              Developed with passion by
            </p>
            <p style={{
              fontSize: '1.5rem',
              fontWeight: 700,
              color: 'var(--text-primary)',
              marginBottom: '2rem',
              background: 'linear-gradient(135deg, #ffffff 0%, #90cdf4 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              Yash Mahajan
            </p>
            
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              gap: '2rem',
              flexWrap: 'wrap'
            }}>
              <a
                href="https://github.com/MrExtinct27"
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.75rem 1.5rem',
                  background: 'rgba(26, 47, 74, 0.6)',
                  border: '1px solid rgba(66, 153, 225, 0.3)',
                  borderRadius: '12px',
                  color: 'var(--text-primary)',
                  textDecoration: 'none',
                  transition: 'all 0.3s ease',
                  backdropFilter: 'blur(10px)',
                  fontSize: '1rem',
                  fontWeight: 600
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(66, 153, 225, 0.2)';
                  e.currentTarget.style.borderColor = 'rgba(66, 153, 225, 0.6)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 6px 25px rgba(66, 153, 225, 0.3)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(26, 47, 74, 0.6)';
                  e.currentTarget.style.borderColor = 'rgba(66, 153, 225, 0.3)';
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
                </svg>
                <span>GitHub</span>
              </a>
              
              <a
                href="https://www.linkedin.com/in/yashmahajan27/"
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.75rem 1.5rem',
                  background: 'rgba(26, 47, 74, 0.6)',
                  border: '1px solid rgba(66, 153, 225, 0.3)',
                  borderRadius: '12px',
                  color: 'var(--text-primary)',
                  textDecoration: 'none',
                  transition: 'all 0.3s ease',
                  backdropFilter: 'blur(10px)',
                  fontSize: '1rem',
                  fontWeight: 600
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(66, 153, 225, 0.2)';
                  e.currentTarget.style.borderColor = 'rgba(66, 153, 225, 0.6)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 6px 25px rgba(66, 153, 225, 0.3)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(26, 47, 74, 0.6)';
                  e.currentTarget.style.borderColor = 'rgba(66, 153, 225, 0.3)';
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path>
                  <rect x="2" y="9" width="4" height="12"></rect>
                  <circle cx="4" cy="4" r="2"></circle>
                </svg>
                <span>LinkedIn</span>
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default Landing;

