// client/src/App.jsx
import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Login from './Login'; 
import Inbox from './Inbox'; 
import Layout from './Layout'; 
import Admin from './Admin';
import Stats from './Stats';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        

        <Route path="/login" element={<Login />} />
        
        <Route element={<Layout />}>
          <Route 
            path="/inbox" 
            element={<Inbox viewType="inbox" apiEndpoint="/api/emails" />} 
          />
          <Route 
            path="/hidden" 
            element={<Inbox viewType="hidden" apiEndpoint="/api/emails/hidden" />} 
          />
          <Route path="/admin" element={<Admin />} />
          <Route path="/stats" element={<Stats />} />
          
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;