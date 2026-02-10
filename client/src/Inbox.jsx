//this is vibe coded, temporary use for testing
import { useEffect, useState } from 'react';

const Inbox = () => {
  const [emails, setEmails] = useState(null);

  useEffect(() => {
    const apiURL = import.meta.env.VITE_API_URL;
    fetch(`${apiURL}/api/emails`, {
      credentials: 'include' // IMPORTANT: This sends the Session Cookie!
    })
    .then(res => res.json())
    .then(data => setEmails(data))
    .catch(err => console.error(err));
  }, []);

  const logout = () => {
    const apiUrl = import.meta.env.VITE_API_URL;
    window.location.href = `${apiUrl}/logout`;
  };

  if (!emails) return <div>Loading your secure inbox...</div>;

  return (
    <div style={{ padding: '2rem' }}>
      <button type="button" onClick={logout}>Logout</button>
      <h1>TEDD Secure Inbox</h1>
      <pre>{JSON.stringify(emails, null, 2)}</pre>
    </div>
  );
}

export default Inbox;