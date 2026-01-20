import './App.css'
import teddLogo from './assets/tedd.png' 
import googleIcon from './assets/google.svg' 

function App() {
  //handles redirect (this button takes to website)
  const handleLogin = () => {
    window.location.href = 'http://localhost:5000/auth/google'
  };

  return (
    <div className='split-screen-container'>
      {/*LEFT SIDE: TEDD LOGO*/}
      <div className='left-panel'>
        <div className='brand-wrapper'>
          {/*USE TEDD IMAGE*/}
          <img src ={teddLogo} alt  = "TEDD Logo" className='brand-logo-img'/>

          <p className='tagline'>The Email Dangers Detector</p>
        </div>
      </div>

    {/*RIGHT SIDE: Login*/}
      <div className='right-panel'>
        <div className='login-card'>
          <h2 className='login-header'>Login</h2>

          <button className='navy-google-btn' onClick={handleLogin}>
            <div className='icon-wrapper'>
             {/* USE GOOGLE IMAGE */}
             <img src={googleIcon} alt="G" className='google-icon' />
            </div>
            <span className='btn-next'>Login with Google</span>
          </button>
  
        </div>
      </div>
    </div>
  )
}

export default App
