//this is vibe coded, temporary use for testing
import { useEffect, useState } from 'react';

const Inbox = () => {
  const [emails, setEmails] = useState(null);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [showHeadersOnly, setShowHeadersOnly] = useState(false);
  const apiURL = import.meta.env.VITE_API_URL;

  useEffect(() => {
    fetch(`${apiURL}/api/emails`, {
      credentials: 'include' // IMPORTANT: This sends the Session Cookie!
    })
    .then(res => res.json())
    .then(data => setEmails(data))
    .catch(err => console.error(err));
  }, []);

  //to fetch a single email
  const openEmail = async (id) => {
    try{
      const res = await fetch(`${apiURL}/api/emails/${id}`, {credentials: 'include'});
      const data = await res.json();
      setSelectedEmail(data);
      setShowHeadersOnly(false);
    } catch (err) {
      console.error('failed to open email', err);
    }
  };

  const logout = () => {
    window.location.href = `${apiURL}/logout`;
  };

  if (!emails) return <div>Loading your secure inbox...</div>;

  if(selectedEmail){
    return(
     <div style={{ padding: '2rem' }}>
        <button onClick={() => setSelectedEmail(null)}>⬅ Back to Inbox</button>
        
        {/* The Toggle Button */}
        <button 
            onClick={() => setShowHeadersOnly(!showHeadersOnly)} 
            style={{ marginLeft: '10px', backgroundColor: '#444', color: 'white' }}
        >
            {showHeadersOnly ? "Show Email" : "Show Headers"}
        </button>

        {/* Dynamic Title */}
        <h2>{showHeadersOnly ? "Email Header" : "Email Content"}</h2>
        
        {/* THE CLEAN VIEW */}
        <pre style={{ background: '#f4f4f4', padding: '10px', overflowX: 'scroll', whiteSpace: 'pre-wrap' }}>
            {JSON.stringify(
                // Logic: Switch between the two cleaned objects from backend
                showHeadersOnly ? selectedEmail.headers : selectedEmail.basic, 
                null, 
                2
            )}
        </pre>
      </div>
    ); 
  }

  return (
    <div style={{ padding: '2rem' }}>
      <button type="button" onClick={logout}>Logout</button>
      <h1>TEDD - Inbox</h1>

      {emails.map(email => (
        <div key={email.id} style={{ marginBottom: '20px', borderBottom: '2px dashed #ccc', paddingBottom: '10px' }}>
            
            {/* 1. The Button for this specific email */}
            <button 
                onClick={() => openEmail(email.id)}
                style={{ marginBottom: '5px', backgroundColor: '#007bff', color: 'white' }}
            >
                vv Open Email vv 
            </button>

            {/* 2. The Raw JSON for just this email */}
            <pre style={{ background: '#f4f4f4', padding: '10px' }}>
                {JSON.stringify(email, null, 2)}
            </pre>
        </div>
      ))}
  
    </div>
  );
}

export default Inbox;