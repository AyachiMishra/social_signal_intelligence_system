import json
import asyncio
import os
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# --- 1. UPDATED DATA SCHEMA ---
# Matches the specific JSON input format provided
class Signal(BaseModel):
    synthetic_id: str
    timestamp: str
    raw_text: str
    source_type: str
    category: str
    generation_sequence: int
    pii_scrubbed_count: int
    scenario_category: str
    sentiment_score: float
    shadow_review_urgency: str
    is_flagged_for_review: bool
    target_department: str
    internal_action_draft: str
    
    # NEW FIELDS ADDED HERE
# NEW FIELDS ADDED HERE - Updated to allow Dict or Str to handle objects
    module3_explanation:  Optional[object] = None
    module3_impact_assessment: Optional[object] = None
    module3_suggested_action: str
    
    status: str = "Awaiting Approval" # internal state, defaults to awaiting

class ResolveSignalRequest(BaseModel):
    synthetic_id: str
    action: str  # 'approve' or 'decline'

# Global in-memory storage for audit logs (Problem 3)
audit_db = []

# --- NEW DATA MODELS FOR PR AGENT ---
class PRSignalRequest(BaseModel):
    synthetic_id: str
    raw_text: str
    scenario_category: str

class PRDecisionRequest(BaseModel):
    synthetic_id: str
    action: str  # 'approve' or 'reject'
    final_text: str
    category: str

# --- NEW MOCK PERSISTENCE FOR PR AGENT ---
# Stores the history of approved public posts
pr_history_db = []


# --- 2. UPDATED MOCK PERSISTENCE ---
signals_db: List[Signal] = [
    Signal(
        synthetic_id="SYN-2026-001",
        timestamp="2026-01-31 08:30:00",
        raw_text="Massive login failure on the app.",
        source_type="Twitter",
        category="Service Outage",
        generation_sequence=1,
        pii_scrubbed_count=0,
        scenario_category="Service or Incident Signals",
        sentiment_score=-0.85,
        shadow_review_urgency="Critical",
        is_flagged_for_review=True,
        target_department="IT Ops",
        internal_action_draft="Deploy bridge.",
        module3_explanation="High volume of reports indicating downtime.",
        module3_impact_assessment="Severe operational risk due to global login failure.",
        module3_suggested_action="Notify users immediately."
    ),
    Signal(
        synthetic_id="SYN-2026-002",
        timestamp="2026-01-31 10:45:00",
        raw_text="Suspicious SMS links claiming to offer Mashreq reward points.",
        source_type="Synthetic Forum",
        category="Fraud Alert",
        generation_sequence=46,
        pii_scrubbed_count=3,
        scenario_category="Fraud or Scam Rumors",
        sentiment_score=-0.72,
        shadow_review_urgency="High",
        is_flagged_for_review=True,
        target_department="Fraud",
        internal_action_draft="Initiate takedown request.",
        module3_explanation="Detected pattern matching known phishing campaigns targeting loyalty programs.",
        module3_impact_assessment="High risk of customer financial loss and reputational damage.",
        module3_suggested_action="Block domain and issue app push notification."
    )
]

# --- HTML TEMPLATES ---
# 1. Dashboard
HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mashreq | Responsible Signal Intelligence</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>
        /* Global Font Increase by 15% */
        html { font-size: 115%; }
        body { font-family: 'Outfit', sans-serif; background-color: #f8fafc; }
        .mono { font-family: 'JetBrains Mono', monospace; }
        .executive-blur { backdrop-filter: blur(12px); background: rgba(15, 23, 42, 0.9); }
        .card-hover { transition: transform 0.2s, box-shadow 0.2s; }
        .card-hover:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); }
        
        /* Animation for removing cards */
        .fade-out-slide { animation: slideOut 0.4s forwards; }
        @keyframes slideOut {
            to { opacity: 0; transform: translateX(50px); height: 0; margin: 0; padding: 0; border: none; }
        }
    </style>
