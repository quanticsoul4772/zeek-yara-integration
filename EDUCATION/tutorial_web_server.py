#!/usr/bin/env python3
"""
Interactive Educational Tutorial Web Server
Modern web-based tutorial system with rich interactivity
"""

import os
import json
import time
import uuid
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import tutorial system components
import sys
sys.path.append(str(Path(__file__).parent.parent))
from tutorial_system import TutorialManager, TutorialStep


@dataclass
class InteractiveStep:
    """Enhanced tutorial step with web interactivity."""
    id: str
    title: str
    content: str
    step_type: str  # 'lesson', 'exercise', 'quiz', 'demonstration'
    duration_estimate: str
    learning_objectives: List[str]
    prerequisites: List[str] = None
    interactive_elements: Dict[str, Any] = None
    code_examples: List[Dict[str, str]] = None
    assessment_questions: List[Dict[str, Any]] = None
    next_steps: List[str] = None
    completion_criteria: Dict[str, Any] = None


@dataclass
class LearningSession:
    """Represents an active learning session."""
    session_id: str
    user_id: str
    tutorial_id: str
    current_step: int
    start_time: datetime
    last_activity: datetime
    progress_data: Dict[str, Any]
    achievements_earned: List[str]


class TutorialWebServer:
    """Web server for interactive educational tutorials."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.project_root = Path(config.get('PROJECT_ROOT', '.'))
        self.education_dir = self.project_root / "EDUCATION"
        self.templates_dir = self.education_dir / "templates"
        self.static_dir = self.education_dir / "static"
        
        # Ensure directories exist
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.static_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize FastAPI app
        self.app = FastAPI(title="Security Learning Platform", description="Interactive Security Education")
        self.setup_middleware()
        self.setup_routes()
        
        # Tutorial management
        self.tutorial_manager = TutorialManager(config)
        self.active_sessions: Dict[str, LearningSession] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        
        # Templates
        self.templates = Jinja2Templates(directory=str(self.templates_dir))
        
        self.logger = logging.getLogger(__name__)
        
    def setup_middleware(self):
        """Setup FastAPI middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """Setup web routes."""
        
        # Serve static files
        self.app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")
        
        # Main routes
        self.app.get("/")(self.home)
        self.app.get("/tutorials")(self.tutorial_list)
        self.app.get("/tutorial/{tutorial_id}")(self.tutorial_detail)
        self.app.get("/tutorial/{tutorial_id}/step/{step_id}")(self.tutorial_step)
        self.app.post("/api/tutorial/{tutorial_id}/start")(self.start_tutorial)
        self.app.post("/api/tutorial/{tutorial_id}/step/{step_id}/complete")(self.complete_step)
        self.app.get("/api/progress")(self.get_progress)
        self.app.get("/api/achievements")(self.get_achievements)
        self.app.websocket("/ws/{session_id}")(self.websocket_endpoint)
        
        # Tutorial content API
        self.app.get("/api/tutorials")(self.api_get_tutorials)
        self.app.get("/api/tutorial/{tutorial_id}/content")(self.api_get_tutorial_content)
        
    async def home(self, request: Request):
        """Home page with learning dashboard."""
        return self.templates.TemplateResponse("dashboard.html", {
            "request": request,
            "user_progress": self.tutorial_manager.user_progress,
            "available_tutorials": self.get_enhanced_tutorials()
        })
    
    async def tutorial_list(self, request: Request):
        """Tutorial listing page."""
        tutorials = self.get_enhanced_tutorials()
        return self.templates.TemplateResponse("tutorial_list.html", {
            "request": request,
            "tutorials": tutorials,
            "user_progress": self.tutorial_manager.user_progress
        })
    
    async def tutorial_detail(self, request: Request, tutorial_id: str):
        """Tutorial detail and overview page."""
        tutorial_content = self.get_tutorial_content(tutorial_id)
        if not tutorial_content:
            raise HTTPException(status_code=404, detail="Tutorial not found")
        
        return self.templates.TemplateResponse("tutorial_detail.html", {
            "request": request,
            "tutorial": tutorial_content,
            "user_progress": self.tutorial_manager.user_progress
        })
    
    async def tutorial_step(self, request: Request, tutorial_id: str, step_id: str):
        """Individual tutorial step page."""
        tutorial_content = self.get_tutorial_content(tutorial_id)
        if not tutorial_content:
            raise HTTPException(status_code=404, detail="Tutorial not found")
        
        step = next((s for s in tutorial_content['steps'] if s['id'] == step_id), None)
        if not step:
            raise HTTPException(status_code=404, detail="Step not found")
        
        return self.templates.TemplateResponse("tutorial_step.html", {
            "request": request,
            "tutorial": tutorial_content,
            "step": step,
            "user_progress": self.tutorial_manager.user_progress
        })
    
    async def start_tutorial(self, tutorial_id: str, request: Request):
        """Start a new tutorial session."""
        session_id = str(uuid.uuid4())
        user_id = "default_user"  # In a real app, get from auth
        
        session = LearningSession(
            session_id=session_id,
            user_id=user_id,
            tutorial_id=tutorial_id,
            current_step=0,
            start_time=datetime.now(),
            last_activity=datetime.now(),
            progress_data={"steps_completed": [], "quiz_scores": {}, "time_spent": 0},
            achievements_earned=[]
        )
        
        self.active_sessions[session_id] = session
        
        return JSONResponse({
            "session_id": session_id,
            "tutorial_id": tutorial_id,
            "status": "started"
        })
    
    async def complete_step(self, tutorial_id: str, step_id: str, request: Request):
        """Mark a step as completed."""
        body = await request.json()
        session_id = body.get("session_id")
        
        if session_id not in self.active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session = self.active_sessions[session_id]
        session.last_activity = datetime.now()
        
        # Record step completion
        if step_id not in session.progress_data["steps_completed"]:
            session.progress_data["steps_completed"].append(step_id)
        
        # Check for achievements
        achievements = self.check_step_achievements(session, step_id)
        
        return JSONResponse({
            "status": "completed",
            "achievements": achievements,
            "progress": session.progress_data
        })
    
    async def get_progress(self, request: Request):
        """Get user progress data."""
        return JSONResponse(self.tutorial_manager.user_progress)
    
    async def get_achievements(self, request: Request):
        """Get user achievements."""
        return JSONResponse({
            "achievements": self.tutorial_manager.user_progress.get("achievements", []),
            "experience_points": self.tutorial_manager.user_progress.get("experience_points", 0)
        })
    
    async def api_get_tutorials(self):
        """API endpoint for tutorial list."""
        return JSONResponse(self.get_enhanced_tutorials())
    
    async def api_get_tutorial_content(self, tutorial_id: str):
        """API endpoint for tutorial content."""
        content = self.get_tutorial_content(tutorial_id)
        if not content:
            raise HTTPException(status_code=404, detail="Tutorial not found")
        return JSONResponse(content)
    
    async def websocket_endpoint(self, websocket: WebSocket, session_id: str):
        """WebSocket endpoint for real-time tutorial interaction."""
        await websocket.accept()
        self.websocket_connections[session_id] = websocket
        
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message["type"] == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message["type"] == "step_progress":
                    await self.handle_step_progress(session_id, message, websocket)
                elif message["type"] == "request_hint":
                    await self.send_hint(session_id, message, websocket)
                
        except WebSocketDisconnect:
            if session_id in self.websocket_connections:
                del self.websocket_connections[session_id]
    
    async def handle_step_progress(self, session_id: str, message: Dict, websocket: WebSocket):
        """Handle step progress updates via WebSocket."""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session.last_activity = datetime.now()
            
            # Send progress update
            await websocket.send_text(json.dumps({
                "type": "progress_update",
                "progress": session.progress_data
            }))
    
    async def send_hint(self, session_id: str, message: Dict, websocket: WebSocket):
        """Send contextual hints via WebSocket."""
        step_id = message.get("step_id")
        hints = self.get_step_hints(step_id)
        
        await websocket.send_text(json.dumps({
            "type": "hint",
            "step_id": step_id,
            "hints": hints
        }))
    
    def get_enhanced_tutorials(self) -> List[Dict[str, Any]]:
        """Get enhanced tutorial list with additional metadata."""
        base_tutorials = self.tutorial_manager.get_available_tutorials()
        
        enhanced_tutorials = []
        for tutorial in base_tutorials:
            enhanced = {
                **tutorial,
                "steps_count": len(self.get_tutorial_content(tutorial['id'])['steps']) if self.get_tutorial_content(tutorial['id']) else 0,
                "interactive_features": ["code_examples", "quizzes", "visualizations"],
                "completion_rate": self.get_completion_rate(tutorial['id']),
                "estimated_xp": self.calculate_tutorial_xp(tutorial['id'])
            }
            enhanced_tutorials.append(enhanced)
        
        return enhanced_tutorials
    
    def get_tutorial_content(self, tutorial_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive tutorial content with enhanced steps."""
        enhanced_tutorials = {
            'network_security_basics': {
                'id': 'network_security_basics',
                'title': 'Network Security Fundamentals',
                'description': 'Interactive journey through network security concepts',
                'difficulty': 'Beginner',
                'duration': '20 minutes',
                'learning_objectives': [
                    'Understand network traffic and communication',
                    'Learn about security monitoring tools',
                    'Recognize common network threats',
                    'Practice with real network data'
                ],
                'steps': [
                    {
                        'id': 'intro',
                        'title': 'Welcome to Network Security',
                        'step_type': 'lesson',
                        'duration_estimate': '3 minutes',
                        'content': '''
                        <div class="lesson-content">
                            <h3>🛡️ Network Security Fundamentals</h3>
                            <p>Welcome to your journey into network security! In this interactive tutorial, you'll learn:</p>
                            <ul class="learning-objectives">
                                <li>🌐 How network communication works</li>
                                <li>🔍 What security monitoring involves</li>
                                <li>⚠️ Common types of network threats</li>
                                <li>🛠️ How security tools protect networks</li>
                            </ul>
                            <div class="info-box">
                                <strong>💡 Did you know?</strong> Every second, millions of data packets flow across networks worldwide. 
                                Security professionals monitor this traffic to protect against cyber threats!
                            </div>
                        </div>
                        ''',
                        'interactive_elements': {
                            'visualization': 'network_traffic_demo',
                            'progress_check': True
                        },
                        'learning_objectives': [
                            'Understand the scope of network security',
                            'Recognize the importance of traffic monitoring'
                        ]
                    },
                    {
                        'id': 'network_basics',
                        'title': 'Understanding Network Traffic',
                        'step_type': 'demonstration',
                        'duration_estimate': '5 minutes',
                        'content': '''
                        <div class="lesson-content">
                            <h3>🌐 How Network Communication Works</h3>
                            <p>Every time you browse the web, send an email, or use an app, your device sends <strong>packets</strong> of data across the network.</p>
                            
                            <div class="concept-explanation">
                                <h4>What's in a Network Packet?</h4>
                                <div class="packet-diagram">
                                    <div class="packet-header">📍 Source Address</div>
                                    <div class="packet-header">📍 Destination Address</div>
                                    <div class="packet-header">📋 Protocol Type</div>
                                    <div class="packet-data">📦 Your Data</div>
                                </div>
                                <p>Think of packets like postal mail - each has sender/receiver addresses and contains your message!</p>
                            </div>
                            
                            <div class="interactive-demo" id="traffic-simulator">
                                <h4>🎮 Interactive Network Traffic Simulator</h4>
                                <p>Click the button below to see live network traffic:</p>
                                <button onclick="startTrafficDemo()">Start Traffic Simulation</button>
                                <div id="traffic-display"></div>
                            </div>
                        </div>
                        ''',
                        'interactive_elements': {
                            'simulation': 'network_traffic',
                            'quiz_question': {
                                'question': 'What information does every network packet contain?',
                                'type': 'multiple_choice',
                                'options': [
                                    'Source and destination addresses',
                                    'Protocol type',
                                    'Data payload',
                                    'All of the above'
                                ],
                                'correct': 3,
                                'explanation': 'Every network packet contains source/destination addresses, protocol information, and the actual data being transmitted.'
                            }
                        }
                    },
                    {
                        'id': 'security_tools',
                        'title': 'Your Security Toolkit',
                        'step_type': 'lesson',
                        'duration_estimate': '6 minutes',
                        'content': '''
                        <div class="lesson-content">
                            <h3>🛠️ Security Tools Overview</h3>
                            <p>This platform uses three powerful security tools working together:</p>
                            
                            <div class="tools-grid">
                                <div class="tool-card zeek">
                                    <h4>🔍 Zeek</h4>
                                    <div class="tool-role">Network Traffic Analyzer</div>
                                    <ul>
                                        <li>Monitors all network communications</li>
                                        <li>Extracts files from network traffic</li>
                                        <li>Creates detailed activity logs</li>
                                        <li>Identifies communication patterns</li>
                                    </ul>
                                    <div class="tool-analogy">Like a security camera for your network! 📹</div>
                                </div>
                                
                                <div class="tool-card yara">
                                    <h4>🚨 YARA</h4>
                                    <div class="tool-role">Malware Detection Engine</div>
                                    <ul>
                                        <li>Scans files for malicious patterns</li>
                                        <li>Uses rules to identify known threats</li>
                                        <li>Detects malware variants</li>
                                        <li>Provides detailed threat classification</li>
                                    </ul>
                                    <div class="tool-analogy">Like a virus scanner on steroids! 🦠</div>
                                </div>
                                
                                <div class="tool-card suricata">
                                    <h4>🛡️ Suricata</h4>
                                    <div class="tool-role">Intrusion Detection System</div>
                                    <ul>
                                        <li>Monitors for attack patterns</li>
                                        <li>Blocks malicious traffic</li>
                                        <li>Generates real-time alerts</li>
                                        <li>Identifies network intrusions</li>
                                    </ul>
                                    <div class="tool-analogy">Like a security guard at the network gate! 🚪</div>
                                </div>
                            </div>
                            
                            <div class="teamwork-section">
                                <h4>🤝 How They Work Together</h4>
                                <div class="workflow-diagram">
                                    <div class="workflow-step">1. Zeek captures network traffic</div>
                                    <div class="workflow-arrow">→</div>
                                    <div class="workflow-step">2. Files extracted and sent to YARA</div>
                                    <div class="workflow-arrow">→</div>
                                    <div class="workflow-step">3. Suricata checks for attack patterns</div>
                                    <div class="workflow-arrow">→</div>
                                    <div class="workflow-step">4. Alerts generated for threats</div>
                                </div>
                            </div>
                        </div>
                        ''',
                        'interactive_elements': {
                            'tool_demo': True,
                            'progress_check': True
                        }
                    },
                    {
                        'id': 'threat_types',
                        'title': 'Common Network Threats',
                        'step_type': 'lesson',
                        'duration_estimate': '5 minutes',
                        'content': '''
                        <div class="lesson-content">
                            <h3>⚠️ Types of Network Threats</h3>
                            <p>Understanding threats helps you recognize and defend against them:</p>
                            
                            <div class="threats-accordion">
                                <div class="threat-category" data-threat="malware">
                                    <h4>🦠 Malware - Malicious Software</h4>
                                    <div class="threat-details">
                                        <p><strong>What it is:</strong> Software designed to damage, steal, or gain unauthorized access</p>
                                        <p><strong>Types:</strong> Viruses, trojans, ransomware, spyware</p>
                                        <p><strong>How it spreads:</strong> Email attachments, infected downloads, malicious websites</p>
                                        <p><strong>Detection tool:</strong> YARA rules identify malware signatures</p>
                                        <div class="example-box">
                                            <strong>Example:</strong> A user downloads what appears to be a game, but it's actually ransomware that encrypts their files.
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="threat-category" data-threat="intrusion">
                                    <h4>🚪 Network Intrusions - Unauthorized Access</h4>
                                    <div class="threat-details">
                                        <p><strong>What it is:</strong> Attempts to gain unauthorized access to network resources</p>
                                        <p><strong>Methods:</strong> Port scans, brute force attacks, vulnerability exploitation</p>
                                        <p><strong>Signs:</strong> Unusual connection patterns, failed login attempts, suspicious traffic</p>
                                        <p><strong>Detection tool:</strong> Suricata detects intrusion patterns</p>
                                        <div class="example-box">
                                            <strong>Example:</strong> An attacker scans your network for open ports, then tries to exploit a vulnerable service.
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="threat-category" data-threat="exfiltration">
                                    <h4>📤 Data Exfiltration - Information Theft</h4>
                                    <div class="threat-details">
                                        <p><strong>What it is:</strong> Unauthorized copying or transmission of sensitive data</p>
                                        <p><strong>Methods:</strong> Large file uploads, encrypted channels, covert communications</p>
                                        <p><strong>Signs:</strong> Unusual data transfers, connections to unknown servers</p>
                                        <p><strong>Detection tool:</strong> Zeek monitors traffic patterns and file transfers</p>
                                        <div class="example-box">
                                            <strong>Example:</strong> Malware secretly uploads your personal documents to an attacker's server.
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="threat-category" data-threat="command_control">
                                    <h4>📡 Command & Control - Remote Malware Communication</h4>
                                    <div class="threat-details">
                                        <p><strong>What it is:</strong> Infected computers communicating with attacker-controlled servers</p>
                                        <p><strong>Purpose:</strong> Receive commands, send stolen data, download additional malware</p>
                                        <p><strong>Signs:</strong> Regular connections to suspicious domains, encrypted communications</p>
                                        <p><strong>Detection tools:</strong> All three tools work together to identify C&C traffic</p>
                                        <div class="example-box">
                                            <strong>Example:</strong> A trojan on your computer regularly "phones home" to receive new instructions from cybercriminals.
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        ''',
                        'interactive_elements': {
                            'accordion': True,
                            'threat_quiz': {
                                'question': 'Which security tool would be MOST effective at detecting a large file being secretly uploaded to an external server?',
                                'type': 'multiple_choice',
                                'options': ['YARA', 'Zeek', 'Suricata', 'All three equally'],
                                'correct': 1,
                                'explanation': 'Zeek excels at monitoring network traffic patterns and would be most likely to detect unusual file transfer activity.'
                            }
                        }
                    },
                    {
                        'id': 'hands_on_demo',
                        'title': 'Hands-On: Spot the Threat',
                        'step_type': 'exercise',
                        'duration_estimate': '4 minutes',
                        'content': '''
                        <div class="lesson-content">
                            <h3>🎯 Hands-On Exercise: Spot the Threat</h3>
                            <p>Now it's time to practice! Below is simulated network traffic data. Can you identify the security threats?</p>
                            
                            <div class="exercise-container">
                                <div class="traffic-log">
                                    <h4>📊 Network Traffic Log</h4>
                                    <div class="log-entry normal" data-threat="false">
                                        <span class="timestamp">10:30:15</span>
                                        <span class="source">192.168.1.100</span>
                                        <span class="dest">google.com</span>
                                        <span class="protocol">HTTPS</span>
                                        <span class="info">Web browsing</span>
                                    </div>
                                    
                                    <div class="log-entry normal" data-threat="false">
                                        <span class="timestamp">10:30:22</span>
                                        <span class="source">192.168.1.100</span>
                                        <span class="dest">mail.company.com</span>
                                        <span class="protocol">SMTP</span>
                                        <span class="info">Sending email</span>
                                    </div>
                                    
                                    <div class="log-entry suspicious" data-threat="true" data-threat-type="port_scan">
                                        <span class="timestamp">10:30:45</span>
                                        <span class="source">203.0.113.15</span>
                                        <span class="dest">192.168.1.0/24</span>
                                        <span class="protocol">TCP</span>
                                        <span class="info">Scanning ports 1-1000</span>
                                    </div>
                                    
                                    <div class="log-entry normal" data-threat="false">
                                        <span class="timestamp">10:31:03</span>
                                        <span class="source">192.168.1.100</span>
                                        <span class="dest">cdn.example.com</span>
                                        <span class="protocol">HTTPS</span>
                                        <span class="info">Downloading update</span>
                                    </div>
                                    
                                    <div class="log-entry suspicious" data-threat="true" data-threat-type="data_exfiltration">
                                        <span class="timestamp">10:31:15</span>
                                        <span class="source">192.168.1.100</span>
                                        <span class="dest">suspicious-site.ru</span>
                                        <span class="protocol">HTTPS</span>
                                        <span class="info">Uploading 500MB encrypted file</span>
                                    </div>
                                    
                                    <div class="log-entry normal" data-threat="false">
                                        <span class="timestamp">10:31:45</span>
                                        <span class="source">192.168.1.100</span>
                                        <span class="dest">update.microsoft.com</span>
                                        <span class="protocol">HTTPS</span>
                                        <span class="info">Windows update</span>
                                    </div>
                                </div>
                                
                                <div class="exercise-instructions">
                                    <h4>🔍 Your Mission:</h4>
                                    <p>Click on any log entries that look suspicious or threatening. Think about:</p>
                                    <ul>
                                        <li>Unusual source/destination addresses</li>
                                        <li>Suspicious activities (port scanning, large uploads)</li>
                                        <li>Unknown or untrusted domains</li>
                                        <li>Atypical protocol usage</li>
                                    </ul>
                                    <div id="exercise-feedback"></div>
                                </div>
                            </div>
                        </div>
                        ''',
                        'interactive_elements': {
                            'clickable_exercise': True,
                            'immediate_feedback': True
                        },
                        'completion_criteria': {
                            'threats_identified': 2,
                            'false_positives_max': 1
                        }
                    },
                    {
                        'id': 'summary',
                        'title': 'Knowledge Check & Next Steps',
                        'step_type': 'quiz',
                        'duration_estimate': '3 minutes',
                        'content': '''
                        <div class="lesson-content">
                            <h3>🎯 Knowledge Check</h3>
                            <p>Let's test what you've learned about network security fundamentals!</p>
                            
                            <div class="quiz-container">
                                <div class="quiz-question" data-question="1">
                                    <h4>Question 1 of 3</h4>
                                    <p>Which security tool is primarily responsible for analyzing network traffic patterns and extracting files?</p>
                                    <div class="quiz-options">
                                        <label><input type="radio" name="q1" value="a"> YARA</label>
                                        <label><input type="radio" name="q1" value="b"> Zeek</label>
                                        <label><input type="radio" name="q1" value="c"> Suricata</label>
                                        <label><input type="radio" name="q1" value="d"> All three equally</label>
                                    </div>
                                </div>
                                
                                <div class="quiz-question" data-question="2" style="display:none;">
                                    <h4>Question 2 of 3</h4>
                                    <p>What makes network packet analysis effective for security monitoring?</p>
                                    <div class="quiz-options">
                                        <label><input type="radio" name="q2" value="a"> It only monitors encrypted traffic</label>
                                        <label><input type="radio" name="q2" value="b"> It shows all network communications with source, destination, and content</label>
                                        <label><input type="radio" name="q2" value="c"> It only works on wireless networks</label>
                                        <label><input type="radio" name="q2" value="d"> It requires special hardware</label>
                                    </div>
                                </div>
                                
                                <div class="quiz-question" data-question="3" style="display:none;">
                                    <h4>Question 3 of 3</h4>
                                    <p>Which type of threat involves an infected computer regularly communicating with an attacker's server?</p>
                                    <div class="quiz-options">
                                        <label><input type="radio" name="q3" value="a"> Port scanning</label>
                                        <label><input type="radio" name="q3" value="b"> Data exfiltration</label>
                                        <label><input type="radio" name="q3" value="c"> Command & Control</label>
                                        <label><input type="radio" name="q3" value="d"> Network intrusion</label>
                                    </div>
                                </div>
                                
                                <div class="quiz-results" style="display:none;">
                                    <h4>🎉 Quiz Complete!</h4>
                                    <div id="quiz-score"></div>
                                    <div id="quiz-feedback"></div>
                                </div>
                                
                                <div class="quiz-navigation">
                                    <button id="quiz-next" onclick="nextQuestion()" disabled>Next Question</button>
                                    <button id="quiz-submit" onclick="submitQuiz()" style="display:none;">Submit Quiz</button>
                                </div>
                            </div>
                            
                            <div class="next-steps" id="completion-section" style="display:none;">
                                <h3>🚀 Congratulations!</h3>
                                <p>You've completed the Network Security Fundamentals tutorial! You now understand:</p>
                                <ul class="achievement-list">
                                    <li>✅ How network communication works</li>
                                    <li>✅ The role of security monitoring tools</li>
                                    <li>✅ Common types of network threats</li>
                                    <li>✅ How to spot suspicious network activity</li>
                                </ul>
                                
                                <div class="recommended-next">
                                    <h4>🎯 Recommended Next Steps:</h4>
                                    <div class="next-tutorial-cards">
                                        <div class="tutorial-card">
                                            <h5>Your First Threat Detection</h5>
                                            <p>Practice detecting malware with the EICAR test file</p>
                                            <span class="duration">10 minutes</span>
                                        </div>
                                        <div class="tutorial-card">
                                            <h5>Network Monitoring with Zeek</h5>
                                            <p>Deep dive into network traffic analysis</p>
                                            <span class="duration">20 minutes</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        ''',
                        'assessment_questions': [
                            {
                                'question': 'Which security tool is primarily responsible for analyzing network traffic patterns and extracting files?',
                                'type': 'multiple_choice',
                                'options': ['YARA', 'Zeek', 'Suricata', 'All three equally'],
                                'correct': 1,
                                'explanation': 'Zeek is specifically designed for network traffic analysis and file extraction.'
                            },
                            {
                                'question': 'What makes network packet analysis effective for security monitoring?',
                                'type': 'multiple_choice', 
                                'options': [
                                    'It only monitors encrypted traffic',
                                    'It shows all network communications with source, destination, and content',
                                    'It only works on wireless networks',
                                    'It requires special hardware'
                                ],
                                'correct': 1,
                                'explanation': 'Packet analysis is effective because it provides complete visibility into network communications.'
                            },
                            {
                                'question': 'Which type of threat involves an infected computer regularly communicating with an attacker\'s server?',
                                'type': 'multiple_choice',
                                'options': ['Port scanning', 'Data exfiltration', 'Command & Control', 'Network intrusion'],
                                'correct': 2,
                                'explanation': 'Command & Control (C&C) communications involve infected systems regularly contacting attacker servers for instructions.'
                            }
                        ],
                        'completion_criteria': {
                            'quiz_score_min': 2,
                            'quiz_attempts_max': 3
                        }
                    }
                ]
            },
            'first_detection': {
                'id': 'first_detection',
                'title': 'Your First Threat Detection',
                'description': 'Hands-on malware detection using EICAR test file',
                'difficulty': 'Beginner',
                'duration': '15 minutes',
                'learning_objectives': [
                    'Understand safe malware testing with EICAR',
                    'Learn YARA rule functionality',
                    'Practice threat detection workflow',
                    'Interpret security alerts'
                ],
                'steps': [
                    {
                        'id': 'eicar_intro',
                        'title': 'Safe Malware Testing',
                        'step_type': 'lesson',
                        'duration_estimate': '3 minutes',
                        'content': '''
                        <div class="lesson-content">
                            <h3>🧪 Safe Malware Testing with EICAR</h3>
                            <p>Before we work with real threats, let's learn about safe testing methods!</p>
                            
                            <div class="eicar-explanation">
                                <h4>What is EICAR?</h4>
                                <p>The <strong>European Institute for Computer Antivirus Research (EICAR)</strong> created a special test file that:</p>
                                <ul>
                                    <li>✅ Is completely harmless (just text)</li>
                                    <li>✅ Is detected by all antivirus programs</li>
                                    <li>✅ Lets you test detection systems safely</li>
                                    <li>✅ Behaves exactly like real malware for testing</li>
                                </ul>
                            </div>
                            
                            <div class="safety-notice">
                                <h4>🛡️ Why Use Test Files?</h4>
                                <p>Security professionals never use real malware for learning because:</p>
                                <ul>
                                    <li>🚫 Real malware can damage systems</li>
                                    <li>🚫 It can spread to other computers</li>
                                    <li>🚫 It may steal personal information</li>
                                    <li>✅ Test files provide the same learning experience safely</li>
                                </ul>
                            </div>
                            
                            <div class="eicar-content">
                                <h4>📝 The EICAR String</h4>
                                <p>The EICAR test file contains this harmless text:</p>
                                <div class="code-block">
                                    <code>X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*</code>
                                </div>
                                <p>Even though it's just text, every security tool treats it as malware!</p>
                            </div>
                        </div>
                        ''',
                        'interactive_elements': {
                            'code_display': True,
                            'safety_emphasis': True
                        }
                    },
                    {
                        'id': 'yara_rules_intro',
                        'title': 'Understanding YARA Rules',
                        'step_type': 'lesson',
                        'duration_estimate': '4 minutes',
                        'content': '''
                        <div class="lesson-content">
                            <h3>🔍 How YARA Rules Work</h3>
                            <p>YARA rules are like fingerprints for malware - they describe patterns that identify specific threats.</p>
                            
                            <div class="yara-explanation">
                                <h4>YARA Rule Structure</h4>
                                <div class="rule-anatomy">
                                    <div class="code-block">
                                        <pre><code>rule EICAR_Test_File {
    meta:
        description = "Detects EICAR test file"
        author = "Security Education"
        
    strings:
        $eicar = "X5O!P%@AP[4\\\\PZX54(P^)7CC)7}"
        
    condition:
        $eicar
}</code></pre>
                                    </div>
                                    
                                    <div class="rule-breakdown">
                                        <div class="rule-section">
                                            <h5>📝 Meta Section</h5>
                                            <p>Contains information about the rule (description, author, date, etc.)</p>
                                        </div>
                                        <div class="rule-section">
                                            <h5>🔤 Strings Section</h5>
                                            <p>Defines patterns to search for (text, hex values, regular expressions)</p>
                                        </div>
                                        <div class="rule-section">
                                            <h5>✅ Condition Section</h5>
                                            <p>Specifies when the rule should trigger (when patterns are found)</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="pattern-matching">
                                <h4>🎯 How Pattern Matching Works</h4>
                                <div class="matching-demo">
                                    <p>When YARA scans a file, it:</p>
                                    <ol>
                                        <li>🔍 Searches through every byte of the file</li>
                                        <li>📋 Compares content against rule patterns</li>
                                        <li>✅ Triggers an alert when patterns match</li>
                                        <li>📊 Reports which rules matched and where</li>
                                    </ol>
                                </div>
                            </div>
                            
                            <div class="rule-types">
                                <h4>🏷️ Types of Detection Rules</h4>
                                <div class="rule-grid">
                                    <div class="rule-type">
                                        <h5>🦠 Malware Signatures</h5>
                                        <p>Detect known malware families</p>
                                    </div>
                                    <div class="rule-type">
                                        <h5>🧬 Behavior Patterns</h5>
                                        <p>Identify suspicious behaviors</p>
                                    </div>
                                    <div class="rule-type">
                                        <h5>📁 File Characteristics</h5>
                                        <p>Check file structure and properties</p>
                                    </div>
                                    <div class="rule-type">
                                        <h5>🌐 Network Indicators</h5>
                                        <p>Find network-related threats</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        ''',
                        'interactive_elements': {
                            'rule_visualization': True,
                            'code_highlighting': True
                        }
                    },
                    {
                        'id': 'detection_exercise',
                        'title': 'Hands-On: Create and Detect',
                        'step_type': 'exercise',
                        'duration_estimate': '6 minutes',
                        'content': '''
                        <div class="lesson-content">
                            <h3>🎯 Hands-On Detection Exercise</h3>
                            <p>Now let's create an EICAR file and watch our security system detect it!</p>
                            
                            <div class="exercise-steps">
                                <div class="step-card" data-step="1">
                                    <h4>Step 1: Create Test File</h4>
                                    <p>Click the button below to create an EICAR test file:</p>
                                    <button class="action-button" onclick="createEicarFile()">Create EICAR Test File</button>
                                    <div class="step-status" id="create-status">Waiting...</div>
                                </div>
                                
                                <div class="step-card" data-step="2">
                                    <h4>Step 2: Monitor Detection</h4>
                                    <p>Watch the real-time detection results:</p>
                                    <div class="detection-monitor" id="detection-display">
                                        <div class="scanning-status">🔍 Waiting for file creation...</div>
                                    </div>
                                </div>
                                
                                <div class="step-card" data-step="3">
                                    <h4>Step 3: Analyze Results</h4>
                                    <p>Review the detection details:</p>
                                    <div class="results-panel" id="results-panel">
                                        <div class="result-placeholder">Results will appear here after detection...</div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="learning-notes">
                                <h4>💡 What to Observe</h4>
                                <ul>
                                    <li>⏱️ How quickly the detection occurs</li>
                                    <li>📍 Where the file was found</li>
                                    <li>🔍 Which YARA rule triggered</li>
                                    <li>⚠️ Alert severity and classification</li>
                                    <li>📊 Detection confidence level</li>
                                </ul>
                            </div>
                        </div>
                        ''',
                        'interactive_elements': {
                            'file_creation': True,
                            'real_time_monitoring': True,
                            'detection_visualization': True
                        },
                        'completion_criteria': {
                            'file_created': True,
                            'detection_observed': True
                        }
                    },
                    {
                        'id': 'alert_analysis',
                        'title': 'Understanding Security Alerts',
                        'step_type': 'lesson',
                        'duration_estimate': '3 minutes',
                        'content': '''
                        <div class="lesson-content">
                            <h3>📊 Analyzing Security Alerts</h3>
                            <p>Great! You just triggered your first security detection. Let's understand what happened.</p>
                            
                            <div class="alert-breakdown">
                                <h4>🚨 Anatomy of a Security Alert</h4>
                                <div class="sample-alert">
                                    <div class="alert-header">
                                        <span class="severity high">🔴 HIGH SEVERITY</span>
                                        <span class="timestamp">2024-01-15 14:30:22</span>
                                    </div>
                                    <div class="alert-content">
                                        <div class="alert-field">
                                            <strong>Detection:</strong> EICAR Test File Detected
                                        </div>
                                        <div class="alert-field">
                                            <strong>File Path:</strong> /extracted_files/eicar_test.txt
                                        </div>
                                        <div class="alert-field">
                                            <strong>Rule Matched:</strong> EICAR_Test_File
                                        </div>
                                        <div class="alert-field">
                                            <strong>Threat Type:</strong> Test File / Malware Signature
                                        </div>
                                        <div class="alert-field">
                                            <strong>Confidence:</strong> 100% (Perfect Match)
                                        </div>
                                        <div class="alert-field">
                                            <strong>Recommended Action:</strong> File quarantined for analysis
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="alert-components">
                                <h4>🔍 Key Alert Components</h4>
                                <div class="components-grid">
                                    <div class="component">
                                        <h5>⚠️ Severity Level</h5>
                                        <p>How critical the threat is (Low/Medium/High/Critical)</p>
                                    </div>
                                    <div class="component">
                                        <h5>📍 Location Information</h5>
                                        <p>Where the threat was found (file path, network location)</p>
                                    </div>
                                    <div class="component">
                                        <h5>🔍 Detection Method</h5>
                                        <p>Which rule or technique identified the threat</p>
                                    </div>
                                    <div class="component">
                                        <h5>📈 Confidence Score</h5>
                                        <p>How certain the detection system is about the threat</p>
                                    </div>
                                    <div class="component">
                                        <h5>🎯 Threat Classification</h5>
                                        <p>Type of threat (malware family, attack technique)</p>
                                    </div>
                                    <div class="component">
                                        <h5>🛡️ Recommended Actions</h5>
                                        <p>What security teams should do next</p>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="response-workflow">
                                <h4>🔄 Typical Response Workflow</h4>
                                <div class="workflow-steps">
                                    <div class="workflow-step">1. Alert Review</div>
                                    <div class="workflow-arrow">→</div>
                                    <div class="workflow-step">2. Threat Validation</div>
                                    <div class="workflow-arrow">→</div>
                                    <div class="workflow-step">3. Impact Assessment</div>
                                    <div class="workflow-arrow">→</div>
                                    <div class="workflow-step">4. Containment Action</div>
                                    <div class="workflow-arrow">→</div>
                                    <div class="workflow-step">5. Investigation</div>
                                </div>
                            </div>
                        </div>
                        ''',
                        'interactive_elements': {
                            'alert_exploration': True,
                            'response_simulation': True
                        }
                    }
                ]
            }
        }
        
        return enhanced_tutorials.get(tutorial_id)
    
    def get_completion_rate(self, tutorial_id: str) -> float:
        """Calculate completion rate for a tutorial."""
        # In a real implementation, this would query actual user data
        return 0.85  # Example: 85% completion rate
    
    def calculate_tutorial_xp(self, tutorial_id: str) -> int:
        """Calculate experience points for completing a tutorial."""
        base_xp = {
            'network_security_basics': 150,
            'first_detection': 100,
            'zeek_basics': 200,
            'suricata_intro': 200,
            'custom_yara_rules': 300,
            'correlation_analysis': 250,
            'tool_integration': 400
        }
        return base_xp.get(tutorial_id, 100)
    
    def check_step_achievements(self, session: LearningSession, step_id: str) -> List[str]:
        """Check for achievements earned by completing a step."""
        achievements = []
        
        # Example achievement logic
        if len(session.progress_data["steps_completed"]) == 1:
            achievements.append("first_step")
        
        if step_id.endswith("_quiz") and "quiz_master" not in session.achievements_earned:
            achievements.append("quiz_master")
        
        # Add achievements to session
        session.achievements_earned.extend(achievements)
        
        return achievements
    
    def get_step_hints(self, step_id: str) -> List[str]:
        """Get contextual hints for a tutorial step."""
        hints_db = {
            'network_basics': [
                "Think of network packets like postal mail with addresses",
                "Every communication needs a source and destination",
                "Protocols define how different types of data are sent"
            ],
            'security_tools': [
                "Each tool has a specialized role in security",
                "Zeek focuses on network traffic analysis",
                "YARA specializes in malware detection",
                "Suricata watches for attack patterns"
            ],
            'threat_types': [
                "Look for unusual patterns in network behavior",
                "Large file transfers might indicate data theft",
                "Port scans often precede attacks",
                "Regular connections to unknown servers are suspicious"
            ]
        }
        
        return hints_db.get(step_id, ["Keep learning and exploring!"])
    
    def create_initial_templates(self):
        """Create initial HTML templates if they don't exist."""
        templates = {
            'base.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Security Learning Platform{% endblock %}</title>
    <link href="/static/css/styles.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="/" class="nav-brand">🛡️ Security Learning Platform</a>
            <div class="nav-links">
                <a href="/tutorials">Tutorials</a>
                <a href="/api/progress">Progress</a>
                <a href="/api/achievements">Achievements</a>
            </div>
        </div>
    </nav>
    
    <main class="main-content">
        {% block content %}{% endblock %}
    </main>
    
    <script src="/static/js/main.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>''',
            
            'dashboard.html': '''{% extends "base.html" %}

{% block title %}Dashboard - Security Learning Platform{% endblock %}

{% block content %}
<div class="dashboard">
    <div class="welcome-section">
        <h1>🎓 Welcome to Your Security Learning Journey!</h1>
        <p>Track your progress, explore tutorials, and build your cybersecurity skills.</p>
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-number">{{ user_progress.experience_points }}</div>
            <div class="stat-label">Experience Points</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ user_progress.tutorials_completed|length }}</div>
            <div class="stat-label">Tutorials Completed</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ user_progress.achievements|length }}</div>
            <div class="stat-label">Achievements Earned</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{{ "%.1f"|format(user_progress.total_time_spent / 60) }}</div>
            <div class="stat-label">Minutes Learned</div>
        </div>
    </div>
    
    <div class="tutorial-recommendations">
        <h2>🚀 Recommended Tutorials</h2>
        <div class="tutorial-grid">
            {% for tutorial in available_tutorials[:3] %}
            <div class="tutorial-card">
                <div class="tutorial-header">
                    <h3>{{ tutorial.title }}</h3>
                    <span class="difficulty-badge {{ tutorial.difficulty.lower() }}">{{ tutorial.difficulty }}</span>
                </div>
                <p>{{ tutorial.description }}</p>
                <div class="tutorial-meta">
                    <span class="duration">⏱️ {{ tutorial.duration }}</span>
                    <span class="xp">🌟 {{ tutorial.estimated_xp }} XP</span>
                </div>
                <a href="/tutorial/{{ tutorial.id }}" class="btn-primary">Start Tutorial</a>
            </div>
            {% endfor %}
        </div>
    </div>
    
    {% if user_progress.achievements %}
    <div class="achievements-section">
        <h2>🏆 Recent Achievements</h2>
        <div class="achievements-list">
            {% for achievement in user_progress.achievements[-3:] %}
            <div class="achievement-badge">{{ achievement }}</div>
            {% endfor %}
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}''',
            
            'tutorial_list.html': '''{% extends "base.html" %}

{% block title %}Tutorials - Security Learning Platform{% endblock %}

{% block content %}
<div class="tutorial-list-page">
    <div class="page-header">
        <h1>📚 Interactive Security Tutorials</h1>
        <p>Choose your learning path and build cybersecurity expertise step by step.</p>
    </div>
    
    <div class="tutorials-container">
        {% for tutorial in tutorials %}
        <div class="tutorial-item">
            <div class="tutorial-content">
                <div class="tutorial-header">
                    <h3>{{ tutorial.title }}</h3>
                    <div class="tutorial-badges">
                        <span class="difficulty-badge {{ tutorial.difficulty.lower() }}">{{ tutorial.difficulty }}</span>
                        {% if tutorial.id in user_progress.tutorials_completed %}
                        <span class="completion-badge">✅ Completed</span>
                        {% endif %}
                    </div>
                </div>
                
                <p>{{ tutorial.description }}</p>
                
                <div class="tutorial-details">
                    <div class="detail-item">
                        <span class="label">⏱️ Duration:</span>
                        <span class="value">{{ tutorial.duration }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">📋 Steps:</span>
                        <span class="value">{{ tutorial.steps_count }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">🌟 XP:</span>
                        <span class="value">{{ tutorial.estimated_xp }}</span>
                    </div>
                    <div class="detail-item">
                        <span class="label">✨ Features:</span>
                        <span class="value">{{ tutorial.interactive_features|join(", ") }}</span>
                    </div>
                </div>
                
                <div class="tutorial-topics">
                    {% for topic in tutorial.topics %}
                    <span class="topic-tag">{{ topic }}</span>
                    {% endfor %}
                </div>
            </div>
            
            <div class="tutorial-actions">
                <a href="/tutorial/{{ tutorial.id }}" class="btn-primary">
                    {% if tutorial.id in user_progress.tutorials_completed %}
                    Review Tutorial
                    {% else %}
                    Start Learning
                    {% endif %}
                </a>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}''',
            
            'tutorial_detail.html': '''{% extends "base.html" %}

{% block title %}{{ tutorial.title }} - Security Learning Platform{% endblock %}

{% block content %}
<div class="tutorial-detail-page">
    <div class="tutorial-hero">
        <div class="hero-content">
            <h1>{{ tutorial.title }}</h1>
            <p class="tutorial-description">{{ tutorial.description }}</p>
            
            <div class="tutorial-meta">
                <span class="meta-item">
                    <strong>Difficulty:</strong> 
                    <span class="difficulty-badge {{ tutorial.difficulty.lower() }}">{{ tutorial.difficulty }}</span>
                </span>
                <span class="meta-item">
                    <strong>Duration:</strong> {{ tutorial.duration }}
                </span>
                <span class="meta-item">
                    <strong>Steps:</strong> {{ tutorial.steps|length }}
                </span>
            </div>
            
            <div class="learning-objectives">
                <h3>🎯 What You'll Learn</h3>
                <ul>
                    {% for objective in tutorial.learning_objectives %}
                    <li>{{ objective }}</li>
                    {% endfor %}
                </ul>
            </div>
            
            <div class="tutorial-actions">
                <button onclick="startTutorial('{{ tutorial.id }}')" class="btn-primary btn-large">
                    🚀 Start Tutorial
                </button>
            </div>
        </div>
    </div>
    
    <div class="tutorial-outline">
        <h2>📋 Tutorial Outline</h2>
        <div class="steps-list">
            {% for step in tutorial.steps %}
            <div class="step-outline-item">
                <div class="step-number">{{ loop.index }}</div>
                <div class="step-content">
                    <h4>{{ step.title }}</h4>
                    <p>{{ step.step_type.title() }} • {{ step.duration_estimate }}</p>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>

<script>
async function startTutorial(tutorialId) {
    try {
        const response = await fetch(`/api/tutorial/${tutorialId}/start`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({})
        });
        const data = await response.json();
        
        if (data.session_id) {
            // Start with first step
            window.location.href = `/tutorial/${tutorialId}/step/${data.session_id}`;
        }
    } catch (error) {
        console.error('Failed to start tutorial:', error);
    }
}
</script>
{% endblock %}''',
            
            'tutorial_step.html': '''{% extends "base.html" %}

{% block title %}{{ step.title }} - {{ tutorial.title }}{% endblock %}

{% block content %}
<div class="tutorial-step-page">
    <div class="step-header">
        <div class="step-progress">
            <div class="progress-bar">
                <div class="progress-fill" style="width: {{ (loop.index / tutorial.steps|length * 100) }}%"></div>
            </div>
            <span class="progress-text">Step {{ loop.index }} of {{ tutorial.steps|length }}</span>
        </div>
        
        <h1>{{ step.title }}</h1>
        <div class="step-meta">
            <span class="step-type">{{ step.step_type.title() }}</span>
            <span class="duration">⏱️ {{ step.duration_estimate }}</span>
        </div>
    </div>
    
    <div class="step-content">
        {{ step.content|safe }}
    </div>
    
    <div class="step-navigation">
        <button onclick="previousStep()" class="btn-secondary">← Previous</button>
        <button onclick="completeStep()" class="btn-primary">Complete Step →</button>
    </div>
    
    <div class="help-panel">
        <button onclick="requestHint()" class="btn-help">💡 Need a Hint?</button>
        <div id="hint-display" class="hint-container" style="display: none;"></div>
    </div>
</div>

<script>
let currentSession = null;

async function completeStep() {
    try {
        const response = await fetch(`/api/tutorial/{{ tutorial.id }}/step/{{ step.id }}/complete`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({session_id: currentSession})
        });
        const data = await response.json();
        
        if (data.achievements && data.achievements.length > 0) {
            showAchievements(data.achievements);
        }
        
        // Navigate to next step or completion
        // Implementation depends on step navigation logic
    } catch (error) {
        console.error('Failed to complete step:', error);
    }
}

async function requestHint() {
    // WebSocket or API call for hints
    const hintDisplay = document.getElementById('hint-display');
    hintDisplay.style.display = 'block';
    hintDisplay.innerHTML = '<p>💡 Hint: Focus on the key concepts and try the interactive elements!</p>';
}

function showAchievements(achievements) {
    // Show achievement notifications
    achievements.forEach(achievement => {
        const notification = document.createElement('div');
        notification.className = 'achievement-notification';
        notification.innerHTML = `🏆 Achievement Unlocked: ${achievement}`;
        document.body.appendChild(notification);
        
        setTimeout(() => notification.remove(), 5000);
    });
}
</script>
{% endblock %}'''
        }
        
        for filename, content in templates.items():
            template_path = self.templates_dir / filename
            if not template_path.exists():
                with open(template_path, 'w') as f:
                    f.write(content)
    
    def create_static_assets(self):
        """Create CSS and JavaScript files."""
        css_dir = self.static_dir / "css"
        js_dir = self.static_dir / "js"
        css_dir.mkdir(parents=True, exist_ok=True)
        js_dir.mkdir(parents=True, exist_ok=True)
        
        # Create main CSS file
        css_content = '''/* Security Learning Platform Styles */
:root {
    --primary-color: #3b82f6;
    --secondary-color: #64748b;
    --success-color: #10b981;
    --warning-color: #f59e0b;
    --danger-color: #ef4444;
    --background-color: #f8fafc;
    --surface-color: #ffffff;
    --text-color: #1e293b;
    --text-muted: #64748b;
    --border-color: #e2e8f0;
    --border-radius: 8px;
    --shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    background-color: var(--background-color);
    color: var(--text-color);
    line-height: 1.6;
}

/* Navigation */
.navbar {
    background: var(--surface-color);
    border-bottom: 1px solid var(--border-color);
    padding: 1rem 0;
    position: sticky;
    top: 0;
    z-index: 100;
}

.nav-container {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 2rem;
}

.nav-brand {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--primary-color);
    text-decoration: none;
}

.nav-links {
    display: flex;
    gap: 2rem;
}

.nav-links a {
    color: var(--text-muted);
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s;
}

.nav-links a:hover {
    color: var(--primary-color);
}

/* Main Content */
.main-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

/* Dashboard */
.dashboard {
    display: flex;
    flex-direction: column;
    gap: 2rem;
}

.welcome-section {
    text-align: center;
    padding: 3rem 0;
}

.welcome-section h1 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
    color: var(--text-color);
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

.stat-card {
    background: var(--surface-color);
    padding: 2rem;
    border-radius: var(--border-radius);
    text-align: center;
    box-shadow: var(--shadow);
}

.stat-number {
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--primary-color);
    margin-bottom: 0.5rem;
}

.stat-label {
    color: var(--text-muted);
    font-weight: 500;
}

/* Tutorial Cards */
.tutorial-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}

.tutorial-card {
    background: var(--surface-color);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    box-shadow: var(--shadow);
    transition: transform 0.2s, box-shadow 0.2s;
}

.tutorial-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.tutorial-header {
    display: flex;
    justify-content: space-between;
    align-items: start;
    margin-bottom: 1rem;
}

.tutorial-header h3 {
    font-size: 1.25rem;
    color: var(--text-color);
}

.difficulty-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
}

.difficulty-badge.beginner {
    background: #dcfce7;
    color: #166534;
}

.difficulty-badge.intermediate {
    background: #fef3c7;
    color: #92400e;
}

.difficulty-badge.advanced {
    background: #fee2e2;
    color: #991b1b;
}

.tutorial-meta {
    display: flex;
    justify-content: space-between;
    margin: 1rem 0;
    font-size: 0.875rem;
    color: var(--text-muted);
}

/* Buttons */
.btn-primary, .btn-secondary, .btn-help {
    padding: 0.75rem 1.5rem;
    border-radius: var(--border-radius);
    font-weight: 600;
    text-decoration: none;
    display: inline-block;
    transition: all 0.2s;
    border: none;
    cursor: pointer;
}

.btn-primary {
    background: var(--primary-color);
    color: white;
}

.btn-primary:hover {
    background: #2563eb;
}

.btn-secondary {
    background: var(--border-color);
    color: var(--text-color);
}

.btn-secondary:hover {
    background: #cbd5e1;
}

.btn-help {
    background: var(--warning-color);
    color: white;
    font-size: 0.875rem;
}

.btn-large {
    padding: 1rem 2rem;
    font-size: 1.1rem;
}

/* Tutorial Steps */
.step-header {
    margin-bottom: 2rem;
}

.progress-bar {
    width: 100%;
    height: 8px;
    background: var(--border-color);
    border-radius: 9999px;
    overflow: hidden;
    margin-bottom: 1rem;
}

.progress-fill {
    height: 100%;
    background: var(--primary-color);
    transition: width 0.3s;
}

.progress-text {
    font-size: 0.875rem;
    color: var(--text-muted);
}

.step-content {
    background: var(--surface-color);
    padding: 2rem;
    border-radius: var(--border-radius);
    box-shadow: var(--shadow);
    margin-bottom: 2rem;
}

.lesson-content h3 {
    color: var(--primary-color);
    margin-bottom: 1rem;
}

.lesson-content p {
    margin-bottom: 1rem;
}

.lesson-content ul {
    margin-left: 1.5rem;
    margin-bottom: 1rem;
}

.info-box {
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: var(--border-radius);
    padding: 1rem;
    margin: 1rem 0;
}

/* Interactive Elements */
.packet-diagram {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin: 1rem 0;
    font-family: monospace;
}

.packet-header, .packet-data {
    padding: 0.75rem;
    border-radius: var(--border-radius);
    text-align: center;
    font-weight: 600;
}

.packet-header {
    background: #dbeafe;
    color: #1e40af;
}

.packet-data {
    background: #fef3c7;
    color: #92400e;
}

.tools-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

.tool-card {
    border: 2px solid var(--border-color);
    border-radius: var(--border-radius);
    padding: 1.5rem;
    transition: border-color 0.2s;
}

.tool-card:hover {
    border-color: var(--primary-color);
}

.tool-card h4 {
    color: var(--primary-color);
    margin-bottom: 0.5rem;
}

.tool-role {
    font-weight: 600;
    color: var(--text-muted);
    margin-bottom: 1rem;
}

.tool-analogy {
    font-style: italic;
    color: var(--text-muted);
    margin-top: 1rem;
}

/* Achievements */
.achievement-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: var(--success-color);
    color: white;
    padding: 1rem 1.5rem;
    border-radius: var(--border-radius);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 1000;
    animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* Responsive Design */
@media (max-width: 768px) {
    .nav-container {
        padding: 0 1rem;
    }
    
    .main-content {
        padding: 1rem;
    }
    
    .stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .tutorial-grid {
        grid-template-columns: 1fr;
    }
    
    .tools-grid {
        grid-template-columns: 1fr;
    }
}'''
        
        css_file = css_dir / "styles.css"
        if not css_file.exists():
            with open(css_file, 'w') as f:
                f.write(css_content)
        
        # Create main JavaScript file
        js_content = '''// Security Learning Platform JavaScript

// WebSocket connection for real-time features
let ws = null;
let currentSession = null;

// Initialize WebSocket connection
function initWebSocket(sessionId) {
    if (ws) {
        ws.close();
    }
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws/${sessionId}`);
    
    ws.onopen = function() {
        console.log('WebSocket connected');
        currentSession = sessionId;
    };
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    ws.onclose = function() {
        console.log('WebSocket disconnected');
        // Attempt to reconnect after 5 seconds
        setTimeout(() => {
            if (currentSession) {
                initWebSocket(currentSession);
            }
        }, 5000);
    };
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'progress_update':
            updateProgressDisplay(data.progress);
            break;
        case 'hint':
            displayHint(data.hints);
            break;
        case 'achievement':
            showAchievement(data.achievement);
            break;
    }
}

// Network traffic simulation
function startTrafficDemo() {
    const display = document.getElementById('traffic-display');
    if (!display) return;
    
    display.innerHTML = '<div class="traffic-header">Live Network Traffic Simulation</div>';
    
    const packets = [
        {time: '10:30:15', src: '192.168.1.100', dst: 'google.com', proto: 'HTTPS', info: 'Web browsing'},
        {time: '10:30:16', src: '192.168.1.100', dst: 'mail.company.com', proto: 'SMTP', info: 'Sending email'},
        {time: '10:30:17', src: '192.168.1.100', dst: 'cdn.example.com', proto: 'HTTP', info: 'Loading images'},
        {time: '10:30:18', src: '203.0.113.15', dst: '192.168.1.100', proto: 'TCP', info: 'Port scan attempt', threat: true},
        {time: '10:30:19', src: '192.168.1.100', dst: 'update.microsoft.com', proto: 'HTTPS', info: 'Windows update'}
    ];
    
    packets.forEach((packet, index) => {
        setTimeout(() => {
            const packetDiv = document.createElement('div');
            packetDiv.className = `packet-entry ${packet.threat ? 'threat' : 'normal'}`;
            packetDiv.innerHTML = `
                <span class="packet-time">${packet.time}</span>
                <span class="packet-src">${packet.src}</span>
                <span class="packet-dst">${packet.dst}</span>
                <span class="packet-proto">${packet.proto}</span>
                <span class="packet-info">${packet.info}</span>
                ${packet.threat ? '<span class="threat-indicator">🚨</span>' : ''}
            `;
            display.appendChild(packetDiv);
            
            if (packet.threat) {
                packetDiv.style.background = '#fee2e2';
                packetDiv.style.border = '2px solid #ef4444';
            }
        }, index * 1000);
    });
}

// EICAR file creation simulation
async function createEicarFile() {
    const statusEl = document.getElementById('create-status');
    const detectionEl = document.getElementById('detection-display');
    const resultsEl = document.getElementById('results-panel');
    
    if (!statusEl) return;
    
    // Step 1: Creating file
    statusEl.innerHTML = '🔄 Creating EICAR test file...';
    statusEl.className = 'step-status creating';
    
    setTimeout(() => {
        statusEl.innerHTML = '✅ EICAR test file created!';
        statusEl.className = 'step-status success';
        
        // Step 2: Detection simulation
        if (detectionEl) {
            detectionEl.innerHTML = `
                <div class="scanning-status active">🔍 YARA scanner processing file...</div>
                <div class="detection-progress">
                    <div class="progress-bar">
                        <div class="progress-fill scanning"></div>
                    </div>
                </div>
            `;
        }
        
        // Step 3: Show detection results
        setTimeout(() => {
            if (detectionEl) {
                detectionEl.innerHTML = `
                    <div class="detection-alert">
                        🚨 THREAT DETECTED!
                        <div class="alert-details">
                            File: eicar_test.txt<br>
                            Rule: EICAR_Test_File<br>
                            Severity: HIGH
                        </div>
                    </div>
                `;
            }
            
            if (resultsEl) {
                resultsEl.innerHTML = `
                    <div class="detection-results">
                        <h4>🔍 Detection Analysis</h4>
                        <div class="result-field">
                            <strong>File Path:</strong> /extracted_files/eicar_test.txt
                        </div>
                        <div class="result-field">
                            <strong>YARA Rule:</strong> EICAR_Test_File
                        </div>
                        <div class="result-field">
                            <strong>Threat Type:</strong> Test File / Malware Signature
                        </div>
                        <div class="result-field">
                            <strong>Confidence:</strong> 100% (Perfect Match)
                        </div>
                        <div class="result-field">
                            <strong>Recommended Action:</strong> File quarantined for analysis
                        </div>
                    </div>
                `;
            }
        }, 2000);
    }, 1500);
}

// Quiz functionality
let currentQuestion = 1;
let quizAnswers = {};

function nextQuestion() {
    const currentQ = document.querySelector(`[data-question="${currentQuestion}"]`);
    const selectedAnswer = document.querySelector(`input[name="q${currentQuestion}"]:checked`);
    
    if (!selectedAnswer) {
        alert('Please select an answer before continuing.');
        return;
    }
    
    quizAnswers[`q${currentQuestion}`] = selectedAnswer.value;
    currentQ.style.display = 'none';
    
    currentQuestion++;
    const nextQ = document.querySelector(`[data-question="${currentQuestion}"]`);
    
    if (nextQ) {
        nextQ.style.display = 'block';
        document.getElementById('quiz-next').disabled = true;
    } else {
        // Show submit button
        document.getElementById('quiz-next').style.display = 'none';
        document.getElementById('quiz-submit').style.display = 'inline-block';
    }
}

function submitQuiz() {
    const lastQuestion = document.querySelector(`[data-question="${currentQuestion}"]`);
    const selectedAnswer = document.querySelector(`input[name="q${currentQuestion}"]:checked`);
    
    if (!selectedAnswer) {
        alert('Please select an answer before submitting.');
        return;
    }
    
    quizAnswers[`q${currentQuestion}`] = selectedAnswer.value;
    
    // Hide last question
    lastQuestion.style.display = 'none';
    
    // Calculate score (simplified)
    const correctAnswers = {q1: 'b', q2: 'b', q3: 'c'};
    let score = 0;
    
    Object.keys(correctAnswers).forEach(question => {
        if (quizAnswers[question] === correctAnswers[question]) {
            score++;
        }
    });
    
    // Show results
    const resultsDiv = document.querySelector('.quiz-results');
    const scoreDiv = document.getElementById('quiz-score');
    const feedbackDiv = document.getElementById('quiz-feedback');
    
    resultsDiv.style.display = 'block';
    scoreDiv.innerHTML = `Your Score: ${score}/3 (${Math.round(score/3*100)}%)`;
    
    if (score === 3) {
        feedbackDiv.innerHTML = '<p class="excellent">🎉 Excellent! Perfect score!</p>';
    } else if (score >= 2) {
        feedbackDiv.innerHTML = '<p class="good">👏 Good job! You understand the key concepts.</p>';
    } else {
        feedbackDiv.innerHTML = '<p class="needs-improvement">📚 Keep learning! Review the material and try again.</p>';
    }
    
    // Show completion section
    const completionSection = document.getElementById('completion-section');
    if (completionSection) {
        setTimeout(() => {
            completionSection.style.display = 'block';
        }, 2000);
    }
}

// Enable quiz navigation when answer is selected
document.addEventListener('change', function(e) {
    if (e.target.type === 'radio') {
        document.getElementById('quiz-next').disabled = false;
    }
});

// Threat identification exercise
document.addEventListener('click', function(e) {
    if (e.target.closest('.log-entry')) {
        const entry = e.target.closest('.log-entry');
        const isThreat = entry.dataset.threat === 'true';
        const feedbackEl = document.getElementById('exercise-feedback');
        
        entry.classList.add('selected');
        
        if (isThreat) {
            entry.classList.add('correct-selection');
            feedbackEl.innerHTML += `<div class="feedback-item correct">✅ Correct! This is suspicious activity.</div>`;
        } else {
            entry.classList.add('incorrect-selection');
            feedbackEl.innerHTML += `<div class="feedback-item incorrect">❌ This is normal network activity.</div>`;
        }
        
        // Disable further clicks on this entry
        entry.style.pointerEvents = 'none';
    }
});

// Initialize page functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add any page-specific initialization here
    console.log('Security Learning Platform loaded');
});'''
        
        js_file = js_dir / "main.js"
        if not js_file.exists():
            with open(js_file, 'w') as f:
                f.write(js_content)
    
    def create_initial_templates(self):
        """Create initial HTML templates if they don't exist."""
        # Create base template
        base_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Security Learning Platform{% endblock %}</title>
    <link href="/static/css/styles.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <a href="/" class="nav-brand">🛡️ Security Learning Platform</a>
            <div class="nav-links">
                <a href="/tutorials">Tutorials</a>
                <a href="/api/progress">Progress</a>
                <a href="/api/achievements">Achievements</a>
            </div>
        </div>
    </nav>
    
    <main class="main-content">
        {% block content %}{% endblock %}
    </main>
    
    <script src="/static/js/main.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>'''
        
        base_path = self.templates_dir / "base.html"
        if not base_path.exists():
            with open(base_path, 'w') as f:
                f.write(base_template)
    
    def create_static_assets(self):
        """Create CSS and JavaScript files."""
        css_dir = self.static_dir / "css"
        js_dir = self.static_dir / "js"
        css_dir.mkdir(parents=True, exist_ok=True)
        js_dir.mkdir(parents=True, exist_ok=True)
        
        # Basic CSS file
        css_content = '''/* Security Learning Platform Styles */
body {
    font-family: 'Inter', sans-serif;
    margin: 0;
    padding: 0;
    background: #f8fafc;
    color: #1e293b;
}

.navbar {
    background: white;
    border-bottom: 1px solid #e2e8f0;
    padding: 1rem 0;
}

.nav-container {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 2rem;
}

.nav-brand {
    font-size: 1.25rem;
    font-weight: 600;
    color: #3b82f6;
    text-decoration: none;
}

.nav-links a {
    color: #64748b;
    text-decoration: none;
    margin-left: 2rem;
}

.main-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

.btn-primary {
    background: #3b82f6;
    color: white;
    padding: 0.75rem 1.5rem;
    border: none;
    border-radius: 0.5rem;
    text-decoration: none;
    display: inline-block;
    font-weight: 600;
    cursor: pointer;
}

.btn-primary:hover {
    background: #2563eb;
}'''
        
        css_file = css_dir / "styles.css"
        if not css_file.exists():
            with open(css_file, 'w') as f:
                f.write(css_content)
        
        # Basic JavaScript file
        js_content = '''// Security Learning Platform JavaScript
console.log('Security Learning Platform loaded');

// Basic tutorial functionality
function startTutorial(tutorialId) {
    console.log('Starting tutorial:', tutorialId);
}'''
        
        js_file = js_dir / "main.js"
        if not js_file.exists():
            with open(js_file, 'w') as f:
                f.write(js_content)
    
    def create_initial_templates(self):
        """Create initial HTML templates if they don't exist."""
        # Create basic templates
        pass
    
    def create_static_assets(self):
        """Create CSS and JavaScript files."""
        # Create basic assets
        pass
    
    def run(self, host: str = "127.0.0.1", port: int = 8001):
        """Run the tutorial web server."""
        self.logger.info(f"Starting tutorial web server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port, log_level="info")


    def create_initial_templates(self):
        """Create initial HTML templates if they don't exist."""
        # Templates are already created as separate files
        print(f"Templates directory: {self.templates_dir}")
        
    def create_static_assets(self):
        """Create CSS and JavaScript files."""
        # Static assets are already created as separate files
        print(f"Static assets directory: {self.static_dir}")


def main():
    """Main function to start the tutorial web server."""
    import sys
    from pathlib import Path
    
    # Example configuration
    config = {
        'PROJECT_ROOT': Path(__file__).parent.parent,
        'EXPERIENCE_LEVEL': 'beginner',
        'TUTORIAL_MODE': True,
        'WEB_INTERFACE': True
    }
    
    server = TutorialWebServer(config)
    
    # Create templates and static files if they don't exist
    server.create_initial_templates()
    server.create_static_assets()
    
    try:
        server.run()
    except KeyboardInterrupt:
        print("\nTutorial server stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()