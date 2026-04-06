"use client"
import { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { fetchApi } from "@/lib/api";
import { Loader2, Search, Filter } from "lucide-react";
import Link from "next/link";

export default function Musicians() {
  const [loading, setLoading] = useState(true);
  const [musicians, setMusicians] = useState([]);
  const [filters, setFilters] = useState({ genres: [], locations: [], types: [] });
  const [error, setError] = useState("");

  const [searchParams, setSearchParams] = useState({
    search: "",
    genre: "",
    location: "",
    musician_type: "",
    page: 1,
    page_size: 12
  });

  useEffect(() => {
    fetchFilterOptions();
  }, []);

  useEffect(() => {
    fetchMusicians();
  }, [searchParams]);

  const fetchFilterOptions = async () => {
    try {
      const data = await fetchApi("/musicians/filters");
      setFilters(data);
    } catch (err) {
      console.error(err);
    }
  };

  const fetchMusicians = async () => {
    setLoading(true);
    try {
      const qs = new URLSearchParams();
      Object.entries(searchParams).forEach(([k, v]) => {
        if (v) qs.append(k, v);
      });
      const data = await fetchApi(`/musicians?${qs.toString()}`);
      setMusicians(data.musicians || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleParamChange = (k, v) => {
    setSearchParams(prev => ({ ...prev, [k]: v, page: 1 }));
  };

  return (
    <AppLayout>
      <div style={{ padding: '20px', maxWidth: '1200px' }}>
        
        <div style={{ marginBottom: '40px', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <div>
            <h1 style={{ fontSize: '32px', fontWeight: 'bold' }}>Browse Musicians</h1>
            <p className="text-muted">Explore our full catalog of authentic, verified talent.</p>
          </div>
        </div>

        {/* Filters */}
        <div className="glass-card animate-fade-in" style={{ marginBottom: '40px', padding: '20px' }}>
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
            <Filter size={20} className="text-muted" />
            
            <input 
              type="text" 
              placeholder="Search by name..." 
              value={searchParams.search}
              onChange={(e) => handleParamChange('search', e.target.value)}
              className="form-input" 
              style={{ width: '250px' }}
            />

            <select 
              value={searchParams.genre} 
              onChange={(e) => handleParamChange('genre', e.target.value)}
              className="form-input" 
              style={{ width: '200px' }}
            >
              <option value="">All Genres</option>
              {filters.genres.map(g => <option key={g} value={g}>{g}</option>)}
            </select>

            <select 
              value={searchParams.location} 
              onChange={(e) => handleParamChange('location', e.target.value)}
              className="form-input" 
              style={{ width: '200px' }}
            >
              <option value="">All Locations</option>
              {filters.locations.map(l => <option key={l} value={l}>{l}</option>)}
            </select>

            <select 
              value={searchParams.musician_type} 
              onChange={(e) => handleParamChange('musician_type', e.target.value)}
              className="form-input" 
              style={{ width: '200px' }}
            >
              <option value="">All Types</option>
              {filters.types.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
            
          </div>
        </div>

        {/* Results */}
        {error && <div style={{ color: 'var(--danger)', marginBottom: '20px' }}>{error}</div>}

        {loading ? (
          <div style={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Loader2 className="animate-spin text-primary" size={32} />
          </div>
        ) : (
          <div className="grid grid-cols-4 animate-fade-in">
            {musicians.map(musician => (
              <div key={musician.musician_id} className="glass-card" style={{ display: 'flex', flexDirection: 'column' }}>
                <div className="badge" style={{ background: 'rgba(255,255,255,0.1)', marginBottom: '16px', alignSelf: 'flex-start' }}>
                  {musician.musician_type}
                </div>
                
                <h3 style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '4px' }}>{musician.name}</h3>
                <p className="text-muted" style={{ fontSize: '13px', marginBottom: '16px' }}>{musician.location}</p>
                
                <div style={{ flex: 1, marginBottom: '24px' }}>
                  <p style={{ fontSize: '14px', color: 'rgba(255,255,255,0.8)' }}>{musician.genres}</p>
                  
                  <div style={{ display: 'flex', gap: '16px', marginTop: '16px' }}>
                    <div>
                      <div className="text-muted" style={{ fontSize: '11px', textTransform: 'uppercase' }}>Rating</div>
                      <div style={{ fontWeight: '500', color: 'var(--warning)' }}>★ {musician.avg_rating || 'N/A'}</div>
                    </div>
                    <div>
                      <div className="text-muted" style={{ fontSize: '11px', textTransform: 'uppercase' }}>Bookings</div>
                      <div style={{ fontWeight: '500' }}>{musician.booking_count}</div>
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '16px' }}>
                  <div>
                    <div className="text-muted" style={{ fontSize: '11px', textTransform: 'uppercase' }}>Base Price</div>
                    <div style={{ fontWeight: 'bold' }}>£{musician.base_price}</div>
                  </div>
                  <Link href={`/musicians/${musician.musician_id}`} className="btn btn-outline" style={{ padding: '6px 12px', fontSize: '12px' }}>
                    View Profile
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    </AppLayout>
  );
}
