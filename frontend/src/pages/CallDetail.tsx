import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { callsApi, CallDetail } from '../api';
import { Icon } from '../components/Icons';

function CallDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [call, setCall] = useState<CallDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setError('Invalid call ID');
      setLoading(false);
      return;
    }

    const loadCallDetail = async () => {
      try {
        setLoading(true);
        setError(null);
        const callData = await callsApi.get(id);
        setCall(callData);
      } catch (err: any) {
        console.error('Error loading call detail:', err);
        setError(err.response?.data?.detail || 'Failed to load call details');
      } finally {
        setLoading(false);
      }
    };

    loadCallDetail();
  }, [id]);

  const formatTopicName = (topic: string) => {
    return topic.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case 'positive':
        return '#48bb78'; // green
      case 'negative':
        return '#f56565'; // red
      case 'neutral':
        return '#ed8936'; // orange
      default:
        return '#718096'; // gray
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toUpperCase()) {
      case 'DONE':
        return '#48bb78';
      case 'PROCESSING':
        return '#4299e1';
      case 'PENDING':
        return '#ed8936';
      case 'FAILED':
        return '#f56565';
      default:
        return '#718096';
    }
  };

  if (loading) {
    return (
      <div>
        <div style={{ marginBottom: '1rem' }}>
          <Link to="/dashboard" className="btn" style={{ display: 'inline-block' }}>
            ← Back to Dashboard
          </Link>
        </div>
        <h1 className="page-title">Call Details</h1>
        <div className="card">
          <div style={{ textAlign: 'center', padding: '4rem 2rem' }}>
            <div style={{ marginBottom: '1rem', animation: 'pulse 2s ease-in-out infinite', display: 'inline-block' }}>
              <Icon name="clock" size={48} color="var(--blue-300)" />
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>
              Loading call details...
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (error || !call) {
    return (
      <div>
        <div style={{ marginBottom: '1rem' }}>
          <Link to="/dashboard" className="btn" style={{ display: 'inline-block' }}>
            ← Back to Dashboard
          </Link>
        </div>
        <h1 className="page-title">Call Details</h1>
        <div className="card">
          <div style={{ padding: '2rem', textAlign: 'center' }}>
            <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Icon name="xCircle" size={48} color="#fc8181" />
            </div>
            <p style={{ color: '#fc8181', marginBottom: '1rem', fontSize: '1.1rem' }}>
              {error || 'Call not found'}
            </p>
            <button className="btn btn-primary" onClick={() => navigate('/dashboard')}>
              Go to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: '1rem' }}>
        <Link to="/dashboard" className="btn btn-primary" style={{ display: 'inline-block' }}>
          ← Back to Dashboard
        </Link>
      </div>
      <h1 className="page-title">Call Details</h1>

      {/* Call Information Card */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h2>Call Information</h2>
        <div style={{ padding: '1rem 0' }}>
          <div style={{ marginBottom: '1rem', display: 'grid', gridTemplateColumns: '200px 1fr', gap: '1rem', alignItems: 'center' }}>
            <strong style={{ color: 'var(--text-primary)' }}>Call ID:</strong>
            <code style={{ 
              fontSize: '0.9rem', 
              background: 'rgba(66, 153, 225, 0.1)', 
              padding: '0.5rem 0.75rem', 
              borderRadius: '6px',
              color: 'var(--blue-300)',
              border: '1px solid rgba(66, 153, 225, 0.2)'
            }}>
              {call.id}
            </code>
          </div>
          <div style={{ marginBottom: '1rem', display: 'grid', gridTemplateColumns: '200px 1fr', gap: '1rem', alignItems: 'center' }}>
            <strong style={{ color: 'var(--text-primary)' }}>Status:</strong>
            <span 
              className={`status-badge ${call.status.toLowerCase()}`}
            >
              {call.status}
            </span>
          </div>
          <div style={{ marginBottom: '1rem', display: 'grid', gridTemplateColumns: '200px 1fr', gap: '1rem', alignItems: 'center' }}>
            <strong style={{ color: 'var(--text-primary)' }}>Created At:</strong>
            <span style={{ color: 'var(--text-secondary)' }}>{formatDate(call.created_at)}</span>
          </div>
          {call.duration_sec && (
            <div style={{ marginBottom: '1rem', display: 'grid', gridTemplateColumns: '200px 1fr', gap: '1rem', alignItems: 'center' }}>
              <strong style={{ color: 'var(--text-primary)' }}>Duration:</strong>
              <span style={{ color: 'var(--text-secondary)' }}>{Math.round(call.duration_sec)} seconds</span>
            </div>
          )}
          <div style={{ marginBottom: '1rem', display: 'grid', gridTemplateColumns: '200px 1fr', gap: '1rem', alignItems: 'center' }}>
            <strong style={{ color: 'var(--text-primary)' }}>Audio File:</strong>
            <code style={{ 
              fontSize: '0.85rem', 
              color: 'var(--text-muted)',
              background: 'rgba(26, 47, 74, 0.5)',
              padding: '0.25rem 0.5rem',
              borderRadius: '4px'
            }}>
              {call.audio_object_key}
            </code>
          </div>
        </div>
      </div>

      {/* Analysis Card */}
      {call.analysis ? (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h2>Analysis</h2>
          <div style={{ padding: '1rem 0' }}>
            <div style={{ marginBottom: '1rem', display: 'grid', gridTemplateColumns: '200px 1fr', gap: '1rem', alignItems: 'center' }}>
              <strong style={{ color: 'var(--text-primary)' }}>Issue (Topic):</strong>
              <span style={{ 
                background: 'rgba(66, 153, 225, 0.2)',
                border: '1px solid rgba(66, 153, 225, 0.4)',
                color: 'var(--blue-300)',
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                display: 'inline-block',
                fontWeight: '600'
              }}>
                {formatTopicName(call.analysis.topic)}
              </span>
            </div>
            <div style={{ marginBottom: '1rem', display: 'grid', gridTemplateColumns: '200px 1fr', gap: '1rem', alignItems: 'center' }}>
              <strong style={{ color: 'var(--text-primary)' }}>Sentiment:</strong>
              <span className="status-badge" style={{ 
                background: getSentimentColor(call.analysis.sentiment) === '#48bb78' ? 'rgba(72, 187, 120, 0.2)' :
                           getSentimentColor(call.analysis.sentiment) === '#f56565' ? 'rgba(245, 101, 101, 0.2)' :
                           'rgba(237, 137, 54, 0.2)',
                border: `1px solid ${getSentimentColor(call.analysis.sentiment)}`,
                color: getSentimentColor(call.analysis.sentiment),
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                display: 'inline-block',
                fontWeight: '600',
                textTransform: 'capitalize'
              }}>
                {call.analysis.sentiment}
              </span>
            </div>
            <div style={{ marginBottom: '1rem', display: 'grid', gridTemplateColumns: '200px 1fr', gap: '1rem', alignItems: 'center' }}>
              <strong style={{ color: 'var(--text-primary)' }}>Problem Resolved:</strong>
              <span className="status-badge" style={{ 
                background: call.analysis.problem_resolved ? 'rgba(72, 187, 120, 0.2)' : 'rgba(245, 101, 101, 0.2)',
                border: `1px solid ${call.analysis.problem_resolved ? '#48bb78' : '#f56565'}`,
                color: call.analysis.problem_resolved ? '#9ae6b4' : '#fc8181',
                padding: '0.5rem 1rem',
                borderRadius: '8px',
                display: 'inline-block',
                fontWeight: '600'
              }}>
                {call.analysis.problem_resolved ? 'Yes' : 'No'}
              </span>
            </div>
            {call.analysis.confidence !== null && (
              <div style={{ marginBottom: '1rem', display: 'grid', gridTemplateColumns: '200px 1fr', gap: '1rem', alignItems: 'center' }}>
                <strong style={{ color: 'var(--text-primary)' }}>Confidence:</strong>
                <span style={{ color: 'var(--text-secondary)' }}>{Math.round(call.analysis.confidence * 100)}%</span>
              </div>
            )}
            <div style={{ marginTop: '1.5rem' }}>
              <strong style={{ display: 'block', marginBottom: '0.75rem', color: 'var(--text-primary)' }}>Summary:</strong>
              <div style={{ 
                background: 'rgba(26, 47, 74, 0.5)',
                padding: '1.5rem',
                borderRadius: '12px',
                border: '1px solid var(--card-border)',
                lineHeight: '1.8',
                color: 'var(--text-secondary)'
              }}>
                {call.analysis.summary}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h2>Analysis</h2>
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            {call.status === 'PROCESSING' || call.status === 'PENDING' ? (
              <div>
                <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon name="clock" size={48} color="var(--text-muted)" />
                </div>
                <p>Analysis is still in progress. Please check back later.</p>
              </div>
            ) : (
              <div>
                <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon name="fileText" size={48} color="var(--text-muted)" />
                </div>
                <p>Analysis not available for this call.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Transcript Card */}
      {call.transcript ? (
        <div className="card">
          <h2>Transcript</h2>
          <div style={{ padding: '1rem 0' }}>
            <div style={{ marginBottom: '1rem', display: 'grid', gridTemplateColumns: '200px 1fr', gap: '1rem', alignItems: 'center' }}>
              <strong style={{ color: 'var(--text-primary)' }}>Model:</strong>
              <code style={{ 
                fontSize: '0.85rem', 
                color: 'var(--text-muted)',
                background: 'rgba(26, 47, 74, 0.5)',
                padding: '0.25rem 0.5rem',
                borderRadius: '4px'
              }}>
                {call.transcript.model || 'Unknown'}
              </code>
            </div>
            <div style={{ marginTop: '1.5rem' }}>
              <strong style={{ display: 'block', marginBottom: '0.75rem', color: 'var(--text-primary)' }}>Full Transcript:</strong>
              <div style={{ 
                background: 'rgba(26, 47, 74, 0.5)',
                padding: '1.5rem',
                borderRadius: '12px',
                border: '1px solid var(--card-border)',
                lineHeight: '1.8',
                maxHeight: '500px',
                overflowY: 'auto',
                whiteSpace: 'pre-wrap',
                wordWrap: 'break-word',
                color: 'var(--text-secondary)'
              }}>
                {call.transcript.text}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="card">
          <h2>Transcript</h2>
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
            {call.status === 'PROCESSING' || call.status === 'PENDING' ? (
              <div>
                <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon name="clock" size={48} color="var(--text-muted)" />
                </div>
                <p>Transcript is still being generated. Please check back later.</p>
              </div>
            ) : (
              <div>
                <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Icon name="fileText" size={48} color="var(--text-muted)" />
                </div>
                <p>Transcript not available for this call.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default CallDetailPage;

