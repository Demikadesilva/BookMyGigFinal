"use client";
import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { 
  Users, Calendar, Activity, TrendingUp, Music, BrainCircuit,
  MessageSquare, CircleDollarSign, LogOut, LayoutDashboard 
} from "lucide-react";

export default function LayoutWrapper({ children }) {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState(null);

  useEffect(() => {
    const storedUser = localStorage.getItem("user");
    if (storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error(e);
      }
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    router.push("/");
  };

  const navItems = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Musicians", href: "/musicians", icon: Users, role: 'client' },
    { name: "My Events", href: "/events", icon: Calendar, role: 'client' },
    { name: "My Gigs", href: "/bookings", icon: Activity },
    { name: "AI Pricing", href: "/ai/pricing", icon: CircleDollarSign },
    { name: "AI Recommendations", href: "/ai/recommendations", icon: BrainCircuit, role: 'client' },
    { name: "Demand Forecast", href: "/ai/demand", icon: TrendingUp },
    { name: "Sentiment & Anomalies", href: "/ai/anomaly", icon: MessageSquare },
  ];

  const filteredNav = navItems.filter(item => !item.role || (user && user.role === item.role));

  return (
    <div className="flex h-screen bg-transparent" style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden'}}>
      {/* Sidebar */}
      <aside className="glass" style={{ width: '280px', padding: '24px', display: 'flex', flexDirection: 'column', margin: '20px', borderRadius: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '40px' }}>
          <Music style={{ color: 'var(--primary)', width: 32, height: 32 }} />
          <h1 style={{ fontSize: '24px', fontWeight: 'bold' }}>BookMy<span className="text-gradient">Gig</span></h1>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px', flex: 1 }}>
          {filteredNav.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link key={item.name} href={item.href} style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '12px', 
                padding: '12px 16px',
                borderRadius: '8px',
                color: isActive ? 'white' : 'rgba(255,255,255,0.6)',
                background: isActive ? 'rgba(124, 58, 237, 0.2)' : 'transparent',
                fontWeight: isActive ? 600 : 400,
                transition: 'all 0.2s',
                textDecoration: 'none'
              }}>
                <item.icon size={20} style={{ color: isActive ? 'var(--primary)' : 'inherit' }} />
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div style={{ marginTop: 'auto', paddingTop: '20px', borderTop: '1px solid var(--border)' }}>
          <button 
            onClick={handleLogout}
            style={{ 
              display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px',
              color: 'var(--danger)', background: 'transparent', border: 'none', cursor: 'pointer', width: '100%', textAlign: 'left', fontWeight: '500'
            }}
          >
            <LogOut size={20} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main style={{ flex: 1, padding: '20px 40px 20px 0', overflowY: 'auto' }}>
        {children}
      </main>
    </div>
  );
}
