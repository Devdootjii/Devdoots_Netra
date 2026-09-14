import React from 'react';

const NetraFooter = () => {
  
  // Hackathon demo ke liye ek dummy click handler
  const handleDemoClick = (e, pageName) => {
    e.preventDefault(); // Page ko refresh hone se rokne ke liye
    alert(`[Demo Mode] The ${pageName} page is currently unavailable in this hackathon build.`);
  };

  return (
    <footer className="w-full border-t border-slate-800/80 bg-[#0a0f1c] py-6 mt-auto">
      <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-slate-400 font-mono">
        
        {/* Logo & Copyright */}
        <div className="flex items-center gap-2">
          <img src="/netra-logo.png" alt="Netra Icon" className="w-5 h-5 rounded-full opacity-80" />
          <span>© 2026 Project Netra (Team Devdoots).</span>
        </div>

        {/* Links */}
        <div className="flex flex-wrap justify-center gap-x-6 gap-y-2">
          
          {/* Dummy Demo Links */}
          <a href="#" onClick={(e) => handleDemoClick(e, 'Terms')} className="hover:text-[#22d3ee] transition-colors">Terms</a>
          <a href="#" onClick={(e) => handleDemoClick(e, 'Privacy')} className="hover:text-[#22d3ee] transition-colors">Privacy</a>
          <a href="#" onClick={(e) => handleDemoClick(e, 'Security')} className="hover:text-[#22d3ee] transition-colors">Security</a>
          
          {/* Actual Working Links (Target Blank se naye tab me khulenge) */}
          <a href="https://github.com/Devdootjii/Devdoots_Netra" target="_blank" rel="noreferrer" className="hover:text-[#22d3ee] transition-colors">Docs</a>
          {/* 👇 NAYA DISCORD LINK YAHAN HAI 👇 */}
          <a href="https://discord.gg/QQmkrACta" target="_blank" rel="noreferrer" className="hover:text-[#22d3ee] transition-colors">Discord</a>
          
          {/* Email Contact Link */}
          <a href="mailto:kdivyansh@gamil.com?subject=Project Netra Query" className="hover:text-[#22d3ee] transition-colors">Contact</a>
          
          <a href="#" onClick={(e) => handleDemoClick(e, 'Cookie Preferences')} className="hover:text-[#22d3ee] transition-colors">Manage cookies</a>
        </div>

      </div>
    </footer>
  );
};

export default NetraFooter;