// client/src/Login.jsx
import React from 'react';
import './App.css'; 

// Make sure these images exist in client/src/assets/ or the app will crash!
import teddLogo from './assets/tedd.png' 
import googleIcon from './assets/google.svg' 

const Login = () => {
  const handleLogin = () => {
    // Redirects to your Node server
    window.location.href = 'http://localhost:5000/auth/google';
  };

  return (
    <div className='split-screen-container'>
      {/* LEFT SIDE: TEDD LOGO */}
      <div className='left-panel'>
        <div className='brand-wrapper'>
          <img src={teddLogo} alt="TEDD Logo" className='brand-logo-img'/>
          <p className='tagline'>The Email Dangers Detector</p>
        </div>
      </div>

      {/* RIGHT SIDE: LOGIN */}
      <div className='right-panel'>
        <div className='login-card'>
          <h2 className='login-header'>Login</h2>

          <button className='navy-google-btn' onClick={handleLogin}>
            <div className='icon-wrapper'>
               <img src={googleIcon} alt="G" className='google-icon' />
            </div>
            <span className='btn-next'>Login with Google</span>
          </button>
  
        </div>
      </div>
    </div>
  );
};

export default Login;