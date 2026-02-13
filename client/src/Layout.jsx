import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';

export default function Layout() {
  const apiURL = import.meta.env.VITE_API_URL;

  const handleLogout = () => {
    window.location.href = `${apiURL}/logout`;
  };

 return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Header with its white bottom border */}
      <Header />

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar with its new white right border */}
        <Sidebar onLogout={handleLogout} />

        {/* Main Content (Inbox, etc.) */}
        <main className="flex-1 overflow-y-auto bg-white">
          <Outlet />
        </main>
      </div>
    </div>
  );
}