</head>
<body class="text-slate-900" onclick="closeMenuOnClickOutside(event)">

    <nav class="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center sticky top-0 z-40">
        <div class="flex items-center gap-4">
            <div class="w-10 h-10 bg-slate-900 rounded-xl flex items-center justify-center">
                <div class="w-5 h-5 border-2 border-white rounded-full animate-pulse"></div>
            </div>
            <div>
                <h1 class="text-lg font-bold tracking-tight">ADAN Intelligence <span class="text-blue-600">Pro</span></h1>
                <p class="text-[10px] text-slate-400 font-bold uppercase tracking-widest">Governance & Risk Oversight</p>
            </div>
        </div>

        <div class="flex items-center gap-6">
            <button onclick="openBriefing()" class="bg-slate-900 text-white px-5 py-2.5 rounded-full text-xs font-bold hover:bg-slate-800 transition-all flex items-center gap-2">
                <span class="font-mono">DOC</span> Executive Briefing
            </button>
            
            <div class="relative">
                <button id="menu-btn" onclick="toggleMenu(event)" class="text-xs font-bold uppercase text-slate-500 hover:text-slate-900 focus:outline-none flex items-center gap-1">
                    System Menu <span id="menu-arrow">▼</span>
                </button>
                <div id="dropdown-menu" class="absolute right-0 top-full mt-2 hidden w-64 bg-white border border-slate-200 shadow-xl rounded-2xl overflow-hidden py-2 z-50 transition-all duration-200 origin-top-right">
                    <a href="/" class="block px-4 py-3 text-xs font-semibold hover:bg-slate-50">Dashboard Overview</a>
                    <a href="/analytics" class="block px-4 py-3 text-xs font-semibold hover:bg-slate-50 border-t border-slate-100 text-blue-600">Advanced Analytics</a> 
                    <a href="/governance" class="block px-4 py-3 text-xs font-semibold hover:bg-slate-50 border-t border-slate-100">Governance & Audit Logs</a>
                    <a href="/ai-logic" class="block px-4 py-3 text-xs font-semibold hover:bg-slate-50 border-t border-slate-100">AI Logic Explanation</a>
                    <a href="/pr-agent" class="block px-4 py-3 text-xs font-semibold hover:bg-slate-50 border-t border-slate-100 text-purple-600">PR Response Agent</a>
                </div>
            </div>
        </div>
    </nav>

    <main class="p-8 max-w-[1600px] mx-auto">
        <div class="grid grid-cols-4 gap-6 mb-10">
            <div class="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm">
                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Active Signals</p>
                <h2 class="text-3xl font-extrabold" id="count-signals">--</h2>
            </div>
            <div class="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm">
                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Avg Sentiment</p>
                <h2 class="text-3xl font-extrabold text-red-500" id="avg-sentiment">--</h2>
            </div>
            <div class="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm">
                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Critical Alerts</p>
                <h2 class="text-2xl font-extrabold text-orange-500 uppercase" id="critical-count">--</h2>
            </div>
            <div class="bg-blue-600 p-5 rounded-3xl shadow-lg text-white">
                <p class="text-[10px] font-bold text-blue-100 uppercase tracking-widest mb-1">Human Actions</p>
                <h2 class="text-3xl font-extrabold" id="human-actions">0</h2>
            </div>
        </div>

        <div class="grid grid-cols-12 gap-8">
            <div class="col-span-8">
                <h3 class="text-xs font-black text-slate-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                    <span class="w-2 h-2 bg-green-500 rounded-full animate-ping"></span> Real-Time Intelligence Stream
                </h3>
                <div id="signal-container" class="space-y-6">
                    <p class="text-sm text-slate-400 animate-pulse">Syncing with Governance Module...</p>
                </div>
            </div>

<div class="col-span-4 space-y-8">
                <div class="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm">
                    <h3 class="text-xs font-black text-slate-400 uppercase tracking-widest mb-8">Risk Distribution</h3>
                    <canvas id="riskChart" height="250"></canvas>
                </div>
            </div>
        </div>
    </main>

    <div id="briefing-modal" class="fixed inset-0 z-50 executive-blur hidden flex items-center justify-center p-6">
        <div class="bg-white w-full max-w-lg rounded-[2rem] shadow-2xl overflow-hidden animate-in fade-in zoom-in duration-300">
            <div class="p-8" id="briefing-export-area">
                <div class="flex justify-between items-start mb-6">
                    <div>
                        <h2 class="text-2xl font-extrabold tracking-tight">Executive Briefing</h2>
                        <p class="text-slate-400 text-xs font-medium mt-1">Generated <span id="current-date"></span></p>
                    </div>
                    <button onclick="closeBriefing()" class="text-slate-300 hover:text-slate-900 text-xl font-light" data-html2canvas-ignore="true">✕</button>
                </div>
                
                <div class="space-y-6" id="briefing-content">
                </div>

                <div class="mt-8 pt-6 border-t border-slate-100 flex justify-between items-center">
                    <p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest italic">Confidential</p>
                    <button onclick="downloadPDF()" class="text-xs font-bold text-blue-600 hover:underline flex items-center gap-2" data-html2canvas-ignore="true">
                        <span class="text-lg">⬇</span> Download PDF
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        const container = document.getElementById('signal-container');
        let currentSignals = [];
        let deptChartInstance = null;
        let riskChartInstance = null;
        let menuOpen = false;

        // --- MENU TOGGLE LOGIC ---
        function toggleMenu(e) {
            e.stopPropagation();
            const menu = document.getElementById('dropdown-menu');
            const arrow = document.getElementById('menu-arrow');
            menuOpen = !menuOpen;
            
            if (menuOpen) {
                menu.classList.remove('hidden');
                arrow.innerText = '▲';
            } else {
                menu.classList.add('hidden');
                arrow.innerText = '▼';
            }
        }

        function closeMenuOnClickOutside(e) {
            const menu = document.getElementById('dropdown-menu');
            const btn = document.getElementById('menu-btn');
            if (menuOpen && !menu.contains(e.target) && !btn.contains(e.target)) {
                menu.classList.add('hidden');
                document.getElementById('menu-arrow').innerText = '▼';
                menuOpen = false;
            }
        }

        // --- CORE FUNCTION: FETCH JSON DATA ---
        async function loadDashboardData() {
            try {
                const response = await fetch('/api/analytics-data');
                currentSignals = await response.json();
                
                if(currentSignals.length > 0) {
                    renderSignals(currentSignals);
                    updateStats(currentSignals);
                    initDashboardCharts(currentSignals);
                } else {
                    container.innerHTML = '<p class="text-slate-500">No signals found in the database.</p>';
                }
            } catch (error) {
                console.error("Error fetching data:", error);
                container.innerHTML = '<p class="text-red-500">Error connecting to Governance Module.</p>';
            }
        }

