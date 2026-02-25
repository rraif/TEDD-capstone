import React, { useEffect, useState } from 'react';
import { useOutletContext, Navigate } from 'react-router-dom';

export default function Admin() {
  const { user } = useOutletContext();
  const [teamData, setTeamData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null); // <-- NEW: Error state!
  
  const apiURL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  useEffect(() => {
    fetchTeamData();
  }, []);

  const fetchTeamData = async () => {
    try {
      const res = await fetch(`${apiURL}/api/teams/current`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setTeamData(data);
      } else {
        // If the server sends back an error (like 404), catch it here!
        setError(`Server returned status: ${res.status}. Did you restart the backend?`);
      }
    } catch (err) {
      console.error("Failed to load team data", err);
      setError("Network error. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const handleKick = async (userId, userName) => {
    if (!window.confirm(`Are you sure you want to remove ${userName} from the team?`)) return;
    try {
      await fetch(`${apiURL}/api/teams/members/${userId}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      fetchTeamData(); // Refresh list
    } catch (err) {
      console.error("Failed to kick user", err);
    }
  };

  const handleDeleteTeam = async () => {
    if (!window.confirm("WARNING: This will permanently delete the team and remove all members. Continue?")) return;
    try {
      const res = await fetch(`${apiURL}/api/teams/current`, {
        method: 'DELETE',
        credentials: 'include'
      });
      if (res.ok) {
        // Force a page reload so the Layout gatekeeper catches them
        window.location.href = '/';
      }
    } catch (err) {
      console.error("Failed to delete team", err);
    }
  };

  // Security check: Only admins allowed
  if (!user?.is_team_admin) return <Navigate to="/inbox" />;

  // Better loading & error UI
  if (loading) return <div className="p-8 text-slate-400 bg-[#0F172A] min-h-full">Loading admin panel...</div>;
  if (error) return <div className="p-8 text-red-400 bg-[#0F172A] min-h-full font-bold">Error: {error}</div>;
  if (!teamData) return <div className="p-8 text-slate-400 bg-[#0F172A] min-h-full">No team data found.</div>;

  return (
    <div className="bg-[#0F172A] min-h-full p-8 text-slate-200">
      <div className="max-w-5xl mx-auto">
        
        {/* Header Section */}
        <div className="flex justify-between items-start mb-10">
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Team Management</h1>
            <p className="text-slate-400">Manage members and settings for <span className="text-blue-400 font-bold">{teamData.team.team_name}</span></p>
          </div>
          
          <div className="bg-slate-900 border border-slate-700 p-4 rounded-xl text-center shadow-lg">
            <div className="text-xs uppercase tracking-widest text-slate-500 font-bold mb-1">Join Code</div>
            <div className="text-3xl font-mono font-bold text-white tracking-widest">{teamData.team.join_code}</div>
          </div>
        </div>

        {/* Member Roster */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-lg mb-8">
          <div className="px-6 py-4 border-b border-slate-800 bg-[#020617] flex justify-between items-center">
            <h2 className="text-lg font-bold text-white">Team Roster</h2>
            <span className="bg-blue-900/50 text-blue-400 text-xs px-3 py-1 rounded-full font-bold">
              {teamData.members.length} Members
            </span>
          </div>
          
          <div className="divide-y divide-slate-800/80">
            {teamData.members.map((member) => (
              <div key={member.user_id} className="flex items-center justify-between p-6 hover:bg-slate-800/30 transition-colors">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center text-xl font-bold border border-slate-700">
                    {member.display_name?.charAt(0) || '?'}
                  </div>
                  <div>
                    <div className="font-bold text-white flex items-center gap-2">
                      {member.display_name}
                      {member.is_team_admin && (
                        <span className="bg-purple-900/50 text-purple-300 text-[10px] uppercase tracking-wider px-2 py-0.5 rounded border border-purple-500/30">Admin</span>
                      )}
                    </div>
                    <div className="text-sm text-slate-400">{member.email}</div>
                  </div>
                </div>
                
                <div className="flex items-center gap-8">
                  <div className="text-right">
                    <div className="text-xs text-slate-500 font-bold uppercase tracking-wider mb-1">Score</div>
                    <div className="text-xl font-mono font-bold text-green-400">{member.user_score}</div>
                  </div>
                  
                  {/* Don't let the admin kick themselves! */}
                  {!member.is_team_admin && (
                    <button 
                      onClick={() => handleKick(member.user_id, member.display_name)}
                      className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                      title="Remove Member"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                    </button>
                  )}
                  {member.is_team_admin && <div className="w-9"></div> /* Spacer for alignment */}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Danger Zone */}
        <div className="border border-red-900/50 bg-red-950/10 rounded-xl p-6">
          <h3 className="text-red-400 font-bold mb-2">Danger Zone</h3>
          <p className="text-sm text-slate-400 mb-4">Permanently delete this team. This action cannot be undone and will remove all members immediately.</p>
          <button 
            onClick={handleDeleteTeam}
            className="bg-red-900/50 hover:bg-red-600 text-red-200 text-sm font-bold py-2 px-4 rounded border border-red-700/50 transition-colors"
          >
            Delete Team
          </button>
        </div>

      </div>
    </div>
  );
}