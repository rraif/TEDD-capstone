//this is vibe coded, temporary use for testing
import { useEffect, useState } from 'react';

const Inbox = () => {
  const [emails, setEmails] = useState(null);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [showHeadersOnly, setShowHeadersOnly] = useState(false); 
  const [scanResult, setScanResult] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const apiURL = import.meta.env.VITE_API_URL;

  useEffect(() => {
    fetch(`${apiURL}/api/emails`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => setEmails(data))
      .catch(err => console.error(err));
  }, []);

  const openEmail = async (id) => {
    try {
      setScanResult(null);
      setIsScanning(true);

      const res = await fetch(`${apiURL}/api/emails/${id}`, { credentials: 'include' });
      const data = await res.json();
      setSelectedEmail(data);
      setShowHeadersOnly(false); // Reset headers when opening a new email

      //model
      fetch(`${apiURL}/api/scan`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ emailId: id }),
          credentials: 'include'
      })
      .then (res => {
        if (!res.ok) throw new Error("Network response was not ok");
        return res.json();
      })
      .then(scanData =>{
        setScanResult(scanData);
        setIsScanning(false);
      })
      .catch(err => {
        console.error("Auto scan failed", err);
        setIsScanning(false);
      });

    } catch (err) {
      console.error('Failed to open email', err);
    }
  };

  const formatSender = (fromHeader) => {
    if (!fromHeader) return "Unknown";
    return fromHeader.split(' <')[0].replace(/"/g, ''); 
  };

  const formatDate = (dateString) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  if (!emails) return <div className="p-8 text-slate-400 bg-[#0F172A] min-h-full">Loading your secure inbox...</div>;

  // ==========================================
  // VIEW 1: SINGLE EMAIL (DETAIL VIEW)
  // ==========================================
  if (selectedEmail) {
    return (
      <div className="bg-[#020617] min-h-full flex flex-col">
        {/* Toolbar */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800/80 sticky top-0 bg-[#020617] z-10">         
        {/* Left: Back Button */}
          <button 
            onClick={() => setSelectedEmail(null)}
            className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors px-2 py-1 rounded hover:bg-slate-800"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to Inbox
          </button>

          {/* Right: Mark as Unsafe Button */}
          <button 
            onClick={() => {
              // You can wire up your API call to mark this email as unsafe here!
              console.log(`Marking email ${selectedEmail.basic.id} as unsafe`);
            }}
            className="flex items-center gap-2 text-red-400 hover:text-red-300 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 transition-colors px-3 py-1.5 rounded text-sm font-medium"
          >
            Mark as Unsafe
            {/* Slashed Eye SVG positioned on the right */}
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
            </svg>
          </button>
        </div>

      {/* Email Content */}
        <div className="p-8 max-w-5xl">
          {/* ZAKY CHANGE THIS PLEASE TO MAKE IT CLOSE TO DESIGN DOC THANKS VERY MUCH */}
          <div className="mb-6">
            {isScanning && (
              <div className="flex items-center gap-2 text-blue-400 bg-blue-900/20 p-3 rounded-lg border border-blue-500/30 animate-pulse">
                <span className="animate-spin text-xl">⏳</span>
                <span>Analyzing content with AI...</span>
              </div>
            )}

            {!isScanning && scanResult && (
              <div className={`flex items-center gap-3 p-4 rounded-lg border shadow-lg ${
                scanResult.verdict === 'Phishing' 
                  ? 'bg-red-950/40 border-red-500/50 text-red-200' 
                  : 'bg-green-950/40 border-green-500/50 text-green-200'
              }`}>
                <div className="text-3xl">
                  {scanResult.verdict === 'Phishing' ? '⚠️' : '🛡️'}
                </div>
                <div>
                  <h3 className="font-bold text-lg">
                    {scanResult.verdict === 'Phishing' ? "Warning: Phishing Detected" : "This email looks safe"}
                  </h3>
                  <p className="text-sm opacity-80">
                    AI Confidence: {(scanResult.confidence * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            )}
          </div>
          {/* === END OF AI SCAN BANNER === */}
          <h2 className="text-3xl font-normal text-white mb-6">
            {selectedEmail.basic.subject}
          </h2>
          
          <div className="flex items-start justify-between mb-8 border-b border-slate-800/80 pb-6">
            <div className="flex items-center gap-3">
              {/* Avatar */}
              <div className="h-10 w-10 rounded-full bg-blue-900/50 text-blue-300 flex items-center justify-center font-bold text-lg border border-blue-800/50">
                {formatSender(selectedEmail.basic.from).charAt(0)}
              </div>
              <div>
                <div className="font-bold text-slate-200 text-sm">
                  {selectedEmail.basic.from}
                </div>
                <div className="text-xs text-slate-400">
                  to {selectedEmail.basic.to || 'me'}
                </div>
              </div>
            </div>

            {/* Date and Header Toggle Container */}
            <div className="flex flex-col items-end gap-1">
              <div className="text-sm text-slate-400">
                {selectedEmail.basic.date}
              </div>
              <button 
                onClick={() => setShowHeadersOnly(!showHeadersOnly)}
                className="text-xs text-blue-400 hover:text-blue-300 hover:underline transition-colors focus:outline-none"
              >
                {showHeadersOnly ? "Hide Email Header" : "View Email Header"}
              </button>
            </div>
          </div>

          {/* Conditionally Render the Raw Headers */}
          {showHeadersOnly && (
            <div className="mb-8 p-4 bg-slate-900 rounded-lg border border-slate-700 overflow-x-auto shadow-inner">
              <div className="text-xs text-slate-500 mb-2 font-bold uppercase tracking-wider">Raw Email Headers</div>
              <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap">
                {JSON.stringify(selectedEmail.headers, null, 2)}
              </pre>
            </div>
          )}

          {/* Email Body */}
          <div 
            className="text-slate-300 text-sm leading-relaxed max-w-none"
            dangerouslySetInnerHTML={{ __html: selectedEmail.basic.body }}
          />
        </div>
      </div>
    );
  }

  // ==========================================
  // VIEW 2: EMAIL LIST (INBOX VIEW)
  // ==========================================
  return (
    <div className="bg-[#0F172A] min-h-full">
      {/* Email List */}
     <div className="flex flex-col">
        {/* Notice we added 'index' here 👇 */}
        {/* 👇 Here is the magic! We use a template literal to swap the background color */}
        {emails.map((email, index) => (
          <div 
            key={email.id} 
            onClick={() => openEmail(email.id)}
            className={`group flex items-center gap-4 px-4 py-2.5 border-b border-slate-800/80 hover:bg-slate-800/60 hover:shadow-sm transition-all cursor-pointer ${
              index % 2 === 0 ? 'bg-[#020617]' : 'bg-[#0F172A]'
            }`}
          >
            
            {/* Left Actions: Hidden*/}
            <div className="flex items-center gap-3 text-slate-500">
              <input 
                type="checkbox" 
                className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500 cursor-pointer"
                onClick={(e) => e.stopPropagation()} 
              />
              {/* Changed hover color to a light slate, and swapped the SVG path */}
              <button 
                className="hover:text-slate-300 transition-colors focus:outline-none"
                onClick={(e) => {
                  e.stopPropagation();
                  // You can add your logic to hide the email here later!
                  console.log(`Hiding email ${email.id}`);
                }}
                title="Hide this email"
              >
                {/* Heroicons 'eye-slash' SVG */}
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                </svg>
              </button>
            </div>

            {/* Sender Name */}
            <div className="w-48 font-bold text-slate-200 truncate text-sm">
              {formatSender(email.from)}
            </div>

            {/* Subject and Snippet */}
            <div className="flex-1 truncate text-sm">
              <span className="font-bold text-slate-200">{email.subject}</span>
              <span className="text-slate-500 mx-2">-</span>
              <span className="text-slate-400">{email.snippet}</span>
            </div>

            {/* Date */}
            <div className="w-20 text-right text-sm font-bold text-slate-300 whitespace-nowrap">
              {formatDate(email.date)}
            </div>

          </div>
        ))}
      </div>
    </div>
  );
}

export default Inbox;