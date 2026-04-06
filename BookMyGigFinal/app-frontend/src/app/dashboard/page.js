"use client";
import AppLayout from "@/components/AppLayout";
import { Users, Calendar, Activity, ShieldCheck, DollarSign, Star, Zap, ArrowRight, Music } from "lucide-react";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { fetchApi } from "@/lib/api";
import Link from "next/link";

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [stats, setStats] = useState({
    total_musicians: 0,
    total_bookings: 0,
    total_events: 0,
    total_reviews: 0,
    avg_price: 0,
    anomaly_rate: 0
  });

  useEffect(() => {
    const token = localStorage.getItem("token");
    const storedUser = localStorage.getItem("user");
    
    if (!token) {
      router.push("/login");
      return;
    }

    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }

    const fetchStats = async () => {
      try {
        const data = await fetchApi("/ai/dashboard-stats");
        setStats(data);
      } catch (err) {
        console.error("Failed to fetch dashboard stats:", err);
      }
    };

    fetchStats();
  }, [router]);

  if (!user) return null;

  const isMusician = user.role === 'musician';

  return (
    <AppLayout>
      <div style={{ padding: '20px' }}>
        <header style={{ marginBottom: '40px' }}>
          <h1 style={{ fontSize: '32px', fontWeight: 'bold', marginBottom: '8px' }}>
            {isMusician ? "Musician Console" : "Client Dashboard"}
          </h1>
          <p className="text-muted">Welcome back, {user.full_name}. Here is the real-time status of your BookMyGig portal.</p>
        </header>

        {/* Global Platform Intelligence (Important for Thesis Showcase) */}
        <section style={{ marginBottom: '48px' }}>
          <h2 style={{ fontSize: '14px', fontWeight: 'bold', textTransform: 'uppercase', color: 'var(--primary)', letterSpacing: '1px', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Zap size={14} /> AI Platform Monitoring
          </h2>
          <div className="grid grid-cols-4">
            <div className="glass-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <h3 className="text-muted" style={{ fontSize: '13px' }}>Current Talent</h3>
                <Users size={18} color="var(--primary)" />
              </div>
              <div style={{ fontSize: '28px', fontWeight: 'bold' }}>{stats.total_musicians}</div>
            </div>

            <div className="glass-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <h3 className="text-muted" style={{ fontSize: '13px' }}>Total Events</h3>
                <Calendar size={18} color="var(--secondary)" />
              </div>
              <div style={{ fontSize: '28px', fontWeight: 'bold' }}>{stats.total_events}</div>
            </div>

            <div className="glass-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <h3 className="text-muted" style={{ fontSize: '13px' }}>Avg Price</h3>
                <DollarSign size={18} color="var(--success)" />
              </div>
              <div style={{ fontSize: '28px', fontWeight: 'bold' }}>£{stats.avg_price.toLocaleString()}</div>
            </div>

            <div className="glass-card" style={{ border: '1px solid rgba(239, 68, 68, 0.2)', background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.02), rgba(239, 68, 68, 0.05))' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <h3 className="text-muted" style={{ fontSize: '13px' }}>AI Anomaly Deflection</h3>
                <ShieldCheck size={18} color="var(--danger)" />
              </div>
              <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--danger)' }}>{stats.anomaly_rate}%</div>
            </div>
          </div>
        </section>

        {/* Role Specific Actions */}
        <div className="grid grid-cols-2" style={{ gap: '32px' }}>
          
          {isMusician ? (
            <>
              <div className="glass-card" style={{ padding: '32px', background: 'var(--bg-secondary)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <h3 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '8px' }}>Are you charging enough?</h3>
                    <p className="text-muted" style={{ fontSize: '14px', marginBottom: '24px' }}>Use our LightGBM pricing model to see your optimal market value based on current UK demand.</p>
                    <Link href="/ai/pricing" className="btn btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                      Open AI Pricing Tool <ArrowRight size={16} />
                    </Link>
                  </div>
                  <div style={{ background: 'rgba(124, 58, 237, 0.1)', padding: '20px', borderRadius: '16px' }}>
                    <DollarSign size={40} color="var(--primary)" />
                  </div>
                </div>
              </div>

              <div className="glass-card" style={{ padding: '32px' }}>
                <h3 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '24px' }}>Reputation Analysis</h3>
                <div style={{ display: 'flex', gap: '24px' }}>
                  <div style={{ flex: 1, textAlign: 'center', padding: '16px', background: 'rgba(255,255,255,0.03)', borderRadius: '12px' }}>
                    <div className="text-muted" style={{ fontSize: '11px', marginBottom: '8px' }}>TRUST SCORE</div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--warning)' }}>4.8 / 5.0</div>
                  </div>
                  <div style={{ flex: 1, textAlign: 'center', padding: '16px', background: 'rgba(255,255,255,0.03)', borderRadius: '12px' }}>
                    <div className="text-muted" style={{ fontSize: '11px', marginBottom: '8px' }}>AI SENTIMENT</div>
                    <div style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--success)' }}>POSITIVE</div>
                  </div>
                </div>
                <Link href="/bookings" style={{ display: 'block', textAlign: 'center', marginTop: '24px', color: 'var(--primary)', fontSize: '14px', textDecoration: 'none' }}>
                  View Detailed Performance Metrics →
                </Link>
              </div>
            </>
          ) : (
            <>
              <div className="glass-card" style={{ padding: '32px', background: 'var(--bg-secondary)', border: '1px solid var(--primary)' }}>
                <h3 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '8px' }}>Need the perfect music?</h3>
                <p className="text-muted" style={{ fontSize: '14px', marginBottom: '24px' }}>Our Hybrid Recommender uses SVD and CBF to match artists to your specific taste and budget.</p>
                <div style={{ display: 'flex', gap: '16px' }}>
                  <Link href="/musicians" className="btn btn-primary">Browse All</Link>
                  <Link href="/ai/recommendations" className="btn btn-outline">AI Matching</Link>
                </div>
              </div>

              <div className="glass-card" style={{ padding: '32px' }}>
                <h3 style={{ fontSize: '20px', fontWeight: 'bold', marginBottom: '16px' }}>Manage Gigs</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
                    <span style={{ fontSize: '14px' }}>Current Events</span>
                    <span className="badge" style={{ background: 'var(--secondary)' }}>{stats.total_events} Active</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: '8px' }}>
                    <span style={{ fontSize: '14px' }}>Bookings</span>
                    <span className="badge">{stats.total_bookings} Total</span>
                  </div>
                  <Link href="/bookings" style={{ marginTop: 'auto', textAlign: 'center', color: 'var(--primary)', fontSize: '14px', textDecoration: 'none' }}>
                    Go to Booking Manager
                  </Link>
                </div>
              </div>
            </>
          )}

        </div>
      </div>
    </AppLayout>
  );
}
