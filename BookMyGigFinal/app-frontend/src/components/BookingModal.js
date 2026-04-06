"use client";
import { useState, useEffect } from "react";
import { fetchApi } from "@/lib/api";
import { X, Calendar, MapPin, Users, DollarSign, Loader2, CheckCircle2 } from "lucide-react";

export default function BookingModal({ musician, isOpen, onClose }) {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [events, setEvents] = useState([]);
  const [showNewEventForm, setShowNewEventForm] = useState(false);

  const [bookingData, setBookingData] = useState({
    event_id: "",
    duration: 3,
    price_charged: musician?.base_price || 0
  });

  const [newEvent, setNewEvent] = useState({
    city: musician?.location || "London",
    date_time: new Date(Date.now() + 86400000 * 7).toISOString().slice(0, 16),
    expected_pax: 100,
    event_type: "Private Party",
    budget: (musician?.base_price || 0) * 1.5
  });

  useEffect(() => {
    if (isOpen) {
      fetchApi('/events/me')
        .then(res => {
          setEvents(res);
          if (res.length > 0) {
            setBookingData(prev => ({ ...prev, event_id: res[0].event_id }));
          } else {
            setShowNewEventForm(true);
          }
        })
        .catch(console.error);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleCreateBooking = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      let finalEventId = bookingData.event_id;

      if (showNewEventForm) {
        const createdEvent = await fetchApi('/events', {
          method: 'POST',
          body: JSON.stringify(newEvent)
        });
        finalEventId = createdEvent.event_id;
      }

      await fetchApi('/bookings', {
        method: 'POST',
        body: JSON.stringify({
          ...bookingData,
          event_id: finalEventId,
          musician_id: musician.musician_id
        })
      });

      setSuccess(true);
      setTimeout(() => {
        onClose();
        setSuccess(false);
      }, 2000);
    } catch (err) {
      setError(err.message || "Failed to create booking");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(8px)', padding: '20px' }}>
      <div className="glass-card animate-fade-in" style={{ width: '100%', maxWidth: '500px', position: 'relative', overflow: 'hidden' }}>
        
        {success ? (
          <div style={{ textAlign: 'center', padding: '60px 20px' }}>
            <div style={{ background: 'rgba(34, 197, 94, 0.1)', width: '80px', height: '80px', borderRadius: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px' }}>
              <CheckCircle2 size={48} color="var(--success)" className="animate-bounce" />
            </div>
            <h2 style={{ fontSize: '24px', fontWeight: 'bold', marginBottom: '8px' }}>Booking Confirmed!</h2>
            <p className="text-muted">Your session with {musician.name} is now locked in.</p>
          </div>
        ) : (
          <>
            <button onClick={onClose} style={{ position: 'absolute', top: '16px', right: '16px', background: 'transparent', border: 'none', color: 'gray', cursor: 'pointer' }}>
              <X size={24} />
            </button>

            <h2 style={{ fontSize: '22px', fontWeight: 'bold', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              Book {musician.name}
            </h2>

            <form onSubmit={handleCreateBooking}>
              
              <div style={{ marginBottom: '20px' }}>
                <label className="form-label">Choose Event</label>
                {events.length > 0 && !showNewEventForm ? (
                  <div style={{ display: 'flex', gap: '10px' }}>
                    <select 
                      className="form-input" 
                      style={{ flex: 1 }}
                      value={bookingData.event_id}
                      onChange={e => setBookingData({...bookingData, event_id: e.target.value})}
                    >
                      {events.map(e => <option key={e.event_id} value={e.event_id}>{e.event_type} - {e.city}</option>)}
                    </select>
                    <button type="button" onClick={() => setShowNewEventForm(true)} className="btn btn-outline" style={{ padding: '8px 12px', fontSize: '12px' }}>New</button>
                  </div>
                ) : (
                  <div className="glass-card" style={{ padding: '16px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
                    <p style={{ fontSize: '13px', fontWeight: 'bold', marginBottom: '12px', color: 'var(--primary)' }}>Create Quick Event</p>
                    <div className="grid grid-cols-2" style={{ gap: '12px' }}>
                      <input type="text" placeholder="City" className="form-input" value={newEvent.city} onChange={e => setNewEvent({...newEvent, city: e.target.value})} />
                      <input type="text" placeholder="Type (e.g. Wedding)" className="form-input" value={newEvent.event_type} onChange={e => setNewEvent({...newEvent, event_type: e.target.value})} />
                      <input type="number" placeholder="Budget" className="form-input" value={newEvent.budget} onChange={e => setNewEvent({...newEvent, budget: Number(e.target.value)})} />
                      <input type="datetime-local" className="form-input" value={newEvent.date_time} onChange={e => setNewEvent({...newEvent, date_time: e.target.value})} />
                    </div>
                    {events.length > 0 && (
                        <button type="button" onClick={() => setShowNewEventForm(false)} style={{ background: 'transparent', border: 'none', color: 'var(--primary)', fontSize: '12px', marginTop: '10px', cursor: 'pointer' }}>Cancel & Use Existing</button>
                    )}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2" style={{ gap: '16px', marginBottom: '24px' }}>
                <div className="form-group">
                  <label className="form-label">Duration (Hours)</label>
                  <input type="number" className="form-input" value={bookingData.duration} onChange={e => setBookingData({...bookingData, duration: Number(e.target.value)})} />
                </div>
                <div className="form-group">
                  <label className="form-label">Price (£)</label>
                  <input type="number" className="form-input" value={bookingData.price_charged} onChange={e => setBookingData({...bookingData, price_charged: Number(e.target.value)})} />
                </div>
              </div>

              {error && <p style={{ color: 'var(--danger)', fontSize: '13px', marginBottom: '16px' }}>{error}</p>}

              <button disabled={loading} type="submit" className="btn btn-primary" style={{ width: '100%', padding: '14px' }}>
                {loading ? <Loader2 className="animate-spin" /> : "Confirm Booking"}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  );
}
