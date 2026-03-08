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
  const [currentUser, setCurrentUser] = useState(null);
  
  // Checklist State
  const [selectedFlags, setSelectedFlags] = useState([]);
  
  // Gamification State
  const [isActualPhishing, setIsActualPhishing] = useState(false);
  const [feedback, setFeedback] = useState(null);

  // --- CHECKLIST CONFIG ---
  const CHECKLIST_OPTIONS = [
    { id: 'mismatched_sender', label: 'Mismatched Sender or Reply-To Address' },
    { id: 'urgency', label: 'Sense of Urgency or Threats' },
    { id: 'suspicious_link', label: 'Suspicious Link or Fake Login' },
    { id: 'financial_request', label: 'Request for Money, Wire, or Gift Cards' }
  ];

  // --- HELPER FUNCTIONS ---
  const formatSender = (fromHeader) => {
    if (!fromHeader) return "Unknown";
    return fromHeader.split(' <')[0].replace(/"/g, ''); 
  };

  const formatDate = (dateString) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };  

  const toggleFlag = (flagId) => {
    setSelectedFlags(prev => 
      prev.includes(flagId) ? prev.filter(id => id !== flagId) : [...prev, flagId]
    );
  };

  // --- HANDLERS ---
  const handleStartTraining = async () => {
    setIsTrainingActive(true); 
    setLoading(true);      
    setSelectedAnswer(null);       
    setSelectedFlags([]); // Reset checklist     
    setFeedback(null); 
    setShowHeadersOnly(false);

    // Skeleton Loader
    setCurrentEmail({
      basic: {
        subject: 'Generating scenario...',
        from: 'AI Training Module',
        to: 'Loading...', 
        date: new Date().toISOString(),
        body: `
          <div class="animate-pulse space-y-4 pt-4">
            <div class="h-4 bg-slate-800 rounded w-3/4"></div>
            <div class="h-4 bg-slate-800 rounded w-full"></div>
            <div class="h-4 bg-slate-800 rounded w-5/6"></div>
            <div class="h-4 bg-slate-800 rounded w-1/2"></div>
          </div>
        `
      },
      headers: {}
    });

    try {
      const apiURL = import.meta.env.VITE_API_URL;
      const response = await fetch(`${apiURL}/api/training/generate`, { 
        method: 'POST',
        credentials: 'include' 
      });
      
      if (response.ok) {
        const data = await response.json();
        setIsActualPhishing(data.isPhishing);
        setCurrentEmail({
          basic: data.email, 
          headers: data.headers || {} 
        });
      } else {
        throw new Error("Failed to fetch training email");
      }
    } catch (error) {
      console.error("Error fetching email:", error);
      setCurrentEmail({
        basic: {
          subject: "Generation Error",
          from: "system@tedd.local",
          to: "me",
          body: "Could not connect to the AI engine to generate a scenario.",
          date: new Date().toISOString()
        },
        headers: {}
      });
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    const guessedPhishing = selectedAnswer === 'yes';
    const isCorrect = guessedPhishing === isActualPhishing;
    
    let earnedPoints = 0;
    let resultMessage = "";
    let missedFeedback = []; 
    let incorrectFeedback = []; 

    if (isCorrect) {
      if (isActualPhishing) {
        const aiFlags = currentEmail.basic.redFlags || [];
        
        // Calculate correct, missed, and incorrect flags
        const correctFlagsFound = selectedFlags.filter(f => aiFlags.includes(f)).length;
        const missedFlagsIds = aiFlags.filter(f => !selectedFlags.includes(f));
        const incorrectFlagsIds = selectedFlags.filter(f => !aiFlags.includes(f)); 
        
        missedFeedback = missedFlagsIds.map(id => CHECKLIST_OPTIONS.find(opt => opt.id === id)?.label);
        incorrectFeedback = incorrectFlagsIds.map(id => CHECKLIST_OPTIONS.find(opt => opt.id === id)?.label);
        
        // Math: +10 for correct flag, -5 for missed flag, -5 for incorrect flag. (Floor at 10 points)
        const penalties = (missedFlagsIds.length * 5) + (incorrectFlagsIds.length * 5);
        earnedPoints = Math.max(10, 50 + (correctFlagsFound * 10) - penalties);
        
        if (missedFeedback.length === 0 && incorrectFeedback.length === 0) {
            resultMessage = `✅ Perfect! You caught the attack and accurately spotted all ${aiFlags.length} red flags.`;
        } else {
            resultMessage = `✅ Good job catching the attack, but your flag analysis wasn't perfect.`;
        }
      } else {
        earnedPoints = 50;
        resultMessage = "✅ Correct! You successfully identified this as a safe email.";
      }
    } else {
      earnedPoints = 0;
      resultMessage = `❌ Incorrect. This was actually a ${isActualPhishing ? 'phishing attack' : 'safe email'}.`;
    }
    
    setFeedback({
      isCorrect,
      message: resultMessage,
      missedFlags: missedFeedback,
      incorrectFlags: incorrectFeedback,
      earnedPoints: earnedPoints 
    });

    try {
      const apiURL = import.meta.env.VITE_API_URL;
      await fetch(`${apiURL}/api/users/score`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ 
          won: isCorrect,
          pointsToAward: earnedPoints 
        })
      });
    } catch (error) {
      console.error("Failed to update score:", error);
    }
  };

  // ==========================================
  // VIEW 1: ACTIVE TRAINING VIEW
  // ==========================================
  if (isTrainingActive) {
    return (
      <div className="bg-[#020617] min-h-full flex flex-col overflow-y-auto">
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800/80 sticky top-0 bg-[#020617] z-20 shadow-md">         
          <button 
            onClick={() => { setIsTrainingActive(false); setCurrentEmail(null); setSelectedAnswer(null); setFeedback(null); }}
            className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors px-2 py-1 rounded hover:bg-slate-800"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Cancel Training
          </button>
        </div> 

        <div className="p-8 max-w-full mx-auto flex flex-col xl:flex-row gap-8 items-start w-full">
          {/* LEFT COLUMN: EMAIL VIEWER */}
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
                  
                  {/* Header Toggle */}
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

                {/* Header Viewer Section */}
                {showHeadersOnly && (
                  <div className="mb-8 p-5 bg-[#020617] rounded-lg border border-slate-800 overflow-x-auto shadow-inner">
                    <div className="text-xs text-slate-500 mb-4 font-bold uppercase tracking-wider border-b border-slate-800 pb-2">
                      Original Message Headers
                    </div>
                    
                    <div className="text-xs font-mono flex flex-col gap-1.5 min-w-[600px] mb-2">
                      {Object.entries(currentEmail.headers || {}).map(([key, val]) => {
                        return (
                          <div key={key} className="grid grid-cols-[160px_1fr] gap-4 hover:bg-slate-800/50 p-1 rounded transition-colors">
                            <div className="text-slate-400 font-semibold text-right mt-0.5">
                              {key}:
                            </div>
                            <div className="text-slate-200 break-words whitespace-pre-wrap leading-relaxed">
                              {val}
                            </div>
                          </div>
                        );
                      })}
                    </div>
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
              <div className="text-slate-400 mt-10">Fetching scenario...</div>
            )}
          </div>

          {/* RIGHT COLUMN: TRAINING PROMPT */}
          <div className="w-full xl:w-80 shrink-0 sticky top-20">
            <h3 className="text-slate-500 text-xs font-bold uppercase tracking-wider mb-4 border-b border-slate-800/80 pb-2">
              Training Session
            </h3>

            <div className="bg-[#0F172A] border border-slate-700 rounded-lg p-6 shadow-2xl flex flex-col">
              {feedback ? (
                <div className={`mb-6 p-4 rounded-lg border ${feedback.isCorrect ? 'bg-green-900/30 border-green-500/50 text-green-200' : 'bg-red-900/30 border-red-500/50 text-red-200'}`}>
                  <p className="font-bold mb-3">{feedback.message}</p>
                  
                  {/* Display missed flags (yellow warning) */}
                  {feedback.missedFlags && feedback.missedFlags.length > 0 && (
                    <div className="mb-3">
                      <span className="text-xs font-bold uppercase tracking-wider text-amber-500">Missed Flags:</span>
                      <ul className="list-disc list-inside text-sm mt-1 space-y-1 ml-1 text-amber-200/80">
                        {feedback.missedFlags.map((flag, idx) => (
                          <li key={idx}>{flag}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Display incorrectly checked flags (red penalty) */}
                  {feedback.incorrectFlags && feedback.incorrectFlags.length > 0 && (
                    <div className="mb-3">
                      <span className="text-xs font-bold uppercase tracking-wider text-red-400">Incorrectly Flagged (Penalty):</span>
                      <ul className="list-disc list-inside text-sm mt-1 space-y-1 ml-1 text-red-300/80">
                        {feedback.incorrectFlags.map((flag, idx) => (
                          <li key={idx}>{flag}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Points Display and Next Button */}
                  <div className="mt-4 pt-4 border-t border-slate-800/50 flex flex-col gap-3">
                    <div className="flex justify-between items-center bg-slate-900/50 px-3 py-2 rounded">
                      <span className="text-sm font-semibold text-slate-300">Points Earned:</span>
                      <span className={`font-bold font-mono ${feedback.earnedPoints > 0 ? 'text-green-400' : 'text-slate-500'}`}>
                        +{feedback.earnedPoints} XP
                      </span>
                    </div>
                    
                    <button 
                      onClick={handleStartTraining}
                      className="w-full py-2 bg-slate-800 hover:bg-slate-700 rounded text-sm text-white transition-colors border border-slate-600"
                    >
                      Next Scenario ➔
                    </button>
                  </div>

                </div>
              ) : (
                <>
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

                  {selectedAnswer === 'yes' && (
                    <div className="mb-8 animate-in fade-in slide-in-from-top-2 duration-300">
                      <label className="block text-sm font-medium text-slate-300 mb-3">
                        What makes this suspicious? (Select all that apply)
                      </label>
                      <div className="flex flex-col gap-2">
                        {CHECKLIST_OPTIONS.map(option => (
                          <label 
                            key={option.id} 
                            className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                              selectedFlags.includes(option.id) 
                                ? 'bg-red-900/20 border-red-500/50 text-slate-200' 
                                : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:bg-slate-800'
                            }`}
                          >
                            <input 
                              type="checkbox" 
                              className="w-4 h-4 rounded border-slate-600 bg-slate-900 text-red-500 focus:ring-red-500 focus:ring-offset-slate-900"
                              checked={selectedFlags.includes(option.id)}
                              onChange={() => toggleFlag(option.id)}
                            />
                            <span className="text-sm font-medium">{option.label}</span>
                          </label>
                        ))}
                      </div>
                    </div>
                  )}

                  <button 
                    disabled={!selectedAnswer || loading}
                    onClick={handleConfirm}
                    className={`w-full py-4 rounded-lg font-bold text-white transition-all duration-200 ${
                      selectedAnswer 
                        ? 'bg-blue-600 hover:bg-blue-500 shadow-[0_0_15px_rgba(37,99,235,0.4)] mt-auto' 
                        : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700 mt-auto'
                    }`}
                  >
                    Confirm
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }
  
  // ==========================================
  // VIEW 2: SPLASH SCREEN
  // ==========================================
  return (
   <div className="flex flex-col items-center justify-start h-full p-2 pt-32 bg-slate-950 relative overflow-hidden">
      <div className="max-w-2xl w-full bg-slate-800 p-10 rounded-xl shadow-sm border border-slate-700 text-center z-10">
        <div className="absolute -top-20 -left-20 w-96 h-96 bg-blue-600/30 rounded-full blur-[100px] pointer-events-none -z-10"></div>
        <div className="absolute top-1/2 -right-20 w-[30rem] h-[30rem] bg-indigo-500/20 rounded-full blur-[120px] pointer-events-none -z-10"></div>

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
        <ul className="list-disc list-inside text-slate-300 space-y-3 text-lg">
          <li>Find out if it’s a phishing email or not</li>
          <li>If it’s a phishing email, select the reasons why using the checklist provided</li>
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