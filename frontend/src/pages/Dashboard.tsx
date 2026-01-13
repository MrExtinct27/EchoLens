import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  callsApi,
  metricsApi,
  analyticsApi,
  Call,
  TopicCount,
  WeeklySpikeAlert,
  TopicTrend,
  ResolutionEffectiveness,
  EscalationRisk,
  ExecutiveSummary,
  CallStatistics,
} from '../api';
import { Icon } from '../components/Icons';

function Dashboard() {
  // Recent calls (paginated)
  const [calls, setCalls] = useState<Call[]>([]);
  const [callsOffset, setCallsOffset] = useState(0);
  const [hasMoreCalls, setHasMoreCalls] = useState(true);
  const [loadingMoreCalls, setLoadingMoreCalls] = useState(false);

  // Analytics / metrics
  const [callStatistics, setCallStatistics] = useState<CallStatistics | null>(null);
  const [topicCounts, setTopicCounts] = useState<TopicCount[]>([]);
  const [alerts, setAlerts] = useState<WeeklySpikeAlert[]>([]);
  const [topicTrends, setTopicTrends] = useState<TopicTrend[]>([]);
  const [resolutionEffectiveness, setResolutionEffectiveness] = useState<ResolutionEffectiveness[]>([]);
  const [escalationRisks, setEscalationRisks] = useState<EscalationRisk[]>([]);
  const [executiveSummary, setExecutiveSummary] = useState<ExecutiveSummary | null>(null);

  const [loading, setLoading] = useState(true);
  const [trendView, setTrendView] = useState<'volume' | 'negative'>('volume');
  const [sortBy, setSortBy] = useState<'topic' | 'resolution' | 'negative' | 'confidence'>('topic');
  const [filterRisk, setFilterRisk] = useState(false);

  // Initial load & manual refresh (includes executive summary)
  const loadData = async (resetPagination: boolean = false) => {
    try {
      setLoading(true);
      const [
        callsData,
        statisticsData,
        topicData,
        alertsData,
        trendsData,
        resolutionData,
        riskData,
        summaryData,
      ] = await Promise.all([
        callsApi.list(10, 0),
        metricsApi.callStatistics(),
        metricsApi.topicCounts(),
        metricsApi.weeklySpikes(),
        analyticsApi.topicTrends(8),
        analyticsApi.resolutionEffectiveness(),
        analyticsApi.escalationRisk(),
        analyticsApi.executiveSummary(),
      ]);

      // Recent calls pagination
      if (resetPagination) {
        setCalls(callsData);
        setCallsOffset(10);
        setHasMoreCalls(callsData.length === 10);
      } else {
        setCalls(callsData);
        setCallsOffset(10);
        setHasMoreCalls(callsData.length === 10);
      }

      // Analytics
      setCallStatistics(statisticsData);
      setTopicCounts(topicData);
      setAlerts(alertsData);
      setTopicTrends(trendsData);
      setResolutionEffectiveness(resolutionData);
      setEscalationRisks(riskData);
      setExecutiveSummary(summaryData);
    } catch (err) {
      console.error('Error loading dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Refresh only Recent Calls section
  const refreshRecentCalls = async () => {
    try {
      const callsData = await callsApi.list(10, 0);
      setCalls(callsData);
      setCallsOffset(10);
      setHasMoreCalls(callsData.length === 10);
    } catch (err) {
      console.error('Error refreshing recent calls:', err);
    }
  };

  // Load more calls (pagination)
  const loadMoreCalls = async () => {
    if (loadingMoreCalls || !hasMoreCalls) return;
    try {
      setLoadingMoreCalls(true);
      const newCalls = await callsApi.list(10, callsOffset);
      if (newCalls.length === 0) {
        setHasMoreCalls(false);
      } else {
        setCalls(prev => [...prev, ...newCalls]);
        const nextOffset = callsOffset + newCalls.length;
        setCallsOffset(nextOffset);
        if (newCalls.length < 10) {
          setHasMoreCalls(false);
        }
      }
    } catch (err) {
      console.error('Error loading more calls:', err);
    } finally {
      setLoadingMoreCalls(false);
    }
  };

  // Initial load only (no polling)
  useEffect(() => {
    loadData(false);
  }, []);

  const formatTopicName = (topic: string) =>
    topic
      .split('_')
      .map(w => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');

  const formatDate = (dateString: string) => {
    const d = new Date(dateString);
    return d.toLocaleString();
  };

  const getRiskColor = (score: number): string => {
    if (score >= 0.7) return '#e53e3e';
    if (score >= 0.5) return '#dd6b20';
    if (score >= 0.3) return '#d69e2e';
    return '#38a169';
  };

  const getTrendColor = (trend: string): string => {
    if (trend === 'up') return '#e53e3e';
    if (trend === 'down') return '#38a169';
    return '#718096';
  };

  const getTopicColor = (topic: string): string => {
    const colors = [
      '#4299e1', // blue
      '#48bb78', // green
      '#ed8936', // orange
      '#9f7aea', // purple
      '#f56565', // red
      '#38b2ac', // teal
      '#f6ad55', // yellow-orange
      '#fc8181', // light red
      '#63b3ed', // light blue
      '#68d391', // light green
    ];
    const index = topic.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return colors[index % colors.length];
  };

  const prepareTrendChartData = () => {
    if (topicTrends.length === 0) return [];
    const maxWeeks = Math.max(...topicTrends.map(t => t.weekly_counts.length));
    const data: any[] = [];
    for (let i = 0; i < maxWeeks; i++) {
      const point: any = { week: `Week ${i + 1}` };
      topicTrends.forEach(trend => {
        if (trendView === 'volume') {
          point[formatTopicName(trend.topic)] = trend.weekly_counts[i] || 0;
        } else {
          point[formatTopicName(trend.topic)] = trend.weekly_negative_rates[i]
            ? Number((trend.weekly_negative_rates[i] * 100).toFixed(1))
            : 0;
        }
      });
      data.push(point);
    }
    return data;
  };

  const sortedResolutionData = [...resolutionEffectiveness].sort((a, b) => {
    switch (sortBy) {
      case 'resolution':
        return b.resolution_rate - a.resolution_rate;
      case 'negative':
        return b.negative_rate - a.negative_rate;
      case 'confidence':
        return (b.avg_confidence || 0) - (a.avg_confidence || 0);
      default:
        return a.topic.localeCompare(b.topic);
    }
  });

  const filteredEscalationRisks = filterRisk
    ? escalationRisks.filter(r => r.risk_score >= 0.6)
    : escalationRisks;

  if (loading) {
    return (
      <div>
        <h1 className="page-title">Analytics Dashboard</h1>
        <div className="card">
          <div style={{ textAlign: 'center', padding: '4rem 2rem' }}>
            <div
              style={{
                marginBottom: '1rem',
                animation: 'pulse 2s ease-in-out infinite',
                display: 'inline-block',
              }}
            >
              <Icon name="clock" size={48} color="var(--blue-300)" />
            </div>
            <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>
              Loading dashboard data...
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="page-title">Analytics Dashboard</h1>

      {/* Executive Summary */}
      {executiveSummary && (
        <div
          className="card executive-summary-card"
          style={{
            background:
              'linear-gradient(135deg, rgba(66, 153, 225, 0.3) 0%, rgba(49, 130, 206, 0.3) 50%, rgba(44, 82, 130, 0.3) 100%)',
            border: '1px solid rgba(66, 153, 225, 0.5)',
            color: 'white',
            marginBottom: '2rem',
            padding: '2rem',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: '1rem',
              gap: '0.75rem',
            }}
          >
            <div style={{ animation: 'pulse 2s ease-in-out infinite' }}>
              <Icon name="sparkles" size={28} color="rgba(255, 255, 255, 0.9)" />
            </div>
            <h2 style={{ margin: 0 }}>
              AI-Generated Executive Summary
            </h2>
          </div>
          <p
            style={{
              fontSize: '1.125rem',
              lineHeight: '1.8',
              margin: 0,
              fontStyle: 'italic',
              color: 'rgba(255, 255, 255, 0.95)',
            }}
          >
            {executiveSummary.summary}
          </p>
        </div>
      )}

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="card" style={{ marginBottom: '2rem' }}>
          <h2>Weekly Spike Alerts</h2>
          <ul>
            {alerts.map((a, idx) => (
              <li key={idx} style={{ marginBottom: '0.5rem' }}>
                {a.message}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="dashboard-grid">
        {/* Topic Trends */}
        <div className="card" style={{ gridColumn: 'span 3' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1rem',
            }}
          >
            <h2>Topic Trend Analysis</h2>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                className={trendView === 'volume' ? 'btn btn-primary' : 'btn'}
                onClick={() => setTrendView('volume')}
              >
                Volume
              </button>
              <button
                className={trendView === 'negative' ? 'btn btn-primary' : 'btn'}
                onClick={() => setTrendView('negative')}
              >
                Negative %
              </button>
            </div>
          </div>
          {topicTrends.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>Not enough data yet.</p>
          ) : (
            <div style={{ height: 320 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={prepareTrendChartData()}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="week" stroke="#a0aec0" />
                  <YAxis
                    stroke="#a0aec0"
                    tickFormatter={v => (trendView === 'negative' ? `${v}%` : v)}
                  />
                  <Tooltip
                    contentStyle={{
                      background: '#1a202c',
                      border: '1px solid rgba(255,255,255,0.1)',
                    }}
                  />
                  <Legend />
                  {topicTrends.map(trend => (
                    <Line
                      key={trend.topic}
                      type="monotone"
                      dataKey={formatTopicName(trend.topic)}
                      stroke={getTopicColor(trend.topic)}
                      strokeWidth={2}
                      dot={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Calls by Topic */}
        <div className="card">
          <h2>Calls by Topic</h2>
          {topicCounts.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>No calls analyzed yet.</p>
          ) : (
            <div style={{ height: 260 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topicCounts}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis
                    dataKey="topic"
                    stroke="#a0aec0"
                    tickFormatter={v => formatTopicName(v)}
                  />
                  <YAxis stroke="#a0aec0" allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      background: '#1a202c',
                      border: '1px solid rgba(255,255,255,0.1)',
                    }}
                    formatter={(value: any, name: any, props: any) => [
                      value,
                      'Calls',
                    ]}
                    labelFormatter={value => formatTopicName(String(value))}
                  />
                  <Bar dataKey="count" fill="#63b3ed" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Call Statistics */}
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <h2>Call Statistics</h2>
          {callStatistics ? (
            <>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(4, minmax(0, 1fr))',
                  gap: '1rem',
                  marginTop: '1rem',
                }}
              >
                <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(66, 153, 225, 0.1)', borderRadius: '12px', border: '1px solid rgba(66, 153, 225, 0.2)' }}>
                  <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '0.5rem' }}>
                    <Icon name="phone" size={32} color="var(--blue-300)" />
                  </div>
                  <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {callStatistics.total_calls}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                    Total Calls
                  </div>
                </div>
                <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(72, 187, 120, 0.1)', borderRadius: '12px', border: '1px solid rgba(72, 187, 120, 0.2)' }}>
                  <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '0.5rem' }}>
                    <Icon name="checkCircle" size={32} color="#48bb78" />
                  </div>
                  <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {callStatistics.done_calls}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                    Successful
                  </div>
                </div>
                <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(237, 137, 54, 0.1)', borderRadius: '12px', border: '1px solid rgba(237, 137, 54, 0.2)' }}>
                  <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '0.5rem' }}>
                    <Icon name="clock" size={32} color="#ed8936" />
                  </div>
                  <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {callStatistics.processing_calls + callStatistics.pending_calls}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                    In Progress
                  </div>
                </div>
                <div style={{ textAlign: 'center', padding: '1rem', background: 'rgba(245, 101, 101, 0.1)', borderRadius: '12px', border: '1px solid rgba(245, 101, 101, 0.2)' }}>
                  <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '0.5rem' }}>
                    <Icon name="xCircle" size={32} color="#f56565" />
                  </div>
                  <div style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    {callStatistics.failed_calls}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                    Failed
                  </div>
                </div>
              </div>
              <div
                style={{
                  marginTop: '1.25rem',
                  padding: '1.25rem',
                  background: 'rgba(26, 47, 74, 0.5)',
                  borderRadius: '12px',
                }}
              >
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                    gap: '1rem',
                  }}
                >
                  <div>
                    <div
                      style={{
                        fontSize: '0.8rem',
                        color: 'var(--text-secondary)',
                        marginBottom: '0.5rem',
                      }}
                    >
                      Success Rate
                    </div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>
                      {callStatistics.success_rate.toFixed(1)}%
                    </div>
                  </div>
                  <div>
                    <div
                      style={{
                        fontSize: '0.8rem',
                        color: 'var(--text-secondary)',
                        marginBottom: '0.5rem',
                      }}
                    >
                      Unique Topics
                    </div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>
                      {callStatistics.unique_topics}
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <p style={{ color: 'var(--text-muted)', marginTop: '1rem' }}>
              No call statistics available yet.
            </p>
          )}
        </div>

        {/* Resolution Effectiveness */}
        <div className="card" style={{ gridColumn: 'span 2' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1rem',
            }}
          >
            <h2>Resolution Effectiveness</h2>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                className={sortBy === 'topic' ? 'btn btn-primary' : 'btn'}
                onClick={() => setSortBy('topic')}
              >
                Topic
              </button>
              <button
                className={sortBy === 'resolution' ? 'btn btn-primary' : 'btn'}
                onClick={() => setSortBy('resolution')}
              >
                Resolution %
              </button>
              <button
                className={sortBy === 'negative' ? 'btn btn-primary' : 'btn'}
                onClick={() => setSortBy('negative')}
              >
                Negative %
              </button>
              <button
                className={sortBy === 'confidence' ? 'btn btn-primary' : 'btn'}
                onClick={() => setSortBy('confidence')}
              >
                Confidence
              </button>
            </div>
          </div>
          {sortedResolutionData.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>No resolution data available yet.</p>
          ) : (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Topic</th>
                    <th>Resolution %</th>
                    <th>Negative %</th>
                    <th>Avg Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedResolutionData.map(row => {
                    const resolutionColor = row.resolution_rate >= 0.7 ? '#48bb78' : row.resolution_rate >= 0.5 ? '#f6ad55' : '#f56565';
                    const negativeColor = row.negative_rate >= 0.6 ? '#f56565' : row.negative_rate >= 0.3 ? '#f6ad55' : '#48bb78';
                    const confidenceColor = (row.avg_confidence || 0) >= 0.7 ? '#48bb78' : (row.avg_confidence || 0) >= 0.5 ? '#f6ad55' : '#f56565';
                    return (
                      <tr key={row.topic}>
                        <td style={{ fontWeight: 600, color: getTopicColor(row.topic) }}>{formatTopicName(row.topic)}</td>
                        <td style={{ color: resolutionColor, fontWeight: 600 }}>{Math.round(row.resolution_rate * 100)}%</td>
                        <td style={{ color: negativeColor, fontWeight: 600 }}>{Math.round(row.negative_rate * 100)}%</td>
                        <td style={{ color: confidenceColor, fontWeight: 600 }}>{Math.round((row.avg_confidence || 0) * 100)}%</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Escalation Risks */}
        <div className="card">
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1rem',
            }}
          >
            <h2>Escalation Risks</h2>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={filterRisk}
                onChange={e => setFilterRisk(e.target.checked)}
              />
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Show high risk only (≥ 0.6)
              </span>
            </label>
          </div>
          {filteredEscalationRisks.length === 0 ? (
            <p style={{ color: 'var(--text-muted)' }}>No high-risk topics detected.</p>
          ) : (
            <div className="escalation-risks-scroll" style={{ maxHeight: 260, overflowY: 'auto' }}>
              {filteredEscalationRisks.map(risk => (
                <div
                  key={risk.topic}
                  style={{
                    padding: '0.75rem 1rem',
                    borderRadius: '8px',
                    border: '1px solid rgba(255,255,255,0.08)',
                    marginBottom: '0.75rem',
                    background: 'rgba(26, 47, 74, 0.7)',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '0.35rem',
                    }}
                  >
                    <span style={{ fontWeight: 600 }}>{formatTopicName(risk.topic)}</span>
                    <span
                      style={{
                        fontSize: '0.85rem',
                        fontWeight: 600,
                        color: getRiskColor(risk.risk_score),
                      }}
                    >
                      Risk: {risk.risk_score.toFixed(2)}
                    </span>
                  </div>
                  <ul style={{ paddingLeft: '1.25rem', margin: 0, fontSize: '0.85rem' }}>
                    {risk.drivers.map((d, i) => (
                      <li key={i} style={{ color: 'var(--text-secondary)' }}>
                        {d}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Calls */}
        <div className="card" style={{ gridColumn: 'span 3' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1rem',
              gap: '0.75rem',
              flexWrap: 'wrap',
            }}
          >
            <h2 style={{ margin: 0, flex: '1 1 auto', minWidth: 0 }}>
              Recent Calls {calls.length > 0 && `(${calls.length})`}
            </h2>
            <button
              className="btn-icon-primary"
              onClick={refreshRecentCalls}
              title="Refresh Recent Calls"
            >
              <Icon name="refreshCw" size={20} className="icon-spin-on-hover" />
            </button>
          </div>

          <div className="table-container">
            {calls.length > 0 ? (
              <table>
                <thead>
                  <tr>
                    <th>Call ID</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th>Audio Key</th>
                  </tr>
                </thead>
                <tbody>
                  {calls.map(call => (
                    <tr key={call.id}>
                      <td>
                        <Link to={`/calls/${call.id}`} style={{ color: 'var(--blue-300)', textDecoration: 'none' }}>
                          {call.id}
                        </Link>
                      </td>
                      <td>
                        <span className={`status-badge ${call.status.toLowerCase()}`}>
                          {call.status}
                        </span>
                      </td>
                      <td>{formatDate(call.created_at)}</td>
                      <td style={{ maxWidth: 260 }}>
                        <code
                          style={{
                            fontSize: '0.85rem',
                            background: 'rgba(26, 47, 74, 0.7)',
                            padding: '0.35rem 0.6rem',
                            borderRadius: '6px',
                            border: '1px solid rgba(66, 153, 225, 0.3)',
                            color: 'var(--text-secondary)',
                            fontFamily: 'SFMono-Regular, Menlo, Monaco, Consolas, \"Liberation Mono\", \"Courier New\", monospace',
                            display: 'inline-block',
                            maxWidth: '100%',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          }}
                          title={call.audio_object_key}
                        >
                          {call.audio_object_key}
                        </code>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="empty-state">
                <Icon name="phone" size={48} color="var(--text-muted)" />
                <p>No calls yet. Upload your first call to get started.</p>
              </div>
            )}
          </div>

          {hasMoreCalls && (
            <div style={{ textAlign: 'center', marginTop: '1.5rem' }}>
              <button
                className="btn-icon-secondary"
                onClick={loadMoreCalls}
                disabled={loadingMoreCalls}
              >
                {loadingMoreCalls ? (
                  <>
                    <Icon name="loader" size={18} className="icon-spin" />
                    <span style={{ marginLeft: '0.35rem' }}>Loading More...</span>
                  </>
                ) : (
                  <>
                    <Icon
                      name="trendingUp"
                      size={18}
                      className="icon-spin-on-hover"
                      style={{ transform: 'rotate(90deg)' }}
                    />
                    <span style={{ marginLeft: '0.35rem' }}>Load More</span>
                  </>
                )}
              </button>
            </div>
          )}
          {!hasMoreCalls && calls.length > 0 && (
            <p
              style={{
                textAlign: 'center',
                marginTop: '1.5rem',
                color: 'var(--text-muted)',
              }}
            >
              No more calls to load.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;


