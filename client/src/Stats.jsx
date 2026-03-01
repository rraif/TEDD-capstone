import React, { useEffect, useState } from 'react';

// 🚀 Pulling the rank logic out so we can use it for both the user AND the leaderboard
const getRankDetails = (currentScore) => {
  if (currentScore >= 5000) return { title: "Unhackable", prevThreshold: 5000, nextThreshold: 5000, isMax: true };
  if (currentScore >= 3000) return { title: "Ultra-Vigilant", prevThreshold: 3000, nextThreshold: 5000, isMax: false };
  if (currentScore >= 1500) return { title: "Analyst III", prevThreshold: 1500, nextThreshold: 3000, isMax: false };
  if (currentScore >= 500) return { title: "Analyst II", prevThreshold: 500, nextThreshold: 1500, isMax: false };
  return { title: "Beginner Analyst", prevThreshold: 0, nextThreshold: 500, isMax: false };
};

export default function Stats() {
  const [userData, setUserData] = useState(null);
  const [teamData, setTeamData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState('score'); // 'score' or 'streak'
  const apiURL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  useEffect(() => {
    // Fetch BOTH personal stats and team roster concurrently
    Promise.all([
      fetch(`${apiURL}/api/current-user`, { credentials: 'include' }).then(res => res.json()),
      fetch(`${apiURL}/api/teams/current`, { credentials: 'include' }).then(res => res.json())
    ])
    .then(([userRes, teamRes]) => {
      if (!userRes.error) setUserData(userRes);
      if (!teamRes.error && teamRes.members) setTeamData(teamRes);
      setLoading(false);
    })
    .catch(err => {
      console.error("Network error fetching stats:", err);
      setLoading(false);
    });
  }, [apiURL]);

  if (loading) {
    return (
      <div className="bg-[#0F172A] min-h-full p-8 flex justify-center items-center">
        <div className="animate-spin h-10 w-10 border-4 border-blue-500 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (!userData) {
    return (
      <div className="bg-[#0F172A] min-h-full p-8 flex flex-col items-center justify-center text-slate-400">
        <span className="text-4xl mb-4">📭</span>
        <p>Could not load user statistics.</p>
      </div>
    );
  }

  // Personal Stats Mapping
  const score = userData.user_score || 0;
  const streak = userData.survival_streak || 0;

  // 🚀 Dynamic Math for the Progress Bar
  const { title, prevThreshold, nextThreshold, isMax } = getRankDetails(score);
  const xpToNext = isMax ? 0 : nextThreshold - score;
  const progressPercent = isMax ? 100 : ((score - prevThreshold) / (nextThreshold - prevThreshold)) * 100;

  // Leaderboard Sorting Logic
  const members = teamData?.members || [];
  const sortedMembers = [...members].sort((a, b) => {
    if (sortBy === 'score') return (b.user_score || 0) - (a.user_score || 0);
    return (b.survival_streak || 0) - (a.survival_streak || 0);
  });

  return (
    <div className="bg-[#0F172A] min-h-full p-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        {/* CARD 1: OVERALL SCORE & RANK */}
        <div className="bg-[#020617] p-6 rounded-xl border border-slate-800 shadow-lg col-span-1 md:col-span-2 lg:col-span-2 flex flex-col justify-center relative overflow-hidden">
          <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 bg-blue-600/10 blur-3xl rounded-full pointer-events-none"></div>
          <div className="flex justify-between items-end mb-2 relative z-10">
            <div>
              <p className="text-slate-400 text-sm font-bold uppercase tracking-wider mb-1">Current Title</p>
              <h2 className="text-4xl font-bold text-blue-400">{title}</h2>
            </div>
            <div className="text-right">
              <p className="text-slate-400 text-sm font-bold uppercase tracking-wider mb-1">Total Score</p>
              <p className="text-4xl font-mono text-white">{score.toLocaleString()} <span className="text-lg text-blue-500">XP</span></p>
            </div>
          </div>
          
          {/* 🚀 Updated Dynamic Progress Bar */}
          <div className="mt-6 relative z-10">
            <div className="flex justify-between text-xs text-slate-500 mb-2 font-mono">
              <span>Current Level Progress</span>
              <span>{isMax ? 'Max Rank Achieved!' : `${xpToNext.toLocaleString()} XP to Next Rank`}</span>
            </div>
            <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-blue-600 to-cyan-400 rounded-full transition-all duration-1000 ease-out"
                style={{ width: `${progressPercent}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* CARD 2: SURVIVAL STREAK */}
        <div className="bg-[#020617] p-6 rounded-xl border border-orange-500/30 shadow-[0_0_15px_rgba(249,115,22,0.1)] flex flex-col items-center justify-center text-center relative overflow-hidden">
          {streak >= 3 && (
            <div className="absolute inset-0 bg-gradient-to-t from-orange-500/10 to-transparent pointer-events-none"></div>
          )}
          <span className="text-5xl mb-3">{streak >= 5 ? '🔥' : '🛡️'}</span>
          <p className="text-slate-400 text-sm font-bold uppercase tracking-wider mb-1">Survival Streak</p>
          <p className="text-5xl font-mono font-bold text-orange-400">{streak}</p>
          <p className="text-xs text-slate-500 mt-2">Emails correctly identified consecutively in the "Training" simulation.</p>
        </div>

        {/* CARD 3: ACCOUNT & ACCESS DETAILS */}
        <div className="bg-[#020617] p-6 rounded-xl border border-slate-800 shadow-lg col-span-1 md:col-span-2 lg:col-span-3">
          <h3 className="text-slate-400 text-sm font-bold uppercase tracking-wider mb-6 border-b border-slate-800 pb-2">
            Account & Access Details
          </h3>
          {/* 🚀 Swapped from grid-cols-3 to grid-cols-2 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-center">
            
            <div className="bg-[#0F172A] p-4 rounded-lg border border-slate-800 flex flex-col justify-center">
              <p className="text-slate-500 text-xs font-bold uppercase mb-2">Organization</p>
              <p className="text-2xl font-bold mt-1 text-slate-200 truncate px-2" title={userData.team_name}>
                {userData.team_name || `Unit #${userData.team_id}`}
              </p>
              <p className="text-xs text-green-500/80 mt-2">Status: Active</p>
            </div>
            
            <div className="bg-[#0F172A] p-4 rounded-lg border border-slate-800 flex flex-col justify-center">
              <p className="text-slate-500 text-xs font-bold uppercase mb-2">System Privileges</p>
              <p className={`text-2xl font-bold mt-1 ${userData.is_team_admin ? 'text-purple-400' : 'text-slate-300'}`}>
                {userData.is_team_admin ? 'Admin' : 'Standard User'}
              </p>
              <p className="text-xs text-slate-500 mt-2">
                {userData.is_team_admin ? 'Full administrative privileges' : 'Standard access'}
              </p>
            </div>
            
          </div>
        </div>

        {/* CARD 4: TEAM LEADERBOARD */}
        <div className="bg-[#020617] p-6 rounded-xl border border-slate-800 shadow-lg col-span-1 md:col-span-2 lg:col-span-3">
          <div className="flex justify-between items-center mb-6 border-b border-slate-800 pb-2">
            <h3 className="text-slate-400 text-sm font-bold uppercase tracking-wider">
              Unit Leaderboard
            </h3>
            
            {/* Toggle Switch */}
            <div className="flex bg-[#0F172A] rounded-lg p-1 border border-slate-800">
              <button 
                onClick={() => setSortBy('score')}
                className={`px-3 py-1.5 text-xs font-bold rounded-md transition-all ${sortBy === 'score' ? 'bg-blue-600/20 text-blue-400 shadow' : 'text-slate-500 hover:text-slate-300'}`}
              >
                By Score
              </button>
              <button 
                onClick={() => setSortBy('streak')}
                className={`px-3 py-1.5 text-xs font-bold rounded-md transition-all ${sortBy === 'streak' ? 'bg-orange-600/20 text-orange-400 shadow' : 'text-slate-500 hover:text-slate-300'}`}
              >
                By Streak
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[600px]">
              <thead>
                <tr className="text-slate-500 text-xs uppercase tracking-wider border-b border-slate-800/80">
                  <th className="pb-3 pl-4 w-16">Rank</th>
                  <th className="pb-3">Operator</th>
                  <th className="pb-3">Title</th>
                  <th className="pb-3 text-right">Score</th>
                  <th className="pb-3 text-right pr-4">Streak</th>
                </tr>
              </thead>
              <tbody>
                {sortedMembers.map((member, index) => {
                  const isMe = member.user_id === userData?.user_id;
                  
                  return (
                    <tr 
                      key={member.user_id} 
                      className={`border-b border-slate-800/40 hover:bg-slate-800/30 transition-colors ${isMe ? 'bg-blue-900/10' : ''}`}
                    >
                      <td className="py-4 pl-4 text-slate-400 font-mono text-sm">
                        #{index + 1}
                      </td>
                      <td className={`py-4 font-bold ${isMe ? 'text-blue-300' : 'text-slate-200'}`}>
                        {member.display_name} 
                        {isMe && <span className="ml-2 text-[10px] bg-blue-600/20 text-blue-400 px-2 py-0.5 rounded uppercase tracking-wider border border-blue-500/30">You</span>}
                      </td>
                      
                      {/* 🚀 Leaderboard now matches the dynamic frontend titles too! */}
                      <td className="py-4 text-sm text-slate-400">
                        {getRankDetails(member.user_score || 0).title}
                      </td>
                      
                      <td className="py-4 text-right font-mono text-blue-400 text-sm">
                        {(member.user_score || 0).toLocaleString()} <span className="text-xs opacity-70">XP</span>
                      </td>
                      <td className="py-4 text-right font-mono text-orange-400 pr-4 text-sm">
                        {member.survival_streak || 0} {(member.survival_streak >= 5) && <span className="ml-1 text-base">🔥</span>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            
            {sortedMembers.length === 0 && (
              <div className="text-center py-8 text-slate-500 text-sm">
                No team data available.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}