// client/src/App.jsx
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './Login'; // Import the file you just created
import Inbox from './Inbox'; // Import the inbox we made earlier
import Layout from './Layout'; //This will store the header and sidebar for all pages

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Default to Login */}
        <Route path="/" element={<Login />} />
        
        {/* Explicit Login Route */}
        <Route path="/login" element={<Login />} />
        
        {/* The Inbox Route (Where the backend sends you) */}
       <Route element={<Layout />}>
          <Route path="/inbox" element={<Inbox />} />
          {/* Any other pages you add later (e.g., /settings) go here! */}
          
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
        
      

export default App;