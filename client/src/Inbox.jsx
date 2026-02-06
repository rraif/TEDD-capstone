//this is vibe coded, temporary use for testing
import { useEffect, useState } from 'react';

function Inbox() {
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

  if (!emails) return <div>Loading your secure inbox...</div>;

  return (
    <div style={{ padding: '2rem' }}>
      <h1>TEDD Secure Inbox</h1>
      <pre>{JSON.stringify(emails, null, 2)}</pre>
    </div>
  );
}

export default Inbox;