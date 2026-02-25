import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import TeamSetup from './TeamSetup'; // <-- Import your new component

export default function Layout() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  const apiURL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  useEffect(() => {
    // 1. Fetch the user profile (including their team_id) when Layout loads
    const fetchUser = async () => {
      try {
        const res = await fetch(`${apiURL}/api/current-user`, { credentials: 'include' });
        if (res.ok) {
          const userData = await res.json();
          setUser(userData);
        } else {
          window.location.href = '/'; // Kick them to login if not authenticated
        }
      } catch (err) {
        console.error("Failed to fetch user session", err);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [apiURL]);

  const handleLogout = () => {
    window.location.href = `${apiURL}/logout`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-950 text-slate-300">
        <div className="animate-pulse text-xl">Loading workspace...</div>
      </div>
    );
  }

  // 2. THE GATEKEEPER: If they are logged in but have NO team, trap them here.
  if (user && !user.team_id) {
    return (
      <TeamSetup 
        onTeamSet={(newTeam) => {
          // When they join/create a team, instantly update state to unlock the Inbox!
          setUser({ ...user, team_id: newTeam.team_id });
        }} 
      />
    );
  }

  // 3. If they have a team_id, let them through to the normal app!
  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Header user={user} />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar user={user} onLogout={handleLogout} />

        <main className="flex-1 overflow-y-auto bg-white">
          <Outlet context={{ user }} />
        </main>
      </div>
    </div>
  );
}