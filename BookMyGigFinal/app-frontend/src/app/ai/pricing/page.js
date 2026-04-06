"use client"
import { useState } from "react";
import AppLayout from "@/components/AppLayout";
import { fetchApi } from "@/lib/api";
import { Loader2, Calculator, Zap, CheckCircle2 } from "lucide-react";

export default function AIPricing() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const [formData, setFormData] = useState({
    event_type: "Wedding",
    city: "London",
    musician_type: "Band",
    expected_pax: 150,
    duration: 4,
    years_experience: 10,
    base_price: 1200
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    const updatedValue = ["expected_pax", "duration", "years_experience", "base_price"].includes(name) 
      ? Number(value) 
      : value;
    setFormData(prev => ({ ...prev, [name]: updatedValue }));
  };

  const handlePredict = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await fetchApi("/ai/price-estimate", {
        method: "POST",
        body: JSON.stringify(formData)
      });
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppLayout>
      <div style={{ padding: '20px', maxWidth: '1000px' }}>
        <div style={{ marginBottom: '40px' }}>
          <div className="badge badge-primary animate-fade-in" style={{ marginBottom: '16px' }}>
            <Zap size={14} style={{ marginRight: '6px' }}/> Powered by LightGBM Regressor
          </div>
          <h1 style={{ fontSize: '32px', fontWeight: 'bold' }}>Dynamic AI Pricing tool</h1>
          <p className="text-muted">Generate fair and accurate real-time market prices for any booking scenario.</p>
        </div>

        <div className="grid grid-cols-2" style={{ gap: '40px' }}>
          <div className="glass-card animate-fade-in">
            <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Calculator size={20} /> Input Parameters
            </h2>

            <form onSubmit={handlePredict}>
              <div className="grid grid-cols-2" style={{ gap: '16px', marginBottom: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Event Type</label>
                  <select name="event_type" value={formData.event_type} onChange={handleChange} className="form-input">
                    <option value="Wedding">Wedding</option>
                    <option value="Corporate">Corporate</option>
                    <option value="Private Party">Private Party</option>
                    <option value="Festival">Festival</option>
                    <option value="Pub/Club">Pub/Club</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">City</label>
                  <select name="city" value={formData.city} onChange={handleChange} className="form-input">
                    <option value="London">London</option>
                    <option value="Manchester">Manchester</option>
                    <option value="Bristol">Bristol</option>
                    <option value="Glasgow">Glasgow</option>
                    <option value="Birmingham">Birmingham</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2" style={{ gap: '16px', marginBottom: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Musician Type</label>
                  <select name="musician_type" value={formData.musician_type} onChange={handleChange} className="form-input">
                    <option value="Band">Band</option>
                    <option value="Solo">Solo</option>
                    <option value="Duo">Duo</option>
                    <option value="DJ">DJ</option>
                    <option value="Orchestra">Orchestra</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Musician Experience (Years)</label>
                  <input type="number" name="years_experience" value={formData.years_experience} onChange={handleChange} className="form-input" min="0" />
                </div>
              </div>

              <div className="form-group" style={{ marginBottom: '16px' }}>
                <label className="form-label">Musician Base Price (£)</label>
                <input type="number" name="base_price" value={formData.base_price} onChange={handleChange} className="form-input" min="0" step="10" />
              </div>

              <div className="grid grid-cols-2" style={{ gap: '16px', marginBottom: '32px' }}>
                <div className="form-group">
                  <label className="form-label">Expected Pax (Attendees)</label>
                  <input type="number" name="expected_pax" value={formData.expected_pax} onChange={handleChange} className="form-input" min="0" />
                </div>
                <div className="form-group">
                  <label className="form-label">Duration (Hours)</label>
                  <input type="number" name="duration" value={formData.duration} onChange={handleChange} className="form-input" min="1" max="12" />
                </div>
              </div>

              <button type="submit" disabled={loading} className="btn btn-primary" style={{ width: '100%', padding: '14px', fontSize: '16px' }}>
                {loading ? <Loader2 className="animate-spin" /> : "Calculate AI Price Estimate"}
              </button>

              {error && (
                <div style={{ padding: '12px', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: '8px', marginTop: '16px', fontSize: '14px' }}>
                  {error}
                </div>
              )}
            </form>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column' }}>
            {result ? (
              <div className="glass-card animate-fade-in" style={{ borderColor: 'var(--primary)', flex: 1 }}>
                <div style={{ textAlign: 'center', padding: '40px 0', borderBottom: '1px solid var(--border)', marginBottom: '24px' }}>
                  <p className="text-muted" style={{ marginBottom: '12px', fontSize: '14px', textTransform: 'uppercase', letterSpacing: '1px' }}>AI Recommended Price</p>
                  <div style={{ fontSize: '64px', fontWeight: '800', fontFamily: 'monospace' }} className="text-gradient">
                    £{result.estimated_price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                  </div>
                </div>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: '500', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <CheckCircle2 color="var(--success)" size={18} /> Model Information
                  </h3>
                  <div style={{ background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '8px', fontSize: '13px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                      <span className="text-muted">Underlying Architecture:</span>
                      <span style={{ fontWeight: '500' }}>LightGBM Regressor</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                      <span className="text-muted">Total Features Used:</span>
                      <span style={{ fontWeight: '500' }}>10 variables</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span className="text-muted">Baseline Difference:</span>
                      <span style={{ fontWeight: '500', color: result.estimated_price >= formData.base_price ? 'var(--success)' : 'var(--danger)' }}>
                        {result.estimated_price >= formData.base_price ? '+' : ''}
                        {(((result.estimated_price / formData.base_price) - 1) * 100).toFixed(1)}% vs baseline
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="glass-card" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', opacity: 0.5 }}>
                <Calculator size={48} style={{ marginBottom: '16px', opacity: 0.5 }} />
                <p>Run a prediction to see the AI output</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
