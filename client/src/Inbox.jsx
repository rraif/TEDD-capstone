import { useEffect, useState } from 'react';

const Inbox = ({viewType ='inbox', apiEndpoint = '/api/emails'}) => {
  const [emails, setEmails] = useState(null);
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [showHeadersOnly, setShowHeadersOnly] = useState(false); 
  const [scanResult, setScanResult] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const apiURL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

  // 🛡️ BULLETPROOF FETCH: Prevents the White Screen of Death
  useEffect(() => {
    setEmails(null);
    setSelectedEmail(null);
    fetch(`${apiURL}${apiEndpoint}`, { credentials: 'include' })
      .then(res => res.json())
      .then(data => {
        if (data.error) {
          console.error("API Error:", data.error);
          setEmails([]); // Fall back to empty array to prevent .map() crashes!
        } else if (data.emails){
          setEmails(data.emails);
        } else if (Array.isArray(data)) {
          setEmails(data);
        } else {
          setEmails([]);
        }
      })
      .catch(err => {
        console.error("Fetch Error:", err);
        setEmails([]);
      });
  }, [apiURL, apiEndpoint]);

  const handleHideEmail = async (e, id) => {
      e.stopPropagation(); 
      setEmails(prev => prev.filter(email => email.id !== id));
      try {
        await fetch(`${apiURL}/api/emails/hide`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ emailId: id }),
          credentials: 'include'
        });
      } catch (err) {
        console.error("Failed to hide email", err);
      }
    };

  const handleUnhideEmail = async (e, id) => {
    e.stopPropagation();
    setEmails(prev => prev.filter(email => email.id !== id));
    try {
      await fetch(`${apiURL}/api/emails/unhide`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ emailId: id }),
        credentials: 'include'
      });
    } catch (err) {
      console.error("Failed to unhide email", err);
    }
  };

  const openEmail = async (emailPreview) => {
    try {
      setScanResult(null);
      setIsScanning(true);
      setShowHeadersOnly(false);

      // 🚀 SKELETON LOADER: Instant transition using list data!
      setSelectedEmail({
        basic: {
          id: emailPreview.id,
          subject: emailPreview.subject,
          from: emailPreview.from,
          date: emailPreview.date,
          to: 'Loading...', 
          body: `
            <div class="animate-pulse space-y-4 pt-4">
              <div class="h-4 bg-slate-800 rounded w-3/4"></div>
              <div class="h-4 bg-slate-800 rounded w-full"></div>
              <div class="h-4 bg-slate-800 rounded w-5/6"></div>
              <div class="h-4 bg-slate-800 rounded w-1/2"></div>
            </div>
          `
        },
        headers: []
      });

      const res = await fetch(`${apiURL}/api/emails/${emailPreview.id}`, { credentials: 'include' });
      const fullData = await res.json();
      
      setSelectedEmail(fullData);

      // AI Scanner
      fetch(`${apiURL}/api/scan`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ emailId: emailPreview.id }),
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

  if (!emails) {
    return (
      <div className="bg-[#0F172A] min-h-full">
        <div className="flex flex-col">
          {[...Array(25)].map((_, i) => (
            <div 
              key={i} 
              className={`flex items-center gap-4 px-4 py-3 border-b border-slate-800/80 animate-pulse ${
                i % 2 === 0 ? 'bg-[#020617]' : 'bg-[#0F172A]'
              }`}
            >
              {/* Checkbox Placeholder */}
              <div className="w-4 h-4 rounded bg-slate-700/40"></div>
              
              {/* Sender Placeholder */}
              <div className="w-48 h-4 bg-slate-700/40 rounded"></div>
              
              {/* Subject & Snippet Placeholder */}
              <div className="flex-1 flex items-center gap-3">
                <div className="h-4 w-1/3 bg-slate-600/40 rounded"></div>
                <div className="h-4 w-1/2 bg-slate-800/60 rounded"></div>
              </div>

              {/* Date Placeholder */}
              <div className="w-16 h-4 bg-slate-700/40 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ==========================================
  // VIEW 1: SINGLE EMAIL (DETAIL VIEW)
  // ==========================================
  if (selectedEmail) {
    return (
      <div className="bg-[#020617] min-h-full flex flex-col">
        {/* Top Navigation Bar */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800/80 sticky top-0 bg-[#020617] z-20 shadow-md">         
          <button 
            onClick={() => setSelectedEmail(null)}
            className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors px-2 py-1 rounded hover:bg-slate-800"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Back to {viewType === 'inbox' ? 'Inbox' : 'Hidden List'}
          </button>

          {viewType === 'hidden' ? (
            <button 
              onClick={(e) => {
                handleUnhideEmail(e, selectedEmail.basic.id);
                setSelectedEmail(null); 
              }}
              className="flex items-center gap-2 text-green-400 hover:text-green-300 bg-green-500/10 hover:bg-green-500/20 border border-green-500/20 transition-colors px-3 py-1.5 rounded text-sm font-medium"
            >
              Restore to Inbox
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
          ) : (
            <button 
              onClick={(e) => {
                handleHideEmail(e, selectedEmail.basic.id);
                setSelectedEmail(null); 
              }}
              className="flex items-center gap-2 text-red-400 hover:text-red-300 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 transition-colors px-3 py-1.5 rounded text-sm font-medium"
            >
              Mark as Unsafe
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
              </svg>
            </button>
          )}
        </div> 

        {/* 🚀 THE NEW SPLIT LAYOUT */}
        <div className="p-8 max-w-full mx-auto flex flex-col xl:flex-row gap-8 items-start w-full">
          
          {/* LEFT COLUMN: The actual email content */}
          <div className="flex-1 min-w-0 w-full xl:w-[calc(100%-320px)]">
            <h2 className="text-3xl font-normal text-white mb-6 break-words">
              {selectedEmail.basic.subject}
            </h2>
            
            <div className="flex items-start justify-between mb-8 border-b border-slate-800/80 pb-6">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 shrink-0 rounded-full bg-blue-900/50 text-blue-300 flex items-center justify-center font-bold text-lg border border-blue-800/50">
                  {formatSender(selectedEmail.basic.from).charAt(0)}
                </div>
                <div className="min-w-0">
                  <div className="font-bold text-slate-200 text-sm truncate">
                    {selectedEmail.basic.from}
                  </div>
                  <div className="text-xs text-slate-400 truncate">
                    to {selectedEmail.basic.to || 'me'}
                  </div>
                </div>
              </div>

              <div className="flex flex-col items-end gap-1 shrink-0 ml-4">
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

            {showHeadersOnly && (
              <div className="mb-8 p-5 bg-[#020617] rounded-lg border border-slate-800 overflow-x-auto shadow-inner">
                <div className="text-xs text-slate-500 mb-4 font-bold uppercase tracking-wider border-b border-slate-800 pb-2">
                  Original Message Headers
                </div>
                
                <div className="text-xs font-mono flex flex-col gap-1.5 min-w-[600px] mb-8">
                  {selectedEmail.headers.map((header, index) => {
                    const authenticValue = header.value.replace(/(\s{2,}|\t+)/g, '\n$1'); 
                    return (
                      <div key={index} className="grid grid-cols-[160px_1fr] gap-4 hover:bg-slate-800/50 p-1 rounded transition-colors">
                        <div className="text-slate-400 font-semibold text-right mt-0.5">
                          {header.name}:
                        </div>
                        <div className="text-slate-200 break-words whitespace-pre-wrap leading-relaxed">
                          {authenticValue}
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="text-xs text-slate-500 mb-4 font-bold uppercase tracking-wider border-b border-slate-800 pb-2">
                  Raw MIME Payload
                </div>
                <pre className="text-xs text-slate-400 font-mono whitespace-pre-wrap break-words leading-relaxed min-w-[600px]">
                  {selectedEmail.rawMimeBody}
                </pre>
              </div>
            )}

            <div className="p-5 bg-[#020617] rounded-lg border border-slate-800 overflow-x-auto shadow-inner mb-8">
              <div className="text-xs text-slate-500 mb-4 font-bold uppercase tracking-wider border-b border-slate-800 pb-2">
                Message Content
              </div>
              <div 
                className="bg-white text-black p-6 rounded-md text-sm leading-relaxed max-w-none break-words"
                dangerouslySetInnerHTML={{ __html: selectedEmail.basic.body }}
              />
            </div>
          </div>

          {/* RIGHT COLUMN: The AI Security Inspector Panel */}
          <div className="w-full xl:w-80 shrink-0 sticky top-20">
            <h3 className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-4 border-b border-slate-800/80 pb-2">
              Security Analysis
            </h3>

            {isScanning && (
              <div className="flex flex-col items-center justify-center gap-5 text-blue-400 bg-blue-900/20 p-8 rounded-lg border border-blue-500/30 text-center">
                {/* Replaced the hourglass emoji with a professional SVG spinner */}
                <svg className="animate-spin h-10 w-10 text-blue-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <div className="space-y-2 animate-pulse">
                  <div className="font-bold">Scanning Payload</div>
                  <div className="text-xs opacity-70">Running BERT Model...</div>
                </div>
              </div>
            )}

            {!isScanning && scanResult && (
              <>
                {/* 1. The Main Verdict Card (Emojis Removed) */}
                <div className={`flex flex-col items-center p-6 rounded-lg border shadow-lg text-center ${
                  scanResult.verdict === 'Phishing' 
                    ? 'bg-red-950/40 border-red-500/50 text-red-200' 
                    : 'bg-green-950/40 border-green-500/50 text-green-200'
                }`}>
                  <h3 className="font-bold text-xl mb-3">
                    {scanResult.verdict === 'Phishing' ? "Phishing Detected" : "Looks Safe"}
                  </h3>
                  <div className="text-sm opacity-90 font-mono bg-black/20 px-4 py-1.5 rounded border border-white/10">
                    Confidence: {(scanResult.confidence * 100).toFixed(1)}%
                  </div>
                </div>

                {/* 2. The Explainable AI Placeholder Box (Emojis Removed) */}
                {scanResult.verdict === 'Phishing' && (
                  <div className="mt-4 bg-[#020617] border border-slate-800 rounded-lg p-5 shadow-lg relative overflow-hidden">
                    <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 to-blue-500 opacity-50"></div>
                    
                    <div className="mb-3 text-purple-400 font-bold text-xs uppercase tracking-wider mt-1">
                      Phishing Explanation
                    </div>
                    
                    <p className="text-slate-400 text-sm leading-relaxed">
                      Explanation Goes here
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  // ==========================================
  // VIEW 2: EMAIL LIST (INBOX VIEW)
  // ==========================================
  return (
    <div className="bg-[#0F172A] min-h-full">
     <div className="flex flex-col">
        {emails.length === 0 ? (
          <div className="text-center p-12 text-slate-500 border border-slate-800 border-dashed rounded-xl m-8">
            {viewType === 'hidden' ? "No hidden emails!" : "Your inbox is completely empty!"}
          </div>
        ) : (
          emails.map((email, index) => (
            <div 
              key={email.id} 
              onClick={() => openEmail(email)}
              className={`group flex items-center gap-4 px-4 py-2.5 border-b border-slate-800/80 hover:bg-slate-800/60 hover:shadow-sm transition-all cursor-pointer ${
                index % 2 === 0 ? 'bg-[#020617]' : 'bg-[#0F172A]'
              }`}
            >
              <div className="flex items-center gap-3 text-slate-500">
                <input 
                  type="checkbox" 
                  className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-blue-500 focus:ring-blue-500 cursor-pointer"
                  onClick={(e) => e.stopPropagation()} 
                />
              </div>

              <div className="w-48 font-bold text-slate-200 truncate text-sm">
                {formatSender(email.from)}
              </div>

              <div className="flex-1 truncate text-sm">
                <span className="font-bold text-slate-200">{email.subject}</span>
                <span className="text-slate-500 mx-2">-</span>
                <span className="text-slate-400">{email.snippet}</span>
              </div>

              <div className="w-20 text-right text-sm font-bold text-slate-300 whitespace-nowrap">
                {formatDate(email.date)}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default Inbox;