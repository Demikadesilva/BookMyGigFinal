"use client";
import { useState } from "react";
import { fetchApi } from "@/lib/api";
import { X, Star, Loader2, Send, ShieldAlert, CheckCircle2 } from "lucide-react";

export default function ReviewModal({ booking, isOpen, onClose, onReviewSubmitted }) {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [rating, setRating] = useState(5);
  const [text, setText] = useState("");
  const [aiAnalysis, setAiAnalysis] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const result = await fetchApi('/reviews', {
        method: 'POST',
        body: JSON.stringify({
          booking_id: booking.booking_id,
          review_text: text,
          rating: rating
        })
      });

      setAiAnalysis(result);
      setSuccess(true);
      
      if (onReviewSubmitted) onReviewSubmitted();

      setTimeout(() => {
        onClose();
        setSuccess(false);
        setAiAnalysis(null);
        setText("");
      }, 5000);
    } catch (err) {
      setError(err.message || "Failed to submit review");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 3000, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(8px)', padding: '20px' }}>
      <div className="glass-card animate-fade-in" style={{ width: '100%', maxWidth: '500px', position: 'relative' }}>
        
        <button onClick={onClose} style={{ position: 'absolute', top: '16px', right: '16px', background: 'transparent', border: 'none', color: 'gray', cursor: 'pointer' }}>
          <X size={24} />
        </button>

        {!success ? (
          <>
            <h2 style={{ fontSize: '22px', fontWeight: 'bold', marginBottom: '8px' }}>Rate your Experience</h2>
            <p className="text-muted" style={{ marginBottom: '24px' }}>Submit a review for {booking.musician_name}.</p>

            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: '24px', textAlign: 'center' }}>
                <div style={{ display: 'flex', justifyContent: 'center', gap: '8px' }}>
                  {[1, 2, 3, 4, 5].map(num => (
                    <Star 
                      key={num} 
                      size={32} 
                      style={{ cursor: 'pointer', fill: num <= rating ? 'var(--warning)' : 'none', color: num <= rating ? 'var(--warning)' : 'gray' }} 
                      onClick={() => setRating(num)}
                    />
                  ))}
                </div>
              </div>

              <div className="form-group" style={{ marginBottom: '24px' }}>
                <label className="form-label">Review Details</label>
                <textarea 
                  className="form-input" 
                  rows={4} 
                  placeholder="How was the performance? Any specific highlights?"
                  value={text}
                  onChange={e => setText(e.target.value)}
                  required
                />
                <p style={{ fontSize: '11px', color: 'gray', marginTop: '8px' }}>Note: Our AI system automatically validates all reviews for sentiment and authenticity.</p>
              </div>

              {error && <p style={{ color: 'var(--danger)', fontSize: '13px', marginBottom: '16px' }}>{error}</p>}

              <button disabled={loading || !text} type="submit" className="btn btn-primary" style={{ width: '100%', padding: '14px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
                {loading ? <Loader2 className="animate-spin" /> : <><Send size={18} /> Submit Review</>}
              </button>
            </form>
          </>
        ) : (
          <div style={{ padding: '20px', textAlign: 'center' }}>
            <div style={{ background: 'rgba(34, 197, 94, 0.1)', width: '60px', height: '60px', borderRadius: '30px', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 20px' }}>
              <CheckCircle2 size={32} color="var(--success)" />
            </div>
            <h2 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '16px' }}>Review Processed!</h2>
            
            {aiAnalysis && (
              <div style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '12px', padding: '20px', textAlign: 'left', border: aiAnalysis.is_anomaly ? '1px solid var(--danger)' : '1px solid var(--success)' }}>
                <h3 style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '1px' }}>AI Engine Output:</h3>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                    <span className="text-muted">Sentiment Detected:</span>
                    <span style={{ fontWeight: 'bold', color: aiAnalysis.sentiment_label === 'POSITIVE' ? 'var(--success)' : 'inherit' }}>{aiAnalysis.sentiment_label}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                    <span className="text-muted">Authenticity Check:</span>
                    {aiAnalysis.is_anomaly ? (
                      <span style={{ color: 'var(--danger)', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <ShieldAlert size={14} /> FLAGGED AS ANOMALY
                      </span>
                    ) : (
                      <span style={{ color: 'var(--success)', fontWeight: 'bold' }}>VERIFIED AUTHENTIC</span>
                    )}
                  </div>
                </div>

                {aiAnalysis.is_anomaly && (
                  <p style={{ marginTop: '16px', fontSize: '11px', color: 'var(--danger)', fontStyle: 'italic' }}>
                    Warning: This review has been flagged by the Isolation Forest model and may be hidden or moderated.
                  </p>
                )}
              </div>
            )}
            
            <p className="text-muted" style={{ marginTop: '24px', fontSize: '12px' }}>Closing in a few seconds...</p>
          </div>
        )}
      </div>
    </div>
  );
}
