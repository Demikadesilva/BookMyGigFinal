"use client";
import { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { fetchApi } from "@/lib/api";
import { Loader2, Star, MapPin, BadgePoundSterling, ShieldCheck } from "lucide-react";
import { useParams } from "next/navigation";
import BookingModal from "@/components/BookingModal";

export default function MusicianProfile() {
  const { id } = useParams();
  const [musician, setMusician] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [isBookingModalOpen, setIsBookingModalOpen] = useState(false);

  useEffect(() => {
    Promise.all([
      fetchApi(`/musicians/${id}`),
      fetchApi(`/musicians/${id}/reviews`)
    ]).then(([m, r]) => {
      setMusician(m);
      setReviews(r || []);
    }).catch(err => {
      setError(err.message);
    }).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <AppLayout><div style={{display:'flex',justifyContent:'center',padding:'100px'}}><Loader2 className="animate-spin text-primary" size={32} /></div></AppLayout>;
  if (error) return <AppLayout><div style={{padding:'20px', color:'var(--danger)'}}>{error}</div></AppLayout>;

  return (
    <AppLayout>
      <div style={{ padding: '20px', maxWidth: '1000px', margin: '0 auto' }}>
        
        {/* Profile Header */}
        <div className="glass-card animate-fade-in" style={{ marginBottom: '40px', display: 'flex', gap: '32px' }}>
          <div style={{ width: '120px', height: '120px', borderRadius: '60px', background: 'linear-gradient(135deg, var(--primary), var(--secondary))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '48px', fontWeight: 'bold' }}>
            {musician.name.charAt(0)}
          </div>
          <div style={{ flex: 1 }}>
            <div className="badge badge-primary" style={{ marginBottom: '8px' }}>{musician.musician_type}</div>
            <h1 style={{ fontSize: '32px', fontWeight: 'bold' }}>{musician.name}</h1>
            <p className="text-muted" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
              <MapPin size={16} /> {musician.location}
            </p>
            <div style={{ display: 'flex', gap: '24px' }}>
              <div>
                <div className="text-muted" style={{ fontSize: '12px', textTransform: 'uppercase' }}>Average Rating</div>
                <div style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--warning)' }}>
                  ★ {musician.avg_rating || 'N/A'} <span style={{fontSize:'12px',color:'gray'}}>({reviews.length} reviews)</span>
                </div>
              </div>
              <div>
                <div className="text-muted" style={{ fontSize: '12px', textTransform: 'uppercase' }}>Bookings</div>
                <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{musician.booking_count}</div>
              </div>
              <div>
                <div className="text-muted" style={{ fontSize: '12px', textTransform: 'uppercase' }}>Experience</div>
                <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{musician.years_experience} Years</div>
              </div>
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div className="text-muted" style={{ fontSize: '12px', textTransform: 'uppercase' }}>Base Price</div>
            <div style={{ fontSize: '32px', fontWeight: 'bold', color: 'var(--success)' }}>£{musician.base_price}</div>
            <button onClick={() => setIsBookingModalOpen(true)} className="btn btn-primary" style={{ marginTop: '16px', width: '100%' }}>Book Now</button>
          </div>
        </div>

        {/* Reviews Section */}
        <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '24px' }}>Verified Reviews</h2>
        
        {reviews.filter(r => !r.is_anomaly).length === 0 ? (
          <p className="text-muted">No verified reviews yet.</p>
        ) : (
          <div className="grid grid-cols-1" style={{ gap: '20px' }}>
            {reviews.filter(r => !r.is_anomaly).map(r => (
              <div key={r.review_id} className="glass-card animate-fade-in" style={{ padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <div style={{ color: 'var(--warning)', letterSpacing: '2px' }}>
                    {'★'.repeat(r.rating)}{'☆'.repeat(5 - r.rating)}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    {r.sentiment_label === 'POSITIVE' && <span className="badge badge-success">Positive</span>}
                    {r.sentiment_label === 'NEGATIVE' && <span className="badge badge-danger">Negative</span>}
                    {r.sentiment_label === 'NEUTRAL' && <span className="badge badge-warning">Neutral</span>}
                    <span className="text-muted" style={{ fontSize: '12px' }}>{new Date(r.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
                <p style={{ lineHeight: '1.6' }}>"{r.review_text}"</p>
                
                <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid rgba(255,255,255,0.05)', display: 'flex', gap: '16px' }}>
                  <span className="badge" style={{ background: 'rgba(255,255,255,0.05)', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <ShieldCheck size={12} color="var(--success)" /> NLP Validated
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}

        {musician && (
            <BookingModal
                musician={musician}
                isOpen={isBookingModalOpen}
                onClose={() => setIsBookingModalOpen(false)}
            />
        )}

      </div>
    </AppLayout>
  );
}
