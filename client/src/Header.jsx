import React, { useState, useEffect } from 'react';
import teddLogo from './assets/TEDD-Logo-White.svg';

export default function Header() {
  const [userEmail, setUserEmail] = useState("Loading...");
  const [userInitial, setUserInitial] = useState("");

  useEffect(() => {
    // Fetch the current user's info from the backend
    const fetchUser = async () => {
      try {
        const apiURL = import.meta.env.VITE_API_URL;
        
        // Ensure you use your actual user endpoint here (e.g., /auth/user, /api/me, etc.)
        const response = await fetch(`${apiURL}/api/current_user`, {
          credentials: 'include' // This is crucial to send the Google session cookie!
        });

        if (response.ok) {
          const userData = await response.json();
          setUserEmail(userData.email);
          // Grab the first letter of their email for the profile picture bubble
          setUserInitial(userData.email.charAt(0).toUpperCase()); 
        } else {
          setUserEmail("Not logged in");
        }
      } catch (error) {
        console.error("Failed to fetch user:", error);
        setUserEmail("Error");
      }
    };

    fetchUser();
  }, []);

  return (
    <header className="flex items-center justify-between pl-0.1 pr-6 py-3 bg-[#0F172A] border-b border-white">
      
      {/* LEFT SIDE: TEDD Logo */}
      <div className="flex items-center">
        <img 
          src={teddLogo} 
          alt="TEDD Logo" 
          className="h-8 w-auto scale-500 origin-left" 
        />
      </div>

      {/* RIGHT SIDE: Email & Profile Picture */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-slate-200">
          {userEmail}
        </span>
        
        <button 
          className="h-9 w-9 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold hover:bg-blue-700 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-[#0F172A] focus:ring-blue-500"
          aria-label="User profile"
        >
          {userInitial || "?"}
        </button>
      </div>

    </header>
  );
}