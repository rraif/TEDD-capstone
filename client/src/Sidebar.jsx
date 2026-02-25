import React from 'react';
import { NavLink } from 'react-router-dom';

export default function Sidebar({ user, onLogout }) {
  const navItems = [
    { name: 'Inbox', icon: '📥', path: '/inbox' },
    { name: 'Training', icon: '🎓', path: '/training' },
    { name: 'Stats', icon: '📊', path: '/stats' },
    { name: 'Hidden', icon: '👁️‍🗨️', path: '/hidden' },
  ];

  return (
    <aside className="w-64 bg-[#0F172A] text-slate-300 h-full border-r border-white flex flex-col p-4">
      
      {/* Navigation Options */}
      <nav className="flex flex-col gap-2">
        {navItems.map((item) => (
          <NavLink
            key={item.name}
            to={item.path}
            className={({ isActive }) => 
              `flex items-center gap-4 px-4 py-3 rounded-lg transition-all duration-200 group ` +
              (isActive 
                ? `bg-blue-600/20 text-blue-400 font-bold` // Highlight active tab
                : `text-slate-400 hover:bg-slate-800 hover:text-white font-medium`)
            }
          >
            <span className="text-xl group-hover:scale-110 transition-transform">
              {item.icon}
            </span>
            <span>{item.name}</span>
          </NavLink>
        ))}

      {/* --- ADMIN BUTTON --- */}
        {user?.is_team_admin && (
          <NavLink
            to="/admin"
            className={({ isActive }) => 
              `flex items-center gap-4 px-4 py-3 rounded-lg transition-all duration-200 group mt-4 border border-transparent ` +
              (isActive 
                ? `bg-purple-900/20 text-purple-400 border-purple-500/30 font-bold` 
                : `text-slate-400 hover:bg-slate-800 hover:text-white font-medium`)
            }
          >
            <span className="text-xl group-hover:scale-110 transition-transform">
              👑
            </span>
            <span>Team Admin</span>
          </NavLink>
        )}
      </nav>

      {/* Logout Button - Pushed to the bottom using mt-auto */}
      <div className="mt-auto pt-4 border-t border-slate-800">
        <button 
          onClick={onLogout}
          className="w-full flex items-center gap-4 px-4 py-3 rounded-lg transition-all duration-200 
                     text-red-400 hover:bg-red-500/10 hover:text-red-300"
        >
          <span className="text-xl">🚪</span>
          <span className="font-medium">LOG OUT</span>
        </button>
      </div>

    </aside>
  );
}