// HELPER: Formats JSON objects into clean HTML lists
        function formatAIObject(data) {
            if (!data) return '<span class="text-slate-400">N/A</span>';
            if (typeof data === 'string') return data; // Handle legacy strings
            
            // Loop through keys (e.g., reputational_risk, Signal, Impact)
            return Object.entries(data).map(([key, val]) => `
                <div class="mb-1">
                    <span class="text-slate-400 uppercase text-[10px] font-bold mr-1">${key.replace(/_/g, ' ')}:</span>
                    <span class="text-slate-800">${val}</span>
                </div>
            `).join('');
        }

        function renderSignals(signals) {
            container.innerHTML = signals.map(s => `
                <div id="card-${s.synthetic_id}" class="bg-white p-8 rounded-[2rem] border border-slate-200 card-hover relative overflow-hidden transition-all duration-300">
                    <div class="flex justify-between items-start mb-6">
                        <div class="flex items-center gap-3">
                            <span class="mono text-[10px] font-bold bg-slate-100 text-slate-500 px-3 py-1.5 rounded-full">${s.synthetic_id}</span>
                            <span class="text-[10px] font-extrabold uppercase px-3 py-1.5 rounded-full ${getUrgencyClass(s.shadow_review_urgency)}">
                                ${s.shadow_review_urgency} Urgency
                            </span>
                        </div>
                        <span class="text-[15px] font-bold text-slate-300 uppercase">${s.timestamp}</span>
                    </div>

                    <p class="text-xl font-semibold leading-relaxed text-slate-800 mb-8">"${s.raw_text}"</p>
                    
                    <div class="bg-slate-50 rounded-2xl p-6 border border-slate-100 mb-8">
                        <div class="flex items-center gap-2 mb-3">
                            <span class="text-blue-600 font-mono font-bold">AI</span>
                            <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Module 3 Analysis & Action</p>
                        </div>
                        <div class="space-y-3">
                             <div class="text-xs font-bold text-slate-800">
                                ${formatAIObject(s.module3_impact_assessment)}
                             </div>
                             <div class="text-xs font-medium text-slate-600 italic border-t border-slate-200 pt-2 mt-2">
                                <span class="not-italic font-bold text-slate-400 block text-[9px] mb-1">REASONING MATRIX</span>
                                ${formatAIObject(s.module3_explanation)}
                             </div>
                             <div class="mt-3 pt-3 border-t border-slate-200">
                                <p class="text-sm font-bold text-blue-700">SUGGESTION: ${s.module3_suggested_action}</p>
                             </div>
                        </div>
                    </div>

                    <div class="flex justify-between items-center pt-6 border-t border-slate-100">
                        <div class="flex gap-6">
                            <div>
                                <p class="text-[9px] font-black text-slate-400 uppercase mb-1">Sentiment</p>
                                <p class="text-xs font-bold ${s.sentiment_score < 0 ? 'text-red-500' : 'text-green-500'}">${s.sentiment_score}</p>
                            </div>
                            <div>
                                <p class="text-[9px] font-black text-slate-400 uppercase mb-1">Target Dept</p>
                                <p class="text-xs font-bold text-slate-700">${s.target_department}</p>
                            </div>
                            <div>
                                <p class="text-[9px] font-black text-slate-400 uppercase mb-1">PII Scrubbed</p>
                                <p class="text-xs font-bold text-slate-700">${s.pii_scrubbed_count} entries</p>
                            </div>
                        </div>
                        
                        <div class="flex gap-3">
                            ${s.is_flagged_for_review ? `
                                <button onclick="approveAction('${s.synthetic_id}')" class="px-6 py-3 bg-slate-900 text-white text-[11px] font-bold uppercase rounded-xl hover:bg-slate-800 transition-all">Approve</button>
                                <button onclick="declineAction('${s.synthetic_id}')" class="px-6 py-3 border border-slate-200 text-slate-400 text-[11px] font-bold uppercase rounded-xl hover:bg-slate-50">Decline</button>
                            ` : `
                                <div class="flex items-center gap-2 text-slate-400 px-4 py-2 bg-slate-50 rounded-xl">
                                    <span class="text-[11px] font-bold uppercase">Auto-Archived</span>
                                </div>
                            `}
                        </div>
                    </div>
                </div>
            `).join('');
        }

        function getUrgencyClass(u) {
            if (u === 'Critical') return 'bg-red-50 text-red-600';
            if (u === 'High') return 'bg-orange-50 text-orange-600';
            if (u === 'Medium') return 'bg-yellow-50 text-yellow-600';
            return 'bg-blue-50 text-blue-600';
        }

        function updateStats(signals) {
            // Count
            document.getElementById('count-signals').innerText = signals.length.toString().padStart(2, '0');
            
            // Avg Sentiment
            const avg = signals.length ? (signals.reduce((a, b) => a + b.sentiment_score, 0) / signals.length) : 0;
            document.getElementById('avg-sentiment').innerText = avg.toFixed(2);
            
            // Critical Count
            const critical = signals.filter(s => s.shadow_review_urgency === 'Critical' || s.shadow_review_urgency === 'High').length;
            document.getElementById('critical-count').innerText = critical.toString().padStart(2, '0');
        }

