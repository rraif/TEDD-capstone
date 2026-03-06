
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';


export default function Training() {

// --- NAVIGATION ---
  const navigate = useNavigate();


// --- STATE ---
  const [isTrainingActive, setIsTrainingActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentEmail, setCurrentEmail] = useState(null);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showHeadersOnly, setShowHeadersOnly] = useState(false);
  const [phishingIndicators, setPhishingIndicators] = useState("");

// --- HELPER FUNCTIONS (From Inbox) ---
  const formatSender = (fromHeader) => {
    if (!fromHeader) return "Unknown";
    return fromHeader.split(' <')[0].replace(/"/g, ''); 
  };

  const formatDate = (dateString) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };  

// --- HANDLERS ---
  const handleStartTraining = async () => {
    setIsTrainingActive(true); 
    setLoading(true);      
    setSelectedAnswer(null);       // Reset answers for new session
    setPhishingIndicators("");     // Reset text box for new session    

    try {
      const apiURL = import.meta.env.VITE_API_URL;
      
      // 1. Fetch the email list
      const response = await fetch(`${apiURL}/api/emails`, { credentials: 'include' });
      
      if (response.ok) {
        const data = await response.json();
        const emailsList = Array.isArray(data) ? data : (data.emails || []);

        if (emailsList.length > 0) {
          // 2. Pick a random email
          const randomEmail = emailsList[Math.floor(Math.random() * emailsList.length)];

          // 3. Set SKELETON LOADER instantly using the basic list data
          setCurrentEmail({
            basic: {
              id: randomEmail.id,
              subject: randomEmail.subject,
              from: randomEmail.from,
              date: randomEmail.date,
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

          // 4. Fetch the FULL email data (headers, raw MIME, etc.)
          const fullRes = await fetch(`${apiURL}/api/emails/${randomEmail.id}`, { credentials: 'include' });
          const fullData = await fullRes.json();
          setCurrentEmail(fullData);

        } else {
          // Fallback if inbox is empty
          setCurrentEmail({
            basic: {
              subject: "No Emails Found",
              from: "system@tedd.local",
              to: "me",
              body: "Your inbox is empty. We couldn't fetch a real email for this training session.",
              date: new Date().toISOString()
            },
            headers: []
          });
        }
      } else {
        throw new Error("Failed to fetch emails");
      }
    } catch (error) {
      console.error("Error fetching email:", error);
      setCurrentEmail({
        basic: {
          subject: "Connection Error",
          from: "system@tedd.local",
          to: "me",
          body: "Could not connect to the server to fetch an email. Please check your network.",
          date: new Date().toISOString()
        },
        headers: []
      });
    } finally {
      setLoading(false);
    }
  };

 const handleConfirm = () => {
    console.log("Verdict:", selectedAnswer);
    if (selectedAnswer === 'yes') {
      console.log("Indicators identified:", phishingIndicators);
    };
    // Add logic here to verify their answer
  };

// ==========================================
  // VIEW 1: ACTIVE TRAINING VIEW (Split Screen)
  // ==========================================
  if (isTrainingActive) {
    return (
      <div className="bg-[#020617] min-h-full flex flex-col overflow-y-auto">
        
        {/* Top Navigation Bar (Optional, gives them a way to back out) */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800/80 sticky top-0 bg-[#020617] z-20 shadow-md">         
          <button 
            onClick={() => { setIsTrainingActive(false); setCurrentEmail(null); setSelectedAnswer(null); }}
            className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors px-2 py-1 rounded hover:bg-slate-800"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Cancel Training
          </button>
        </div> 

        <div className="p-8 max-w-full mx-auto flex flex-col xl:flex-row gap-8 items-start w-full">
          
          {/* LEFT COLUMN: IDENTICAL INBOX EMAIL VIEWER */}
          <div className="flex-1 min-w-0 w-full xl:w-[calc(100%-320px)]">
            {currentEmail ? (
              <>
                <h2 className="text-3xl font-normal text-white mb-6 break-words">
                  {currentEmail.basic.subject}
                </h2>
                
                <div className="flex items-start justify-between mb-8 border-b border-slate-800/80 pb-6">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 shrink-0 rounded-full bg-blue-900/50 text-blue-300 flex items-center justify-center font-bold text-lg border border-blue-800/50">
                      {formatSender(currentEmail.basic.from).charAt(0)}
                    </div>
                    <div className="min-w-0">
                      <div className="font-bold text-slate-200 text-sm truncate">
                        {currentEmail.basic.from}
                      </div>
                      <div className="text-xs text-slate-400 truncate">
                        to {currentEmail.basic.to || 'me'}
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-1 shrink-0 ml-4">
                    <div className="text-sm text-slate-400">
                      {formatDate(currentEmail.basic.date)}
                    </div>
                    <button 
                      onClick={() => setShowHeadersOnly(!showHeadersOnly)}
                      className="text-xs text-blue-400 hover:text-blue-300 hover:underline transition-colors focus:outline-none"
                    >
                      {showHeadersOnly ? "Hide Email Header" : "View Email Header"}
                    </button>
                  </div>
                </div>

                {/* Email Headers (Toggleable) */}
                {showHeadersOnly && currentEmail.headers && (
                  <div className="mb-8 p-5 bg-[#020617] rounded-lg border border-slate-800 overflow-x-auto shadow-inner">
                    <div className="text-xs text-slate-500 mb-4 font-bold uppercase tracking-wider border-b border-slate-800 pb-2">
                      Original Message Headers
                    </div>
                    
                    <div className="text-xs font-mono flex flex-col gap-1.5 min-w-[600px] mb-8">
                      {currentEmail.headers.map((header, index) => {
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
                      {currentEmail.rawMimeBody || "Payload loading..."}
                    </pre>
                  </div>
                )}

                {/* Main Email Body */}
                <div className="p-5 bg-[#020617] rounded-lg border border-slate-800 overflow-x-auto shadow-inner mb-8">
                  <div className="text-xs text-slate-500 mb-4 font-bold uppercase tracking-wider border-b border-slate-800 pb-2">
                    Message Content
                  </div>
                  <div 
                    className="bg-white text-black p-6 rounded-md text-sm leading-relaxed max-w-none break-words"
                    dangerouslySetInnerHTML={{ __html: currentEmail.basic.body }}
                  />
                </div>
              </>
            ) : (
              <div className="text-slate-400 mt-10">Fetching random email...</div>
            )}
          </div>

          {/* RIGHT COLUMN: TRAINING PROMPT */}
          <div className="w-full xl:w-80 shrink-0 sticky top-20">
            <h3 className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-4 border-b border-slate-800/80 pb-2">
              Training Session
            </h3>

            <div className="bg-[#0F172A] border border-slate-700 rounded-lg p-6 shadow-2xl flex flex-col">
              <p className="text-lg font-medium text-slate-200 mb-6 leading-relaxed">
                Is this a phishing email?
              </p>
              
              <div className="flex gap-4 mb-8">
                <button 
                  onClick={() => setSelectedAnswer('yes')}
                  className={`flex-1 py-3 rounded-lg font-semibold transition-all duration-200 ${
                    selectedAnswer === 'yes' 
                      ? 'bg-red-600 text-white ring-2 ring-red-500 ring-offset-2 ring-offset-[#0F172A]' 
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
                  }`}
                >
                  Yes
                </button>
                
                <button 
                  onClick={() => setSelectedAnswer('no')}
                  className={`flex-1 py-3 rounded-lg font-semibold transition-all duration-200 ${
                    selectedAnswer === 'no' 
                      ? 'bg-emerald-600 text-white ring-2 ring-emerald-500 ring-offset-2 ring-offset-[#0F172A]' 
                      : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
                  }`}
                >
                  No
                </button>
              </div>

              {/* NEW CONDITIONAL TEXT BOX */}
              {selectedAnswer === 'yes' && (
                <div className="mb-8 animate-in fade-in slide-in-from-top-2 duration-300">
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Enter Indicators of Phishing
                  </label>
                  <textarea
                    className="w-full bg-slate-900/50 border border-slate-600 rounded-lg p-3 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent resize-none h-28"
                    placeholder="e.g., Suspicious sender address, sense of urgency, fake link..."
                    value={phishingIndicators}
                    onChange={(e) => setPhishingIndicators(e.target.value)}
                  />
                </div>
              )}

              <button 
                disabled={!selectedAnswer}
                onClick={handleConfirm}
                className={`w-full py-4 rounded-lg font-bold text-white transition-all duration-200 ${
                  selectedAnswer 
                    ? 'bg-blue-600 hover:bg-blue-500 shadow-[0_0_15px_rgba(37,99,235,0.4)] mt-auto' 
                    : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700 mt-auto'
                }`}
              >
                Confirm
              </button>
            </div>
          </div>

        </div>
      </div>
    );
  }
  



  return (
   <div className="flex flex-col items-center justify-start h-full p-2 pt-32 bg-slate-950 relative overflow-hidden">
      
        {/*Background light orbs*/}
      <div className="max-w-2xl w-full bg-slate-800 p-10 rounded-xl shadow-sm border border-slate-700 text-center">
        
        <div className="absolute -top-20 -left-20 w-96 h-96 bg-blue-600/30 rounded-full blur-[100px] pointer-events-none"></div>
      
      
         <div className="absolute top-1/2 -right-20 w-[30rem] h-[30rem] bg-indigo-500/20 rounded-full blur-[120px] pointer-events-none"></div>
      {/* -------------------------------- */}


        <h1 className="text-5xl font-bold text-white mb-8 leading-15">
          Are you ready to start your training?
        </h1>

        <div className="flex flex-col gap-4">
          <button 
            className="w-3/4 mx-auto text-2xl bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-colors duration-200"
            onClick={handleStartTraining}
          >
            Yes
          </button>
          
          <button 
            className="w-3/4 mx-auto text-2xl bg-slate-700 hover:bg-slate-600 text-slate-200 font-bold py-3 px-6 rounded-lg transition-colors duration-200"
            onClick={() => navigate('/inbox')}
          >
            No
          </button>
        </div>
      </div>

        <div className="max-w-2xl w-full mt-6 px-6 z-10">
                <h2 className="text-xl font-bold text-slate-200 mb-4">
                What you have to do:
                </h2>
                
                {/* 'list-disc' creates bullet points, 'space-y-3' adds vertical space between them */}
                <ul className="list-disc list-inside text-slate-300 space-y-3 text-lg">
                <li>Find out if it’s a phishing email or not</li>
                <li>If it’s a phishing email, provide as many reasons as you can why it’s a phishing email</li>
                </ul>
            </div>


        <div className="absolute bottom-8 px-6 text-center w-full">
            <p className="text-sm text-slate-500 italic">
            *The training system will use your inbox data to create a localized phishing email.
            </p>
        </div>





    </div>

  );
}