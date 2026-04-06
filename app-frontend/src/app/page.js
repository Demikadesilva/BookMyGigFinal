import Link from "next/link";
import { Brain, Music, ShieldCheck, Zap } from "lucide-react";

export default function Home() {
  return (
    <div className="container" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', padding: '40px 24px' }}>
      
      {/* Header */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '80px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ background: 'linear-gradient(135deg, var(--primary), var(--secondary))', padding: '8px', borderRadius: '12px' }}>
            <Music color="white" size={28} />
          </div>
          <h1 style={{ fontSize: '24px', fontWeight: 'bold' }}>BookMy<span className="text-gradient">Gig</span></h1>
        </div>
        <div style={{ display: 'flex', gap: '16px' }}>
          <Link href="/login" className="btn btn-outline" style={{ padding: '8px 24px' }}>Sign In</Link>
          <Link href="/register" className="btn btn-primary" style={{ padding: '8px 24px' }}>Create Account</Link>
        </div>
      </header>

      {/* Hero Section */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', maxWidth: '800px', margin: '0 auto' }}>
        <div className="badge badge-primary animate-fade-in" style={{ marginBottom: '24px' }}>
          <Brain size={16} /> <span style={{ marginLeft: '8px' }}>Powered by 5 Machine Learning Models</span>
        </div>
        
        <h2 className="animate-fade-in" style={{ fontSize: '56px', fontWeight: '800', lineHeight: '1.2', marginBottom: '24px', animationDelay: '0.1s' }}>
          The Intelligent Way to <br/>
          <span className="text-gradient">Book Live Music</span>
        </h2>
        
        <p className="text-muted animate-fade-in" style={{ fontSize: '20px', marginBottom: '40px', lineHeight: '1.6', animationDelay: '0.2s' }}>
          Connect with top UK talent. Get fair AI dynamic pricing, personalised hybrid recommendations, and 100% verified authentic reviews.
        </p>
        
        <div className="animate-fade-in" style={{ display: 'flex', gap: '16px', animationDelay: '0.3s' }}>
          <Link href="/dashboard" className="btn btn-primary" style={{ padding: '16px 32px', fontSize: '16px' }}>Go to Dashboard</Link>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-3 animate-fade-in" style={{ marginTop: '80px', animationDelay: '0.4s', textAlign: 'left' }}>
          
          <div className="glass-card">
            <div style={{ background: 'rgba(124, 58, 237, 0.1)', width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '20px', color: '#a78bfa' }}>
              <Zap size={24} />
            </div>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '12px' }}>Dynamic Pricing</h3>
            <p className="text-muted" style={{ fontSize: '14px' }}>Our LightGBM model calculates fair booking prices in real-time based on expected attendance, duration, and market demand.</p>
          </div>

          <div className="glass-card">
            <div style={{ background: 'rgba(59, 130, 246, 0.1)', width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '20px', color: '#60a5fa' }}>
              <Brain size={24} />
            </div>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '12px' }}>Hybrid Recommendations</h3>
            <p className="text-muted" style={{ fontSize: '14px' }}>Combines Collaborative filtering (SVD) with Content-Based TF-IDF to find the perfect musician for your exact event needs.</p>
          </div>

          <div className="glass-card">
            <div style={{ background: 'rgba(16, 185, 129, 0.1)', width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '20px', color: '#34d399' }}>
              <ShieldCheck size={24} />
            </div>
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '12px' }}>Verified Authentic</h3>
            <p className="text-muted" style={{ fontSize: '14px' }}>We use DistilBERT NLP sentiment analysis and Isolation Forest anomaly detection to automatically flag fake or anomalous reviews.</p>
          </div>

        </div>
      </main>

    </div>
  );
}