async function removeCardAndRefresh(id, actionType) {
            // 1. Call Backend to update JSON and Audit Log (Problem 1 & 3)
            try {
                await fetch('/api/resolve-signal', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ synthetic_id: id, action: actionType })
                });
            } catch (e) {
                console.error("Failed to sync status", e);
            }

            const card = document.getElementById(`card-${id}`);
            if (card) {
                card.classList.add('fade-out-slide');
                
                // Update local data model
                currentSignals = currentSignals.filter(s => s.synthetic_id !== id);
                
                // Update UI Counters immediately
                updateStats(currentSignals);
                
                if (actionType === 'approve') {
                    const actionCount = document.getElementById('human-actions');
                    actionCount.innerText = parseInt(actionCount.innerText) + 1;
                }
                
                setTimeout(() => {
                    card.remove();
                    if(currentSignals.length === 0) {
                        container.innerHTML = '<p class="text-slate-500">No pending signals.</p>';
                    }
                }, 400);
            }
        }

        function approveAction(id) {
            // Removed Alert
            removeCardAndRefresh(id, 'approve');
        }

        function declineAction(id) {
            // Removed Alert
            removeCardAndRefresh(id, 'decline'); 
        }

        function initDashboardCharts(signals) {
            // Data Prep: Departments
            const deptCounts = {};
            signals.forEach(s => { deptCounts[s.target_department] = (deptCounts[s.target_department] || 0) + 1; });
            
            // Data Prep: Risk (Urgency)
            const riskCounts = { 'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0 };
            signals.forEach(s => { 
                if(riskCounts[s.shadow_review_urgency] !== undefined) riskCounts[s.shadow_review_urgency]++; 
            });



            // 2. Risk Chart
            const riskCtx = document.getElementById('riskChart').getContext('2d');
            if (riskChartInstance) riskChartInstance.destroy();
            riskChartInstance = new Chart(riskCtx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(riskCounts),
                    datasets: [{
                        data: Object.values(riskCounts),
                        backgroundColor: ['#ef4444', '#f97316', '#eab308', '#3b82f6'], 
                        borderWidth: 0,
                        cutout: '75%'
                    }]
                },
                options: { plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, font: { weight: 'bold', size: 10 } } } } }
            });
        }

        function openBriefing() {
            document.getElementById('current-date').innerText = new Date().toLocaleString();
            const content = document.getElementById('briefing-content');
            
            // Dynamic Briefing Content
            if (currentSignals.length === 0) {
                 content.innerHTML = '<p class="text-sm text-slate-500">No active signals to report.</p>';
            } else {
                const topRisk = currentSignals.find(s => s.shadow_review_urgency === 'Critical') || currentSignals[0];
                const avgSent = (currentSignals.reduce((a,b)=>a+b.sentiment_score,0)/currentSignals.length).toFixed(2);
                
                content.innerHTML = `
                    <div class="p-6 bg-blue-50 border border-blue-100 rounded-2xl">
                        <p class="text-xs font-bold text-blue-600 uppercase mb-2">Trend Analysis</p>
                        <p class="text-xs font-medium leading-relaxed text-slate-700">
                            Tracking <strong>${currentSignals.length}</strong> active signals. 
                            Primary driver: <strong>${topRisk.scenario_category}</strong> (Avg Sentiment: <strong>${avgSent}</strong>). 
                            Focus: <strong>${topRisk.target_department}</strong>.
                        </p>
                    </div>
                    <div class="space-y-3">
                        <p class="text-xs font-bold text-slate-400 uppercase">Key Actions Required</p>
                        ${currentSignals.filter(s => s.is_flagged_for_review).slice(0, 3).map(s => `
                            <div class="flex gap-3 items-start p-3 border border-slate-100 rounded-xl">
                                <div class="w-1.5 h-1.5 bg-slate-900 rounded-full mt-1.5"></div>
                                <div>
                                    <p class="text-[10px] font-bold uppercase text-slate-400 mb-0.5">${s.target_department} • ${s.shadow_review_urgency}</p>
                                    <p class="text-xs font-bold text-slate-800 leading-tight">${s.module3_impact_assessment}</p>
                                    <p class="text-[10px] font-medium text-slate-500 mt-1">Rec: ${s.module3_suggested_action}</p>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;
            }
            document.getElementById('briefing-modal').classList.remove('hidden');
        }

        function closeBriefing() {
            document.getElementById('briefing-modal').classList.add('hidden');
        }

        function downloadPDF() {
            const element = document.getElementById('briefing-export-area');
            const opt = {
                margin: 0.2,
                filename: 'Mashreq_Executive_Brief.pdf',
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2 },
                jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
            };
            html2pdf().set(opt).from(element).save();
        }

        // Initialize
        loadDashboardData();
        
        // --- ADDED: Auto-refresh every 10 seconds ---
        setInterval(loadDashboardData, 10000);
    </script>
</body>
</html>
"""


# 2. Governance
HTML_GOVERNANCE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Mashreq | Governance & Audit</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>html { font-size: 115%; } body { font-family: 'Outfit', sans-serif; background-color: #f8fafc; }</style>
</head>
<body class="text-slate-900">
    <nav class="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center">
        <h1 class="text-lg font-bold">Signal Intelligence <span class="text-blue-600">Pro</span></h1>
        <a href="/" class="text-xs font-bold uppercase text-slate-500 hover:text-slate-900">← Back to Dashboard</a>
    </nav>
    <main class="p-8 max-w-[1200px] mx-auto">
        <h2 class="text-3xl font-extrabold mb-2">Governance & Audit Logs</h2>
        <p class="text-slate-500 mb-8">Immutable record of all human-in-the-loop decisions and AI interactions.</p>
        
        <div class="bg-white rounded-[2rem] border border-slate-200 shadow-sm overflow-hidden">
            <table class="w-full text-left text-sm text-slate-600">
                <thead class="bg-slate-50 text-slate-900 font-bold uppercase text-xs">
                    <tr>
                        <th class="p-6">Timestamp</th>
                        <th class="p-6">Signal ID</th>
                        <th class="p-6">Action Taken</th>
                        <th class="p-6">Authorized By</th>
                        <th class="p-6">Status</th>
                    </tr>
                </thead>
                <tbody id="audit-table-body" class="divide-y divide-slate-100">
                    </tbody>
            </table>
        </div>
    </main>
    <script>
        async function loadAuditLog() {
            const res = await fetch('/api/audit-log');
            const data = await res.json();
            const tbody = document.getElementById('audit-table-body');
            
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="p-6 text-center text-slate-400">No actions recorded yet.</td></tr>';
            } else {
                tbody.innerHTML = data.map(row => `
                    <tr class="hover:bg-slate-50">
                        <td class="p-6 font-mono text-xs">${row.timestamp}</td>
                        <td class="p-6 font-mono text-xs">${row.synthetic_id}</td>
                        <td class="p-6 capitalize">${row.action} Signal</td>
                        <td class="p-6">Human Operator</td>
                        <td class="p-6">
                            <span class="${row.action === 'approve' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'} px-3 py-1 rounded-full text-xs font-bold uppercase">
                                ${row.action === 'approve' ? 'AUTHORIZED' : 'DECLINED'}
                            </span>
                        </td>
                    </tr>
                `).join('');
            }
        }
        loadAuditLog();
    </script>
</body>
</html>
"""

