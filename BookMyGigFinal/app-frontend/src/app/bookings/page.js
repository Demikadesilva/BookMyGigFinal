"use client";
import { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { fetchApi } from "@/lib/api";
import { Loader2, Calendar, MapPin, Star, MessageSquare, BadgeCheck, ShieldAlert } from "lucide-react";
import ReviewModal from "@/components/ReviewModal";

export default function Bookings() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedBooking, setSelectedBooking] = useState(null);
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);

  const fetchBookings = async () => {
    setLoading(true);
    try {
      const data = await fetchApi("/bookings/me");
      setBookings(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBookings();
  }, []);

  const openReviewModal = (booking) => {
    setSelectedBooking(booking);
    setIsReviewModalOpen(true);
  };

  return (
    <AppLayout>
      <div style={{ padding: '20px', maxWidth: '1200px' }}>
        <header style={{ marginBottom: '40px' }}>
          <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '8px' }}>My Gigs</h1>
          <p className="text-muted">Manage your bookings, track upcoming performances, and provide feedback.</p>
        </header>

        {loading ? (
          <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Loader2 className="animate-spin text-primary" size={32} />
          </div>
        ) : bookings.length === 0 ? (
          <div className="glass-card" style={{ textAlign: 'center', padding: '100px 20px' }}>
            <Calendar size={48} className="text-muted" style={{ margin: '0 auto 24px', opacity: 0.3 }} />
            <h2 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '8px' }}>No bookings found</h2>
            <p className="text-muted">You haven't scheduled any gigs yet.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1" style={{ gap: '24px' }}>
            {bookings.map((b) => (
              <div key={b.booking_id} className="glass-card animate-fade-in" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '24px' }}>
                <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
                  <div style={{ width: '60px', height: '60px', borderRadius: '12px', background: 'rgba(124, 58, 237, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '24px', fontWeight: 'bold', color: 'var(--primary)' }}>
                    {b.musician_name ? b.musician_name.charAt(0) : 'B'}
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '4px' }}>
                      <h3 style={{ fontSize: '18px', fontWeight: 'bold' }}>{b.musician_name}</h3>
                      <span className="badge" style={{ fontSize: '10px' }}>{b.booking_id}</span>
                    </div>
                    <div className="text-muted" style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '13px' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Calendar size={14} /> {b.date_time ? new Date(b.date_time).toLocaleDateString() : 'Date TBD'}</span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><MapPin size={14} /> {b.city}</span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><BadgeCheck size={14} className="text-success" /> {b.event_type}</span>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '32px', alignItems: 'center' }}>
                  <div style={{ textAlign: 'right' }}>
                    <div className="text-muted" style={{ fontSize: '11px', textTransform: 'uppercase' }}>Amount Paid</div>
                    <div style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--success)' }}>£{b.price_charged.toLocaleString()}</div>
                  </div>
                  
                  {b.rating > 0 ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--warning)', background: 'rgba(234, 179, 8, 0.1)', padding: '8px 16px', borderRadius: '8px' }}>
                      <Star size={16} fill="var(--warning)" />
                      <span style={{ fontWeight: 'bold' }}>{b.rating} / 5</span>
                    </div>
                  ) : (
                    <button onClick={() => openReviewModal(b)} className="btn btn-outline" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <MessageSquare size={16} /> Leave Feedback
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {selectedBooking && (
          <ReviewModal 
            booking={selectedBooking}
            isOpen={isReviewModalOpen}
            onClose={() => setIsReviewModalOpen(false)}
            onReviewSubmitted={fetchBookings}
          />
        )}

      </div>
    </AppLayout>
  );
}
