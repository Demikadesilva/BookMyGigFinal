"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { fetchApi } from "@/lib/api";

export default function Login() {
  const router = useRouter();
  const [formData, setFormData] = useState({ email: "", password: "" });
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetchApi("/auth/login", {
        method: "POST",
        body: JSON.stringify(formData),
      });

      // Save token and user details to localStorage
      localStorage.setItem("token", res.access_token);
      localStorage.setItem("user", JSON.stringify(res.user));

      router.push("/dashboard");
    } catch (err) {
      setError(err.message || "Invalid credentials. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: 'var(--bg-primary)' }}>
      <div className="glass-card" style={{ width: '100%', maxWidth: '400px', padding: '40px' }}>
        <h2 style={{ fontSize: '28px', fontWeight: 'bold', marginBottom: '8px', textAlign: 'center' }}>Welcome Back</h2>
        <p className="text-muted" style={{ textAlign: 'center', marginBottom: '32px' }}>Sign in to continue to BookMyGig</p>

        {error && (
          <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: '8px', marginBottom: '20px', fontSize: '14px' }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: 'var(--text-secondary)' }}>Email</label>
            <input 
              type="email" 
              required
              className="glass-card"
              style={{ width: '100%', padding: '12px 16px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: 'white' }}
              value={formData.email} 
              onChange={e => setFormData({ ...formData, email: e.target.value })} 
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '14px', color: 'var(--text-secondary)' }}>Password</label>
            <input 
              type="password" 
              required
              className="glass-card"
              style={{ width: '100%', padding: '12px 16px', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: 'white' }}
              value={formData.password} 
              onChange={e => setFormData({ ...formData, password: e.target.value })} 
            />
          </div>
          <button 
            type="submit" 
            className="btn btn-primary" 
            style={{ width: '100%', padding: '14px', marginTop: '10px' }}
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div style={{ marginTop: '32px', paddingTop: '32px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
          <p className="text-muted" style={{ fontSize: '11px', textAlign: 'center', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '1px' }}>Quick Demo Access</p>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button 
              onClick={() => setFormData({ email: "musician@demo.com", password: "password123" })}
              className="btn btn-outline" 
              style={{ flex: 1, fontSize: '12px', padding: '8px' }}
            >
              As Musician
            </button>
            <button 
              onClick={() => setFormData({ email: "client@demo.com", password: "password123" })}
              className="btn btn-outline" 
              style={{ flex: 1, fontSize: '12px', padding: '8px' }}
            >
              As Client
            </button>
          </div>
        </div>

        <p style={{ textAlign: 'center', marginTop: '24px', fontSize: '14px', color: 'var(--text-secondary)' }}>
          Don't have an account? <Link href="/register" style={{ color: 'var(--primary)' }}>Create one</Link>
        </p>
      </div>
    </div>
  );
}
