import React from 'react';

const NetraHeaderLogo = () => {
  return (
    <div className="flex items-center gap-3">
      {/* Yahan class me rounded-full aur object-cover add kiya hai */}
      <img 
        src="/netra-logo.png" 
        alt="Netra Logo" 
        className="w-10 h-10 object-cover rounded-full drop-shadow-[0_0_12px_rgba(34,211,238,0.4)]"
      />
      <h1 className="font-black font-mono netra-logo text-cyan-400">
        <span className="text-2xl">N</span>
        <span className="text-xl">ETR</span>
        <span className="text-2xl">A</span>
      </h1>
    </div>
  );
};

export default NetraHeaderLogo;