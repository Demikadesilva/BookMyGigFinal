"use client"
import { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { fetchApi } from "@/lib/api";
import { Loader2, ShieldCheck, AlertTriangle, ShieldAlert } from "lucide-react";

export default function AIAnomaly() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const data = await fetchApi("/ai/anomaly-stats");
      setStats(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getSentimentBadge = (label) => {
    switch (label) {
      case "POSITIVE": return <span className="badge badge-success">Positive</span>;
      case "NEGATIVE": return <span className="badge badge-danger">Negative</span>;
      default: return <span className="badge badge-warning">Neutral</span>;
    }
  };

  return (
    <AppLayout>
      <div style={{ padding: '20px', maxWidth: '1200px' }}>
        
        <div style={{ marginBottom: '40px' }}>
          <div className="badge badge-primary animate-fade-in" style={{ marginBottom: '16px' }}>
            <ShieldCheck size={14} style={{ marginRight: '6px' }}/> NLP Sentiment & Isolation Forest
          </div>
          <h1 style={{ fontSize: '32px', fontWeight: 'bold' }}>Review Moderation Engine</h1>
          <p className="text-muted">Automatically flagged reviews due to high sentiment-rating discrepancy or anomalous text patterns.</p>
        </div>

        {error ? (
          <div style={{ padding: '20px', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: '12px' }}>
            {error}
          </div>
        ) : loading || !stats ? (
          <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Loader2 className="animate-spin text-primary" size={32} />
          </div>
        ) : (
          <div className="animate-fade-in">
            {/* Top Level Stats */}
            <div className="grid grid-cols-4" style={{ marginBottom: '40px' }}>
              <div className="glass-card">
                <h3 className="text-muted" style={{ fontSize: '14px', marginBottom: '8px' }}>Total Reviews Handled</h3>
                <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{stats.total_reviews}</div>
              </div>
              <div className="glass-card" style={{ borderColor: 'var(--warning)', background: 'rgba(245, 158, 11, 0.05)' }}>
                <h3 className="text-muted" style={{ fontSize: '14px', marginBottom: '8px', color: 'rgba(255,255,255,0.7)' }}>Anomalies Flagged</h3>
                <div style={{ fontSize: '32px', fontWeight: 'bold', color: 'var(--warning)' }}>{stats.flagged_anomalies}</div>
              </div>
              <div className="glass-card" style={{ borderColor: 'var(--danger)', background: 'rgba(239, 68, 68, 0.05)' }}>
                <h3 className="text-muted" style={{ fontSize: '14px', marginBottom: '8px', color: 'rgba(255,255,255,0.7)' }}>Platform Fake Review Rate</h3>
                <div style={{ fontSize: '32px', fontWeight: 'bold', color: 'var(--danger)' }}>{stats.flagged_pct}%</div>
              </div>
              <div className="glass-card">
                <h3 className="text-muted" style={{ fontSize: '14px', marginBottom: '8px' }}>Average Anomaly Score</h3>
                <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{stats.avg_anomaly_score.toFixed(2)}</div>
              </div>
            </div>

            {/* List of anomalies */}
            <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertTriangle size={20} color="var(--warning)" /> Recently Flagged Reviews
            </h2>

            <div className="grid grid-cols-2" style={{ gap: '24px' }}>
              {stats.recent_anomalies.map(review => (
                <div key={review.review_id} className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                    <div>
                      <div style={{ display: 'flex', gap: '4px', marginBottom: '8px' }}>
                        {[1,2,3,4,5].map(star => (
                          <span key={star} style={{ color: star <= review.rating ? 'var(--warning)' : 'rgba(255,255,255,0.2)' }}>★</span>
                        ))}
                      </div>
                      <span className="text-muted" style={{ fontSize: '12px' }}>Booking ID: {review.booking_id} • {review.created_at}</span>
                    </div>
                    {getSentimentBadge(review.sentiment_label)}
                  </div>

                  <p style={{ fontSize: '15px', lineHeight: '1.6', marginBottom: '24px', flex: 1, fontStyle: 'italic' }}>
                    "{review.review_text}"
                  </p>

                  <div style={{ background: 'rgba(239, 68, 68, 0.1)', padding: '12px', borderRadius: '8px', borderLeft: '3px solid var(--danger)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', fontWeight: 'bold', color: 'var(--danger)' }}>
                      <ShieldAlert size={16} /> Fake Review Flag
                    </div>
                    <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.7)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span>Isolation Forest Score:</span>
                        <span>{review.anomaly_score.toFixed(4)}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                        <span>NLP Sentiment Score:</span>
                        <span>{review.sentiment_score.toFixed(3)}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#fff' }}>
                        <span>Discrepancy:</span>
                        <span>User rated {review.rating}/5 but NLP detected {review.sentiment_label.toLowerCase()} text.</span>
                      </div>
                    </div>
                  </div>

                </div>
              ))}
            </div>

            {stats.recent_anomalies.length === 0 && (
              <div className="glass-card" style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--success)' }}>
                <ShieldCheck size={48} style={{ margin: '0 auto 16px' }} />
                <h3 style={{ fontSize: '20px', fontWeight: 'bold' }}>Platform is Clean</h3>
                <p>No anomalous reviews actively detected in the recent batch.</p>
              </div>
            )}

          </div>
        )}
      </div>
    </AppLayout>
  );
}
