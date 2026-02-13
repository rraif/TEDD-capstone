import React from 'react';

export default function Sidebar({ onLogout }) {
  const navItems = [
    { name: 'Inbox', icon: '📥' },
    { name: 'Training', icon: '🎓' },
    { name: 'Stats', icon: '📊' },
    { name: 'Hidden', icon: '👁️‍🗨️' },
  ];

  return (
    <aside className="w-64 bg-[#0F172A] text-slate-300 h-full border-r border-white flex flex-col p-4">
      
      {/* Navigation Options */}
      <nav className="flex flex-col gap-2">
        {navItems.map((item) => (
          <button
            key={item.name}
            className="flex items-center gap-4 px-4 py-3 rounded-lg transition-all duration-200 
                       text-slate-400 hover:bg-slate-800 hover:text-white group"
          >
            <span className="text-xl group-hover:scale-110 transition-transform">
              {item.icon}
            </span>
            <span className="font-medium">{item.name}</span>
          </button>
        ))}
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