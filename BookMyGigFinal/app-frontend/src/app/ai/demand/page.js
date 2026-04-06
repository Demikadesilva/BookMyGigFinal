"use client"
import { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { fetchApi } from "@/lib/api";
import { Loader2, TrendingUp, Calendar as CalendarIcon } from "lucide-react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart
} from "recharts";

export default function AIDemandForecast() {
  const [loading, setLoading] = useState(true);
  const [cities, setCities] = useState([]);
  const [selectedCity, setSelectedCity] = useState("All");
  const [demandData, setDemandData] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchCities();
    fetchDemand("");
  }, []);

  const fetchCities = async () => {
    try {
      const data = await fetchApi("/ai/demand/cities");
      setCities(data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchDemand = async (city) => {
    setLoading(true);
    setError("");
    try {
      const qs = city && city !== "All" ? `?city=${encodeURIComponent(city)}` : "";
      const data = await fetchApi(`/ai/demand${qs}`);
      setDemandData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCityChange = (e) => {
    const city = e.target.value;
    setSelectedCity(city);
    fetchDemand(city);
  };

  return (
    <AppLayout>
      <div style={{ padding: '20px', maxWidth: '1200px' }}>
        
        <div style={{ marginBottom: '40px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div className="badge badge-primary animate-fade-in" style={{ marginBottom: '16px' }}>
              <TrendingUp size={14} style={{ marginRight: '6px' }}/> LightGBM Time-Series
            </div>
            <h1 style={{ fontSize: '32px', fontWeight: 'bold' }}>Demand Forecasting</h1>
            <p className="text-muted">Analyze weekly booking demand patterns and seasonality across locations.</p>
          </div>
          
          <div className="glass-card animate-fade-in" style={{ padding: '16px 24px' }}>
            <label className="text-muted" style={{ fontSize: '13px', display: 'block', marginBottom: '8px' }}>Location Filter</label>
            <select value={selectedCity} onChange={handleCityChange} className="form-input" style={{ width: '250px' }}>
              <option value="All">All Cities (National)</option>
              {cities.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        </div>

        {error ? (
          <div style={{ padding: '20px', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: '12px' }}>
            {error}
          </div>
        ) : loading ? (
          <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }} className="glass-card">
            <Loader2 className="animate-spin text-primary" size={32} />
          </div>
        ) : (
          <div className="grid grid-cols-1" style={{ gap: '24px' }}>
            
            {/* Main Chart */}
            <div className="glass-card animate-fade-in" style={{ height: '500px', display: 'flex', flexDirection: 'column' }}>
              <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CalendarIcon size={18} /> Weekly Booking Volume (Last 12 Months)
              </h2>
              
              <div style={{ flex: 1, width: '100%' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={demandData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorDemand" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                    <XAxis 
                      dataKey="week" 
                      tickFormatter={(val) => {
                        const d = new Date(val);
                        return `${d.toLocaleString('default', { month: 'short' })} ${d.getDate()}`;
                      }}
                      stroke="rgba(255,255,255,0.3)"
                      tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 12 }}
                      minTickGap={30}
                    />
                    <YAxis 
                      stroke="rgba(255,255,255,0.3)"
                      tick={{ fill: 'rgba(255,255,255,0.5)', fontSize: 12 }}
                    />
                    <Tooltip 
                      contentStyle={{ background: 'rgba(15, 16, 21, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                      itemStyle={{ color: '#fff' }}
                      labelFormatter={(val) => new Date(val).toLocaleDateString()}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="demand" 
                      stroke="var(--primary)" 
                      strokeWidth={3}
                      fillOpacity={1} 
                      fill="url(#colorDemand)" 
                      name="Total Bookings"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Sub Charts */}
            <div className="grid grid-cols-2 animate-fade-in" style={{ animationDelay: '0.2s' }}>
              <div className="glass-card" style={{ height: '300px', display: 'flex', flexDirection: 'column' }}>
                <h2 style={{ fontSize: '16px', fontWeight: '500', marginBottom: '16px' }}>Average Booking Price Trend</h2>
                <div style={{ flex: 1, width: '100%' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={demandData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                      <XAxis dataKey="week" hide />
                      <YAxis domain={['auto', 'auto']} tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }} />
                      <Tooltip contentStyle={{ background: '#111', border: 'none', borderRadius: '4px' }} />
                      <Line type="monotone" dataKey="avg_price" stroke="var(--success)" strokeWidth={2} dot={false} name="Avg Price (£)" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="glass-card" style={{ height: '300px', display: 'flex', flexDirection: 'column' }}>
                <h2 style={{ fontSize: '16px', fontWeight: '500', marginBottom: '16px' }}>Customer Satisfaction (Avg Rating)</h2>
                <div style={{ flex: 1, width: '100%' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={demandData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                      <XAxis dataKey="week" hide />
                      <YAxis domain={[3.5, 5]} tick={{ fill: 'rgba(255,255,255,0.4)', fontSize: 11 }} />
                      <Tooltip contentStyle={{ background: '#111', border: 'none', borderRadius: '4px' }} />
                      <Line type="step" dataKey="avg_rating" stroke="var(--warning)" strokeWidth={2} dot={false} name="Avg Rating" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

          </div>
        )}
      </div>
    </AppLayout>
  );
}
