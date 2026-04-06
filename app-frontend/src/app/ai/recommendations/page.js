"use client";
import { useState, useEffect } from "react";
import AppLayout from "@/components/AppLayout";
import { fetchApi } from "@/lib/api";
import { Loader2, Search, BrainCircuit, Sparkles } from "lucide-react";

export default function AIRecommendations() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const [formData, setFormData] = useState({
    genres: ["Jazz", "Soul"],
    location: "London",
    top_n: 6,
  });

  const availableGenres = [
    'Acoustic', 'Blues', 'Classical', 'Country', 'Electronic', 
    'Folk', 'Funk', 'Hip Hop', 'Indie', 'Jazz', 'Latin', 
    'Metal', 'Pop', 'Punk', 'R&B', 'Reggae', 'Rock', 'Soul'
  ];

  const handleChange = (e) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const toggleGenre = (genre) => {
    setFormData(prev => {
      const genres = prev.genres.includes(genre)
        ? prev.genres.filter(g => g !== genre)
        : [...prev.genres, genre];
      return { ...prev, genres };
    });
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (isDropdownOpen && !event.target.closest('.multi-select-container')) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isDropdownOpen]);

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const payload = {
        ...formData,
        genres: formData.genres.join(", ")
      };
      const qs = new URLSearchParams(payload).toString();
      const data = await fetchApi(`/ai/recommendations?${qs}`);
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppLayout>
      <div style={{ padding: '20px', maxWidth: '1200px' }}>
        
        <div style={{ marginBottom: '40px' }}>
          <div className="badge badge-primary animate-fade-in" style={{ marginBottom: '16px' }}>
            <BrainCircuit size={14} style={{ marginRight: '6px' }}/> Content-Based & Collaborative Filtering
          </div>
          <h1 style={{ fontSize: '32px', fontWeight: 'bold' }}>Find The Perfect Musician</h1>
          <p className="text-muted">Our hybrid recommendation matrix uses TF-IDF and SVD to precisely match talent to your needs.</p>
        </div>

        <div className="glass-card animate-fade-in" style={{ marginBottom: '40px', padding: '20px' }}>
          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '16px', alignItems: 'flex-end', flexWrap: 'wrap' }}>
            
            <div className="form-group" style={{ marginBottom: 0, flex: '2 1 400px' }}>
              <label className="form-label">Musical Genres</label>
              <div className="multi-select-container">
                <div 
                  className="selected-genres" 
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                >
                  {formData.genres.length === 0 ? (
                    <span className="text-muted" style={{ fontSize: '14px' }}>Select genres...</span>
                  ) : (
                    formData.genres.map(genre => (
                      <span key={genre} className="genre-pill">
                        {genre}
                        <button 
                          type="button" 
                          onClick={(e) => { e.stopPropagation(); toggleGenre(genre); }}
                        >
                          ×
                        </button>
                      </span>
                    ))
                  )}
                </div>

                {isDropdownOpen && (
                  <div className="genre-dropdown glass-card animate-fade-in" style={{ padding: '8px' }}>
                    {availableGenres.map(genre => (
                      <div 
                        key={genre} 
                        className={`genre-option ${formData.genres.includes(genre) ? 'selected' : ''}`}
                        onClick={() => toggleGenre(genre)}
                      >
                        {genre}
                        {formData.genres.includes(genre) && <Sparkles size={12} />}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            
            <div className="form-group" style={{ marginBottom: 0, flex: '1 1 200px' }}>
              <label className="form-label">Location</label>
              <input 
                type="text" 
                name="location" 
                value={formData.location} 
                onChange={handleChange} 
                className="form-input" 
                placeholder="City"
              />
            </div>

            <button type="submit" disabled={loading} className="btn btn-primary" style={{ height: '45px', padding: '0 30px', minWidth: '140px' }}>
              {loading ? <Loader2 className="animate-spin" /> : <><Search size={18} style={{ marginRight: '8px' }}/> Search</>}
            </button>
          </form>
          {error && <p style={{ color: 'var(--danger)', marginTop: '12px' }}>{error}</p>}
        </div>

        {results.length > 0 && (
          <div className="animate-fade-in">
            <h2 style={{ fontSize: '20px', fontWeight: '600', marginBottom: '24px' }}>Top AI Recommendations</h2>
            
            <div className="grid grid-cols-3">
              {results.map((musician, idx) => (
                <div key={musician.musician_id} className="glass-card" style={{ position: 'relative', overflow: 'hidden' }}>
                  
                  {idx === 0 && (
                     <div style={{ position: 'absolute', top: 12, right: 12, background: 'var(--primary)', color: 'white', padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Sparkles size={12} /> BEST MATCH
                     </div>
                  )}

                  <div style={{ marginBottom: '16px' }}>
                    <div className="badge" style={{ background: 'rgba(255,255,255,0.1)', marginBottom: '12px' }}>{musician.musician_type}</div>
                    <h3 style={{ fontSize: '20px', fontWeight: 'bold' }}>{musician.musician_name}</h3>
                    <p className="text-muted" style={{ fontSize: '14px', marginTop: '4px' }}>{musician.location}</p>
                  </div>

                  <p style={{ fontSize: '14px', marginBottom: '20px', minHeight: '42px', color: 'rgba(255,255,255,0.8)' }}>
                    {musician.genres}
                  </p>

                  <div style={{ background: 'rgba(0,0,0,0.3)', padding: '12px', borderRadius: '8px', marginBottom: '20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '8px' }}>
                      <span className="text-muted">Recommendation Score</span>
                      <span style={{ fontWeight: 'bold', color: 'var(--primary)' }}>{(musician.final_score * 100).toFixed(1)}%</span>
                    </div>
                    
                    <div style={{ display: 'flex', height: '6px', borderRadius: '3px', overflow: 'hidden', background: 'rgba(255,255,255,0.1)' }}>
                      <div style={{ width: `${(musician.cbf_score / (musician.final_score || 1)) * 100}%`, background: 'var(--primary)' }} title={`Content Match: ${(musician.cbf_score*100).toFixed(1)}%`} />
                      <div style={{ width: `${(musician.sentiment_boost / (musician.final_score || 1)) * 100}%`, background: 'var(--success)' }} title={`Sentiment Boost: ${(musician.sentiment_boost*100).toFixed(1)}%`} />
                    </div>
                    <div style={{ display: 'flex', gap: '12px', marginTop: '6px', fontSize: '10px' }}>
                      <span style={{ color: 'var(--primary)', display: 'flex', alignItems: 'center', gap: '4px' }}><div style={{width: 6, height: 6, borderRadius: 3, background:'var(--primary)'}}/> TF-IDF Match</span>
                      <span style={{ color: 'var(--success)', display: 'flex', alignItems: 'center', gap: '4px' }}><div style={{width: 6, height: 6, borderRadius: 3, background:'var(--success)'}}/> NLP Boost</span>
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ fontWeight: 'bold' }}>£{musician.base_price}<span className="text-muted" style={{ fontSize: '12px', fontWeight: 'normal' }}> base</span></div>
                    <button className="btn btn-outline" style={{ padding: '6px 16px', fontSize: '13px' }}>View Profile</button>
                  </div>

                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </AppLayout>
  );
}