# 3. AI Logic Page
HTML_AILOGIC = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Mashreq | AI Logic</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>html { font-size: 115%; } body { font-family: 'Outfit', sans-serif; background-color: #f8fafc; }</style>
</head>
<body class="text-slate-900">
    <nav class="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center">
        <h1 class="text-lg font-bold">Signal Intelligence <span class="text-blue-600">Pro</span></h1>
        <a href="/" class="text-xs font-bold uppercase text-slate-500 hover:text-slate-900">← Back to Dashboard</a>
    </nav>
    <main class="p-8 max-w-[1000px] mx-auto space-y-8">
        <div>
            <h2 class="text-3xl font-extrabold mb-2">Responsible AI Logic</h2>
            <p class="text-slate-500">Transparent explanation of signal detection and decision boundaries.</p>
        </div>

        <div class="grid grid-cols-2 gap-8">
            <div class="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm">
                <h3 class="text-lg font-bold mb-4">Detection Methodology</h3>
                <p class="text-sm leading-relaxed text-slate-600 mb-4">
                    The system utilizes a hybrid NLP approach to ingest synthetic social data. It filters for banking-specific keywords related to fraud, outages, and reputation.
                </p>
                <ul class="list-disc list-inside text-sm text-slate-600 space-y-2">
                    <li><strong>Sentiment Analysis:</strong> Range -1.0 to 1.0</li>
                    <li><strong>Entity Recognition:</strong> Filters PII automatically</li>
                    <li><strong>Urgency Scoring:</strong> Based on velocity of mentions</li>
                </ul>
            </div>
            
             <div class="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm">
                <h3 class="text-lg font-bold mb-4">Human-in-the-Loop Guardrails</h3>
                <p class="text-sm leading-relaxed text-slate-600 mb-4">
                    No action is taken autonomously. The AI generates a <span class="font-bold">Module 3 impact assessment</span> which must be explicitly authorized by a human operator.
                </p>
                <div class="bg-blue-50 p-4 rounded-xl text-xs text-blue-800 font-mono">
                    IF risk > 0.8 THEN flag_for_human_review()<br>
                    ELSE archive_signal()
                </div>
            </div>
        </div>
    </main>
</body>
</html>
"""

# 4. Analytics Page
HTML_ANALYTICS = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Mashreq | Advanced Analytics</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono&display=swap" rel="stylesheet">
    <style>html { font-size: 115%; } body { font-family: 'Outfit', sans-serif; background-color: #f8fafc; }</style>
</head>
<body class="text-slate-900">
    <nav class="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center sticky top-0 z-50">
        <h1 class="text-lg font-bold">Signal Intelligence <span class="text-blue-600">Analytics</span></h1>
        <a href="/" class="text-xs font-bold uppercase text-slate-500 hover:text-slate-900">← Back to Dashboard</a>
    </nav>
    <main class="p-8 max-w-[1600px] mx-auto">
        <div class="mb-8">
            <h2 class="text-3xl font-extrabold mb-2">Deep-Dive Analytics</h2>
            <p class="text-slate-500">Historical trend analysis and risk metrics.</p>
        </div>

        <div class="grid grid-cols-2 gap-8">
            
            <div class="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm">
                <h3 class="text-xs font-black text-slate-400 uppercase tracking-widest mb-4">Signal vs. Noise Scatter</h3>
                <p class="text-[10px] text-slate-400 mb-6">Sentiment (X) vs. Derived Urgency Impact (Y)</p>
                <div class="h-[300px]">
                    <canvas id="scatterChart"></canvas>
                </div>
            </div>

            <div class="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm">
                <h3 class="text-xs font-black text-slate-400 uppercase tracking-widest mb-4">Scenario Distribution</h3>
                <div class="h-[300px] flex justify-center">
                    <canvas id="scenarioChart"></canvas>
                </div>
            </div>

            <div class="bg-white p-8 rounded-[2rem] border border-slate-200 shadow-sm flex flex-col items-center">
                <h3 class="text-xs font-black text-slate-400 uppercase tracking-widest mb-4 w-full text-left">Human Review Load</h3>
                <div class="h-[250px] w-full flex justify-center items-end pb-8 relative">
                    <canvas id="gaugeChart"></canvas>
                    <div class="absolute bottom-10 text-4xl font-black text-slate-800" id="gauge-text">0%</div>
                </div>
                <p class="text-xs text-center text-slate-500 max-w-md">Percentage of total signals flagged for mandatory human review.</p>
            </div>

        </div>
    </main>

    <script>
        async function loadData() {
            const response = await fetch('/api/analytics-data');
            const data = await response.json();
            initCharts(data);
        }

        function initCharts(data) {
            // HELPER: Convert Urgency Text to Number
            const urgencyToNum = (u) => {
                if (u === 'Critical') return 4;
                if (u === 'High') return 3;
                if (u === 'Medium') return 2;
                return 1; // Low
            };

            // HELPER: Convert Urgency to 0-100 Score for Scatter
            const urgencyToScore = (u) => {
                if (u === 'Critical') return 95;
                if (u === 'High') return 75;
                if (u === 'Medium') return 50;
                return 20; // Low
            };

            // 1. SCATTER (Sentiment vs Derived Impact)
            new Chart(document.getElementById('scatterChart'), {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: 'Signals',
                        data: data.map(d => ({ 
                            x: d.sentiment_score, 
                            y: urgencyToScore(d.shadow_review_urgency) 
                        })),
                        backgroundColor: (ctx) => {
                            const val = ctx.raw?.y;
                            return val > 80 ? '#ef4444' : (val > 50 ? '#f97316' : '#3b82f6');
                        }
                    }]
                },
                options: {
                    scales: {
                        x: { title: { display: true, text: 'Sentiment (-1.0 to 1.0)' }, min: -1, max: 1 },
                        y: { title: { display: true, text: 'Derived Impact Score (0-100)' }, min: 0, max: 100 }
                    },
                    plugins: { legend: { display: false } }
                }
            });

            // 2. DISTRIBUTION (Pie)
            const categories = {};
            data.forEach(d => { categories[d.scenario_category] = (categories[d.scenario_category] || 0) + 1; });
            
            new Chart(document.getElementById('scenarioChart'), {
                type: 'doughnut',
                data: {
                    labels: Object.keys(categories),
                    datasets: [{
                        data: Object.values(categories),
                        // CHANGED: "Good coloring" applied here (Problem 5)
                        backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'],
                        borderWidth: 0
                    }]
                },
                options: { cutout: '60%', plugins: { legend: { position: 'right' } } }
            });

            // 3. FLAGGED RATIO GAUGE
            const flaggedCount = data.filter(d => d.is_flagged_for_review === true).length;
            const percentage = Math.round((flaggedCount / data.length) * 100) || 0;
            document.getElementById('gauge-text').innerText = percentage + '%';

            new Chart(document.getElementById('gaugeChart'), {
                type: 'doughnut',
                data: {
                    labels: ['Flagged', 'Auto-Archived'],
                    datasets: [{
                        data: [percentage, 100 - percentage],
                        backgroundColor: ['#ef4444', '#e2e8f0'],
                        circumference: 180,
                        rotation: 270,
                        borderWidth: 0
                    }]
                },
                options: { aspectRatio: 2, cutout: '80%', plugins: { legend: { display: false }, tooltip: { enabled: false } } }
            });
        }

        loadData();
    </script>
</body>
</html>
"""


# 5. PR Page
HTML_PR_AGENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>ADAN | Signal Intelligence</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Outfit', sans-serif; background-color: #f8fafc; }
        .fade-out { opacity: 0; transform: translateY(-10px); transition: all 0.3s ease; }
        .fade-in { animation: slideUp 0.4s ease-out forwards; }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body class="text-slate-900">
    <nav class="bg-white border-b border-slate-200 px-8 py-4 flex justify-between items-center sticky top-0 z-50">
        <div class="flex items-center gap-4">
            <h1 class="text-lg font-bold italic">ADAN <span class="text-blue-600">BANK</span></h1>
            <span class="text-[10px] font-black text-slate-400 border border-slate-200 px-3 py-1 rounded-full uppercase">PR HITL AGENT</span>
        </div>
        <a href="/" class="text-xs font-bold uppercase text-slate-500 hover:text-slate-900">← Back to Dashboard</a>
    </nav>

    <main class="p-8 max-w-[1400px] mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        <div class="lg:col-span-2 space-y-8">
            <section class="bg-white p-8 rounded-[2.5rem] border border-slate-200 shadow-sm">
                <h2 class="text-2xl font-extrabold mb-6">Signal Simulation</h2>
                <div class="flex flex-wrap gap-3">
                    <button onclick="simulate('scam')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-8 py-6 rounded-3xl text-lg font-bold transition w-full md:w-auto flex-1">🚨 Security</button>
                    <button onclick="simulate('bankrupt')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-8 py-6 rounded-3xl text-lg font-bold transition w-full md:w-auto flex-1">📉 Market</button>
                    <button onclick="simulate('loan')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-8 py-6 rounded-3xl text-lg font-bold transition w-full md:w-auto flex-1">💰 Product</button>
                    <button onclick="simulate('privacy')" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-8 py-6 rounded-3xl text-lg font-bold transition w-full md:w-auto flex-1">🔒 Privacy</button>
                </div>
            </section>

            <div id="output-container" class="hidden">
                <div id="card-frame" class="bg-white p-8 rounded-[2.5rem] border border-slate-200 shadow-xl relative">
                    <div class="flex justify-between items-center mb-6">
                        <span id="badge-category" class="bg-blue-600 text-white text-[10px] font-black uppercase px-3 py-1 rounded-full">CATEGORY</span>
                        <p class="text-[10px] text-slate-400 font-mono" id="signal-id"></p>
                    </div>

                    <h3 id="signal-text" class="text-xl font-bold mb-6 text-slate-800"></h3>

                    <div class="grid grid-cols-1 gap-6">
                        <div id="text-display-mode">
                            <label class="text-[10px] font-black text-slate-400 uppercase mb-2 block">Official Broadcast Draft</label>
                            <div class="bg-slate-50 p-6 rounded-2xl border border-slate-100 text-slate-700 italic leading-relaxed" id="ai-suggestion"></div>
                        </div>
                        <div id="text-edit-mode" class="hidden">
                            <label class="text-[10px] font-black text-blue-600 uppercase mb-2 block">Post Editor</label>
                            <textarea id="edit-area" class="w-full h-32 p-4 rounded-2xl border-2 border-blue-400 focus:ring-4 focus:ring-blue-50 outline-none text-slate-700"></textarea>
                        </div>
                        
                        <div class="bg-blue-50 p-4 rounded-2xl border border-blue-100">
                            <p class="text-[10px] font-black text-blue-400 uppercase mb-1">AI Reasoning Log</p>
                            <p id="ai-reasoning" class="text-xs text-blue-800"></p>
                        </div>
                    </div>

                    <div id="action-bar" class="mt-8 pt-6 border-t border-slate-100 flex items-center gap-4">
                        <button onclick="handleAction('approve')" class="bg-blue-600 text-white px-8 py-3 rounded-xl font-bold text-sm hover:bg-blue-700 transition active:scale-95">Approve & Broadcast</button>
                        <button id="edit-btn" onclick="toggleEdit()" class="bg-white border border-slate-200 text-slate-600 px-8 py-3 rounded-xl font-bold text-sm hover:bg-slate-50">Edit Text</button>
                        <button onclick="handleAction('reject')" class="ml-auto text-red-400 font-bold text-sm">Discard</button>
                    </div>
                </div>
            </div>

            <div id="empty-state" class="text-center py-20 bg-slate-50 rounded-[2.5rem] border-2 border-dashed border-slate-200 text-slate-400 text-sm font-medium">
                Review queue empty.
            </div>
        </div>

        <div class="space-y-6">
            <div class="bg-white p-8 rounded-[2.5rem] border border-slate-200 shadow-sm h-full">
                <div class="flex items-center justify-between mb-8">
                    <h2 class="text-xl font-extrabold">Noticeboard</h2>
                    <span id="post-count" class="text-[10px] bg-blue-600 text-white px-2 py-0.5 rounded-full font-bold">0</span>
                </div>
                
                <div id="noticeboard-list" class="space-y-5">
                    </div>
            </div>
        </div>
    </main>

    <script>
        let currentId = "";
        let currentCat = "";

        const scenarios = {
            scam: { text: "Just got a call asking for my bank PIN!", cat: "Security" },
            bankrupt: { text: "Rumors say ADAN bank is closing next week!", cat: "Market" },
            loan: { text: "Are your loan rates still the lowest in the city?", cat: "Product" },
            privacy: { text: "Does the bank sell my spending data?", cat: "Privacy" }
        };

        async function simulate(type) {
            const data = scenarios[type];
            currentId = "SYN-" + Math.floor(Math.random()*9999);
            currentCat = data.cat;

            document.getElementById('empty-state').classList.add('hidden');
            const container = document.getElementById('output-container');
            container.classList.remove('hidden', 'fade-out');
            container.classList.add('fade-in');

            const res = await fetch('/api/process-signal', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ synthetic_id: currentId, raw_text: data.text, scenario_category: data.cat })
            });
            const result = await res.json();

            document.getElementById('signal-text').innerText = `"${data.text}"`;
            document.getElementById('ai-suggestion').innerText = result.suggested_response;
            document.getElementById('edit-area').value = result.suggested_response;
            document.getElementById('ai-reasoning').innerText = result.reasoning_notes;
            document.getElementById('signal-id').innerText = `REQ: ${currentId}`;
            document.getElementById('badge-category').innerText = data.cat;
        }

        function toggleEdit() {
            const isEditing = document.getElementById('text-edit-mode').classList.contains('hidden');
            document.getElementById('text-edit-mode').classList.toggle('hidden');
            document.getElementById('text-display-mode').classList.toggle('hidden');
            document.getElementById('edit-btn').innerText = isEditing ? "Save Preview" : "Edit Text";
            if(!isEditing) document.getElementById('ai-suggestion').innerText = document.getElementById('edit-area').value;
        }

        async function handleAction(action) {
            const res = await fetch('/api/submit-decision', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    synthetic_id: currentId,
                    action: action,
                    final_text: document.getElementById('edit-area').value,
                    category: currentCat
                })
            });

            if (res.ok) {
                const container = document.getElementById('output-container');
                container.classList.add('fade-out');
                setTimeout(() => {
                    container.classList.add('hidden');
                    document.getElementById('empty-state').classList.remove('hidden');
                    updateNoticeboard();
                }, 300);
            }
        }

        async function updateNoticeboard() {
            const res = await fetch('/api/history');
            const data = await res.json();
            const list = document.getElementById('noticeboard-list');
            document.getElementById('post-count').innerText = data.length;
            
            list.innerHTML = data.length ? data.map(post => `
                <div class="p-5 bg-white border border-slate-100 rounded-2xl shadow-sm space-y-3 fade-in border-l-4 border-l-blue-600">
                    <div class="flex justify-between items-center">
                        <span class="text-[8px] font-black text-blue-600 uppercase tracking-widest">${post.category} Update</span>
                        <span class="text-[8px] text-slate-400 font-mono">${post.timestamp}</span>
                    </div>
                    <p class="text-xs text-slate-700 leading-relaxed font-bold">${post.text}</p>
                </div>
            `).join('') : '<p class="text-center py-20 text-slate-300 text-xs italic">Waiting for official updates.</p>';
        }

        updateNoticeboard();
    </script>
