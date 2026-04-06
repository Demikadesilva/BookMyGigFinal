"use client"
import AppLayout from "@/components/AppLayout";
import { fetchApi } from "@/lib/api";
import { useEffect, useState } from "react";
import { Calendar, Loader2 } from "lucide-react";

export default function Events() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApi('/events')
      .then(res => setEvents(res))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppLayout>
      <div style={{ padding: '20px', maxWidth: '1000px' }}>
        <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '8px' }}>Events</h1>
        <p className="text-muted" style={{ marginBottom: '32px' }}>Browse the latest events across the platform.</p>

        {loading ? (
           <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
             <Loader2 className="animate-spin text-primary" size={32} />
           </div>
        ) : (
          <div className="grid grid-cols-3">
            {events.map((evt) => (
              <div key={evt.event_id} className="glass-card">
                <Calendar size={24} style={{ color: 'var(--secondary)', marginBottom: '16px' }} />
                <h3 className="text-gradient" style={{ fontSize: '20px', fontWeight: 'bold' }}>{evt.event_type}</h3>
                <p className="text-muted">{evt.city}</p>
                <div style={{ marginTop: '16px', fontSize: '14px' }}>
                  <p><strong>Attendees:</strong> {evt.expected_pax}</p>
                  <p><strong>Budget:</strong> £{evt.budget}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  )
}
