// client/src/App.jsx
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './Login'; // Import the file you just created
import Inbox from './Inbox'; // Import the inbox we made earlier

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Default to Login */}
        <Route path="/" element={<Login />} />
        
        {/* Explicit Login Route */}
        <Route path="/login" element={<Login />} />
        
        {/* The Inbox Route (Where the backend sends you) */}
        <Route path="/inbox" element={<Inbox />} />
        
        {/* Catch-all: If user types random junk, go to Login */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;