import React from "react";

import { exportConversation } from "../services/api";

const ExportButton = ({ sessionId }) => {
    const handleExportChat = async () => {
        const currentSessionId = sessionId;
        
        try {
            // Convert the incoming data into a File Blob
            const blob = await exportConversation(currentSessionId);
            
            // Create a temporary hidden URL for the Blob
            const url = window.URL.createObjectURL(blob);
            
            // Create an invisible HTML <a> tag, click it, and delete it
            const link = document.createElement("a");
            link.href = url;
            link.download = `Support_Transcript_${currentSessionId}.txt`;
            document.body.appendChild(link);
            link.click();
            
            // Clean up the temporary URL to save memory
            window.URL.revokeObjectURL(url);
            document.body.removeChild(link);

        } catch (error) {
            console.error("Error exporting chat:", error);
            alert("Could not export the conversation. Check the console for details.");
        }
    };

    return (
        <button
            onClick={handleExportChat}
            disabled={!sessionId}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded-md shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-blue-500"
            title="Download Chat Transcript"
        >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Export Chat
        </button>
    );
};

export default ExportButton;