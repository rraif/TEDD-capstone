// client/src/App.jsx
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Login from './Login'; 
import Inbox from './Inbox'; 
import Layout from './Layout'; 
import Admin from './Admin';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Default to Login */}
        <Route path="/" element={<Login />} />
        
        {/* Explicit Login Route */}
        <Route path="/login" element={<Login />} />
        
        {/* Authenticated Routes wrapped in Layout (Sidebar/Header) */}
        <Route element={<Layout />}>
          
          {/* Standard Inbox Mode */}
          <Route 
            path="/inbox" 
            element={<Inbox viewType="inbox" apiEndpoint="/api/emails" />} 
          />
          
          {/* Hidden Emails Mode */}
          <Route 
            path="/hidden" 
            element={<Inbox viewType="hidden" apiEndpoint="/api/emails/hidden" />} 
          />
          
          <Route path="/admin" element={<Admin />} />
          
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;