</body>
</html>
"""

# --- ROUTES ---

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await websocket.send_json({"type": "INIT", "payload": [s.dict() for s in signals_db]})

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    return HTMLResponse(content=HTML_DASHBOARD)

@app.get("/governance", response_class=HTMLResponse)
async def get_governance(request: Request):
    return HTMLResponse(content=HTML_GOVERNANCE)

@app.get("/ai-logic", response_class=HTMLResponse)
async def get_ai_logic(request: Request):
    return HTMLResponse(content=HTML_AILOGIC)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- UPDATED SIMULATION TASK ---
@app.on_event("startup")
async def simulate_live_signals():
    async def task():
        await asyncio.sleep(8)
        new_signal = Signal(
            synthetic_id=f"SYN-2024-{datetime.now().second}",
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            raw_text="Users reporting unverified claims about account closures on Telegram groups.",
            source_type="Synthetic Messaging",
            category="Misinformation",
            generation_sequence=47,
            pii_scrubbed_count=5,
            scenario_category="Misinformation or False Claims",
            sentiment_score=-0.45,
            shadow_review_urgency="Moderate",
            is_flagged_for_review=True,
            target_department="Comms",
            internal_action_draft="Draft clarifying social post.",
            # Added Module 3 fields for simulation
            module3_explanation="Context implies potential for viral spread of false information.",
            module3_impact_assessment="Moderate reputational risk if left unaddressed.",
            module3_suggested_action="Monitor sentiment drift and prepare statement."
        )
        signals_db.insert(0, new_signal)
        await manager.broadcast({"type": "UPDATE", "payload": [s.dict() for s in signals_db]})
    
    asyncio.create_task(task())

@app.get("/analytics", response_class=HTMLResponse)
async def get_analytics(request: Request):
    return HTMLResponse(content=HTML_ANALYTICS)

@app.get("/api/analytics-data")
async def get_analytics_data():
    # 1. Construct the path to the sibling directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "..", "module3_reasoning", "agentic_output.json")
    
    # 2. Try to read the file
    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Fallback to internal mock data if file is missing or currently being written
        return [s.dict() for s in signals_db]

# --- NEW ROUTES FOR PR AGENT ---

@app.get("/pr-agent", response_class=HTMLResponse)
async def get_pr_agent(request: Request):
    return HTMLResponse(content=HTML_PR_AGENT)

@app.post("/api/process-signal")
async def process_pr_signal(request: PRSignalRequest):
    """
    Simulates the AI analyzing a PR signal and drafting a response.
    """
    await asyncio.sleep(1) # Simulate processing delay
    
    # Simple Mock Logic for dynamic responses
    suggestion = ""
    reasoning = ""
    
    if request.scenario_category == "Security":
        suggestion = "We are aware of reports regarding potential phishing attempts. Please never share your PIN. Our security team is investigating."
        reasoning = "High Urgency: Recognized keywords 'PIN' and 'call'. Drafted standard containment response."
    
    elif request.scenario_category == "Market":
        suggestion = "ADAN Bank maintains a liquidity coverage ratio of 150%, well above regulatory requirements. Operations are normal."
        reasoning = "Category: Market Rumor. Retrieved latest liquidity stats from internal ledger. Tone: Reassuring and factual."
        
    elif request.scenario_category == "Privacy":
        suggestion = "We value your privacy. ADAN Bank does not sell personal customer data to third parties. Review our policy at adan.com/privacy."
        reasoning = "Detected privacy concern. Matched with Policy Section 4.2 (Data Sovereignty). Suggested direct link to policy."
        
    else: # Default/Product
        suggestion = "Thank you for your interest! Yes, our personal loan rates remain the most competitive in the region at 3.5% APR."
        reasoning = "Sentiment: Inquisitive. Action: Sales opportunity detected. Drafted engagement response."

    return {
        "suggested_response": suggestion,
        "reasoning_notes": reasoning
    }

@app.post("/api/submit-decision")
async def submit_pr_decision(request: PRDecisionRequest):
    """
    Handles the Human-in-the-Loop decision. 
    If approved, saves to the public noticeboard history.
    """
    if request.action == "approve":
        new_entry = {
            "id": request.synthetic_id,
            "text": request.final_text,
            "category": request.category,
            "timestamp": datetime.now().strftime("%H:%M")
        }
        pr_history_db.insert(0, new_entry) # Add to top of list
        
    return {"status": "success"}

@app.get("/api/history")
async def get_pr_history():
    return pr_history_db

@app.get("/api/audit-log")
async def get_audit_log():
    # Sort by newest first
    return sorted(audit_db, key=lambda x: x['timestamp'], reverse=True)

@app.post("/api/resolve-signal")
async def resolve_signal_endpoint(request: ResolveSignalRequest):
    # 1. Update Audit Log (Problem 3)
    audit_db.append({
        "synthetic_id": request.synthetic_id,
        "action": request.action,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    # 2. Remove from JSON File (Problem 1)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "..", "module3_reasoning", "agentic_output.json")
    
    try:
        # Read
        if os.path.exists(json_path):
            with open(json_path, "r") as f:
                data = json.load(f)
            
            # Filter
            new_data = [d for d in data if d.get('synthetic_id') != request.synthetic_id]
            
            # Write
            with open(json_path, "w") as f:
                json.dump(new_data, f, indent=4)
                
    except Exception as e:
        print(f"Error updating JSON: {e}")
        
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)