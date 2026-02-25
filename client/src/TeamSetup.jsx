import React, { useState } from 'react';

export default function TeamSetup({ onTeamSet }) {
  const [activeTab, setActiveTab] = useState('join'); // 'join' or 'create'
  const [teamName, setTeamName] = useState('');
  const [joinCode, setJoinCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [createdTeam, setCreatedTeam] = useState(null);

  const apiURL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  const handleCreate = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${apiURL}/api/teams/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ teamName }),
        credentials: 'include'
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      
      // Success! Pass the new team data back up to Layout.jsx
      setCreatedTeam(data.team);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleJoin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${apiURL}/api/teams/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ joinCode: joinCode.toUpperCase() }),
        credentials: 'include'
      });
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      
      // Success! Pass the joined team data back up to Layout.jsx
      onTeamSet(data.team);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
if (createdTeam) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-slate-950 text-slate-200">
        <div className="w-full max-w-md p-8 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl text-center">
          <div className="text-5xl mb-4">🎉</div>
          <h2 className="text-3xl font-bold text-white mb-2">Team Created!</h2>
          <p className="text-slate-400 mb-8">Share this join code with your group members:</p>
          
          <div className="bg-slate-950 border border-slate-800 rounded-xl p-6 mb-8 shadow-inner">
              <span className="text-5xl font-mono font-bold text-blue-400 tracking-[0.2em]">
                {createdTeam.join_code}
              </span>
          </div>
          
          <button 
            onClick={() => onTeamSet(createdTeam)} 
            className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-lg transition-all shadow-lg shadow-blue-900/20"
          >
            Go to Workspace
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-slate-950 text-slate-200">
      <div className="w-full max-w-md p-8 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Welcome to TEDD</h1>
          <p className="text-slate-400">Join a team or create a new one to access your security dashboard.</p>
        </div>
        
        {/* Toggle Tabs */}
        <div className="flex bg-slate-950 rounded-lg p-1 mb-8 border border-slate-800">
          <button
            className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === 'join' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
            onClick={() => { setActiveTab('join'); setError(''); }}
          >
            Join Team
          </button>
          <button
            className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${activeTab === 'create' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}
            onClick={() => { setActiveTab('create'); setError(''); }}
          >
            Create Team
          </button>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-950/50 border border-red-500/50 text-red-400 text-sm rounded-lg flex items-center gap-2">
            ⚠️ {error}
          </div>
        )}

        {/* JOIN TEAM FORM */}
        {activeTab === 'join' && (
          <form onSubmit={handleJoin} className="flex flex-col gap-5">
            <div>
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Team Code</label>
              <input
                type="text"
                value={joinCode}
                onChange={(e) => setJoinCode(e.target.value)}
                placeholder="e.g. ABC123"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-4 text-white text-center text-xl tracking-[0.5em] font-mono focus:outline-none focus:border-blue-500 transition-colors uppercase"
                maxLength={6}
                required
              />
            </div>
            <button disabled={loading} className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-lg transition-all">
              {loading ? 'Joining...' : 'Join Workspace'}
            </button>
          </form>
        )}

        {/* CREATE TEAM FORM */}
        {activeTab === 'create' && (
          <form onSubmit={handleCreate} className="flex flex-col gap-5">
            <div>
              <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Team Name</label>
              <input
                type="text"
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
                placeholder="e.g. SOC Alpha Team"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-4 text-white focus:outline-none focus:border-blue-500 transition-colors"
                required
              />
            </div>
            <button disabled={loading} className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-4 rounded-lg transition-all">
              {loading ? 'Creating...' : 'Create Workspace'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}