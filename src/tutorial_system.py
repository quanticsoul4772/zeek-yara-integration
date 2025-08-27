#!/usr/bin/env python3
"""
Interactive Tutorial System for Educational Security Platform
Provides step-by-step guided learning experiences
"""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


@dataclass
class TutorialStep:
    """Represents a single tutorial step."""

    id: str
    title: str
    content: str
    action: str
    duration_estimate: str
    prerequisites: List[str]
    learning_objectives: List[str]
    verification_check: Optional[str] = None
    next_steps: List[str] = None


class TutorialManager:
    """Manages interactive tutorials and learning progress."""

    def __init__(self, config: Dict, console: Optional[Console] = None):
        self.config = config
        self.console = console or (Console() if RICH_AVAILABLE else None)
        self.project_root = Path(config.get("PROJECT_ROOT", "."))
        self.tutorial_data_path = self.project_root / "EDUCATION" / "tutorials"
        self.progress_file = self.project_root / "user_progress.json"
        self.current_tutorial = None
        self.user_progress = self.load_user_progress()

    def load_user_progress(self) -> Dict:
        """Load user's learning progress."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass

        return {
            "tutorials_completed": [],
            "current_tutorial": None,
            "achievements": [],
            "total_time_spent": 0,
            "experience_points": 0,
        }

    def save_user_progress(self):
        """Save user's learning progress."""
        try:
            self.progress_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.progress_file, "w") as f:
                json.dump(self.user_progress, f, indent=2)
        except Exception as e:
            self.log(f"Failed to save progress: {e}", "warning")

    def get_available_tutorials(self) -> List[Dict]:
        """Get list of available tutorials based on experience level."""
        try:
            experience_level = self.config.get("EXPERIENCE_LEVEL", "beginner")
        except Exception:
            experience_level = "beginner"

        tutorials = {
            "beginner": [
                {
                    "id": "network_security_basics",
                    "title": "Network Security Fundamentals",
                    "description": "Learn the basics of network security monitoring",
                    "duration": "15 minutes",
                    "difficulty": "Beginner",
                    "topics": [
                        "Network Traffic",
                        "Security Monitoring",
                        "Threat Detection",
                    ],
                },
                {
                    "id": "first_detection",
                    "title": "Your First Threat Detection",
                    "description": "Detect malware using YARA rules and EICAR test file",
                    "duration": "10 minutes",
                    "difficulty": "Beginner",
                    "topics": ["YARA Rules", "Malware Detection", "Test Files"],
                },
                {
                    "id": "zeek_basics",
                    "title": "Network Monitoring with Zeek",
                    "description": "Monitor network traffic and extract files",
                    "duration": "20 minutes",
                    "difficulty": "Beginner",
                    "topics": ["Zeek", "Network Analysis", "File Extraction"],
                },
                {
                    "id": "suricata_intro",
                    "title": "Intrusion Detection with Suricata",
                    "description": "Detect network intrusions and attacks",
                    "duration": "20 minutes",
                    "difficulty": "Beginner",
                    "topics": ["Suricata", "IDS", "Network Security"],
                },
            ],
            "intermediate": [
                {
                    "id": "custom_yara_rules",
                    "title": "Writing Custom YARA Rules",
                    "description": "Create your own malware detection rules",
                    "duration": "30 minutes",
                    "difficulty": "Intermediate",
                    "topics": ["YARA", "Rule Writing", "Pattern Matching"],
                },
                {
                    "id": "correlation_analysis",
                    "title": "Alert Correlation and Analysis",
                    "description": "Correlate alerts from multiple security tools",
                    "duration": "25 minutes",
                    "difficulty": "Intermediate",
                    "topics": ["Alert Correlation", "Analysis", "Investigation"],
                },
            ],
            "advanced": [
                {
                    "id": "tool_integration",
                    "title": "Advanced Tool Integration",
                    "description": "Integrate additional security tools and customize workflows",
                    "duration": "45 minutes",
                    "difficulty": "Advanced",
                    "topics": ["Integration", "Customization", "Automation"],
                }
            ],
        }

        # Ensure we always return at least some tutorials for CI environments
        result_tutorials = tutorials.get(experience_level, tutorials["beginner"])

        # Fallback to ensure tutorials are always available
        if not result_tutorials:
            result_tutorials = tutorials["beginner"]

        # Final safety check - create minimal tutorials if still empty
        if not result_tutorials:
            result_tutorials = [
                {
                    "id": "quick_start",
                    "title": "Quick Start Guide",
                    "description": "Basic platform introduction",
                    "duration": "5 minutes",
                    "difficulty": "Beginner",
                    "topics": ["Setup", "Overview"],
                },
                {
                    "id": "basic_detection",
                    "title": "Basic Detection",
                    "description": "Simple threat detection example",
                    "duration": "10 minutes",
                    "difficulty": "Beginner",
                    "topics": ["Detection", "YARA"],
                },
                {
                    "id": "dashboard_intro",
                    "title": "Dashboard Introduction",
                    "description": "Navigate the security dashboard",
                    "duration": "5 minutes",
                    "difficulty": "Beginner",
                    "topics": ["Dashboard", "UI"],
                },
                {
                    "id": "getting_help",
                    "title": "Getting Help",
                    "description": "Find support resources",
                    "duration": "3 minutes",
                    "difficulty": "Beginner",
                    "topics": ["Support", "Resources"],
                },
            ]

        return result_tutorials

    def show_tutorial_menu(self) -> Optional[str]:
        """Show tutorial selection menu."""
        tutorials = self.get_available_tutorials()

        if self.console:
            # Create tutorial selection table
            table = Table(title="📚 Available Tutorials")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="green")
            table.add_column("Duration", style="yellow")
            table.add_column("Status", style="blue")

            for i, tutorial in enumerate(tutorials, 1):
                status = (
                    "✅ Completed"
                    if tutorial["id"] in self.user_progress["tutorials_completed"]
                    else "📝 Available"
                )
                table.add_row(str(i), tutorial["title"], tutorial["duration"], status)

            self.console.print(table)

            choices = [str(i) for i in range(1, len(tutorials) + 1)] + ["0"]
            choice = Prompt.ask(
                "Select a tutorial (0 to return to main menu)",
                choices=choices,
                default="1",
            )
        else:
            print("\nAvailable Tutorials:")
            print("-" * 50)
            for i, tutorial in enumerate(tutorials, 1):
                status = (
                    "✅ Completed"
                    if tutorial["id"] in self.user_progress["tutorials_completed"]
                    else "📝 Available"
                )
                print(f"{i}. {tutorial['title']} ({tutorial['duration']}) - {status}")
            print("0. Return to main menu")

            choice = input("Select a tutorial: ").strip()

        if choice == "0":
            return None

        try:
            tutorial_index = int(choice) - 1
            if 0 <= tutorial_index < len(tutorials):
                return tutorials[tutorial_index]["id"]
        except ValueError:
            pass

        return None

    def create_tutorial_steps(self, tutorial_id: str) -> List[TutorialStep]:
        """Create tutorial steps for a specific tutorial."""
        steps = {
            "network_security_basics": [
                TutorialStep(
                    id="intro",
                    title="Welcome to Network Security!",
                    content="""
🎓 Network Security Fundamentals

Network security is about protecting your network and data from threats.
In this tutorial, you'll learn:

• What network security monitoring is
• How security tools work together
• Common types of network threats
• How to detect and respond to incidents

This knowledge forms the foundation for everything else you'll learn!
                    """,
                    action="introduction",
                    duration_estimate="2 minutes",
                    prerequisites=[],
                    learning_objectives=[
                        "Understand basic network security concepts",
                        "Learn about security monitoring",
                        "Recognize common network threats",
                    ],
                ),
                TutorialStep(
                    id="network_basics",
                    title="Understanding Network Traffic",
                    content="""
🌐 Network Traffic Basics

Every device on a network communicates by sending packets of data.
These packets contain:

• Source and destination addresses (like postal addresses)
• The type of communication (web browsing, email, file transfer)
• The actual data being sent

Security monitoring watches this traffic to spot suspicious activity,
just like a security guard watching who enters and leaves a building.
                    """,
                    action="explain_network_traffic",
                    duration_estimate="3 minutes",
                    prerequisites=["intro"],
                    learning_objectives=[
                        "Understand network packet structure",
                        "Learn about network communication",
                        "Recognize the role of traffic monitoring",
                    ],
                ),
                TutorialStep(
                    id="security_tools",
                    title="Your Security Toolkit",
                    content="""
🛠️ Security Tools Overview

This platform uses three main security tools:

1. **Zeek** - Network traffic analyzer
   • Monitors all network communications
   • Extracts files sent over the network
   • Creates detailed logs of network activity

2. **YARA** - Malware detection engine
   • Scans files for malicious patterns
   • Uses rules to identify known threats
   • Can detect new variants of known malware

3. **Suricata** - Intrusion detection system
   • Monitors for attack patterns
   • Blocks malicious traffic
   • Generates real-time alerts

Together, they provide comprehensive protection!
                    """,
                    action="demonstrate_tools",
                    duration_estimate="5 minutes",
                    prerequisites=["network_basics"],
                    learning_objectives=[
                        "Understand each tool's purpose",
                        "Learn how tools complement each other",
                        "See tools in action",
                    ],
                ),
                TutorialStep(
                    id="threat_types",
                    title="Common Network Threats",
                    content="""
⚠️ Types of Network Threats

Understanding common threats helps you recognize them:

1. **Malware** - Malicious software
   • Viruses, trojans, ransomware
   • Spread through email, downloads, or network
   • YARA helps detect these

2. **Network Intrusions** - Unauthorized access attempts
   • Port scans, brute force attacks
   • Exploitation of vulnerabilities
   • Suricata detects these patterns

3. **Data Exfiltration** - Stealing sensitive data
   • Large file transfers to external servers
   • Encrypted communications to hide theft
   • Zeek can spot unusual traffic patterns

4. **Command & Control** - Remote malware communication
   • Infected computers calling home
   • Receiving commands from attackers
   • All three tools can detect C&C traffic
                    """,
                    action="show_threat_examples",
                    duration_estimate="4 minutes",
                    prerequisites=["security_tools"],
                    learning_objectives=[
                        "Identify common threat types",
                        "Understand threat detection methods",
                        "Recognize attack indicators",
                    ],
                ),
                TutorialStep(
                    id="summary",
                    title="Putting It All Together",
                    content="""
🎯 Network Security Summary

You now understand the fundamentals:

✅ **Network traffic** carries all communications
✅ **Security tools** monitor different aspects of network activity
✅ **Threats** come in many forms but have detectable patterns
✅ **Layered defense** using multiple tools provides better protection

Next steps:
• Try the "First Threat Detection" tutorial
• Explore the web dashboard
• Practice with real examples

Remember: Security is a continuous learning process!
                    """,
                    action="complete_tutorial",
                    duration_estimate="1 minute",
                    prerequisites=["threat_types"],
                    learning_objectives=[
                        "Summarize key learning points",
                        "Plan next learning steps",
                        "Gain confidence in security concepts",
                    ],
                ),
            ],
            "first_detection": [
                TutorialStep(
                    id="eicar_intro",
                    title="EICAR Test File",
                    content="""
🧪 Safe Malware Testing with EICAR

The EICAR (European Institute for Computer Antivirus Research) test file
is a harmless file that all antivirus programs detect as "malware."

It's perfect for testing because:
• It's completely safe - contains no actual malware
• All security tools recognize it
• It helps verify your detection systems work

We'll use EICAR to trigger our YARA detection rules safely!
                    """,
                    action="explain_eicar",
                    duration_estimate="2 minutes",
                    prerequisites=[],
                    learning_objectives=[
                        "Understand EICAR test file purpose",
                        "Learn about safe testing practices",
                        "Prepare for first detection",
                    ],
                ),
                TutorialStep(
                    id="create_detection",
                    title="Creating the Test Detection",
                    content="""
🚨 Let's Trigger a Detection!

We'll create an EICAR test file and watch our security tools detect it.

This demonstrates the complete detection workflow:
1. File appears in monitored directory
2. YARA scanner processes the file
3. YARA rules match the EICAR signature
4. Alert is generated and logged
5. Results appear in dashboard

Ready to see your first threat detection?
                    """,
                    action="create_eicar_file",
                    duration_estimate="3 minutes",
                    prerequisites=["eicar_intro"],
                    learning_objectives=[
                        "Execute first malware detection",
                        "Observe detection workflow",
                        "Understand alert generation",
                    ],
                ),
                TutorialStep(
                    id="analyze_results",
                    title="Analyzing Detection Results",
                    content="""
📊 Understanding Your Detection Results

Great! You just detected your first "threat". Let's analyze what happened:

The detection log shows:
• **File name and path** - Where the threat was found
• **Rule that matched** - Which YARA rule detected it
• **Threat classification** - Type of malware detected
• **Confidence level** - How certain the detection is
• **Timestamp** - When the detection occurred

This information helps security analysts investigate and respond to threats.
                    """,
                    action="show_detection_analysis",
                    duration_estimate="4 minutes",
                    prerequisites=["create_detection"],
                    learning_objectives=[
                        "Interpret detection results",
                        "Understand alert components",
                        "Learn analysis techniques",
                    ],
                ),
                TutorialStep(
                    id="detection_complete",
                    title="Congratulations!",
                    content="""
🎉 Your First Detection Complete!

You've successfully:
✅ Created a test malware file (EICAR)
✅ Triggered YARA detection rules
✅ Generated a security alert
✅ Analyzed the detection results

This is exactly how real malware detection works, but with actual threats!

Next steps:
• Try the Zeek network monitoring tutorial
• Explore more YARA rules
• Practice with different file types

You're on your way to becoming a security analyst!
                    """,
                    action="complete_detection_tutorial",
                    duration_estimate="1 minute",
                    prerequisites=["analyze_results"],
                    learning_objectives=[
                        "Celebrate first achievement",
                        "Plan next learning steps",
                        "Build confidence in detection capabilities",
                    ],
                ),
            ],
        }

        return steps.get(tutorial_id, [])

    def run_tutorial(self, tutorial_id: str) -> bool:
        """Run a specific tutorial."""
        self.current_tutorial = tutorial_id
        steps = self.create_tutorial_steps(tutorial_id)

        if not steps:
            self.log(f"Tutorial '{tutorial_id}' not found", "error")
            return False

        self.log(f"Starting tutorial: {tutorial_id}")
        start_time = time.time()

        try:
            for i, step in enumerate(steps):
                if not self.run_tutorial_step(step, i + 1, len(steps)):
                    self.log("Tutorial cancelled by user")
                    return False

            # Mark tutorial as completed
            if tutorial_id not in self.user_progress["tutorials_completed"]:
                self.user_progress["tutorials_completed"].append(tutorial_id)
                self.user_progress["experience_points"] += 100
                self.check_achievements()

            elapsed_time = time.time() - start_time
            self.user_progress["total_time_spent"] += elapsed_time
            self.save_user_progress()

            self.log(f"Tutorial completed successfully! +100 XP", "success")
            return True

        except KeyboardInterrupt:
            self.log("Tutorial interrupted by user")
            return False
        except Exception as e:
            self.log(f"Tutorial error: {e}", "error")
            return False

    def run_tutorial_step(
        self, step: TutorialStep, step_num: int, total_steps: int
    ) -> bool:
        """Run a single tutorial step."""
        if self.console:
            # Show step panel
            panel = Panel(
                step.content.strip(),
                title=f"📚 {step.title} (Step {step_num}/{total_steps})",
                subtitle=f"⏱️ Estimated time: {step.duration_estimate}",
                border_style="blue",
                padding=(1, 2),
            )
            self.console.print(panel)

            # Show learning objectives if available
            if step.learning_objectives:
                objectives_text = "\n".join(
                    [f"• {obj}" for obj in step.learning_objectives]
                )
                objectives_panel = Panel(
                    objectives_text,
                    title="🎯 Learning Objectives",
                    border_style="green",
                    padding=(0, 1),
                )
                self.console.print(objectives_panel)
        else:
            print(f"\n=== {step.title} (Step {step_num}/{total_steps}) ===")
            print(step.content.strip())
            print(f"\nEstimated time: {step.duration_estimate}")

            if step.learning_objectives:
                print("\nLearning Objectives:")
                for obj in step.learning_objectives:
                    print(f"• {obj}")

        # Execute step action
        self.execute_step_action(step.action, step)

        # Ask user to continue (except for last step)
        if step_num < total_steps:
            if self.console:
                return Confirm.ask("Continue to next step?", default=True)
            else:
                response = input("\nContinue to next step? (y/n) [y]: ").strip().lower()
                return response != "n"

        return True

    def execute_step_action(self, action: str, step: TutorialStep):
        """Execute the action for a tutorial step."""
        try:
            if action == "introduction":
                self.show_welcome_message()
            elif action == "explain_network_traffic":
                self.demonstrate_network_concepts()
            elif action == "demonstrate_tools":
                self.show_tools_demonstration()
            elif action == "show_threat_examples":
                self.display_threat_examples()
            elif action == "complete_tutorial":
                self.show_completion_message()
            elif action == "explain_eicar":
                self.explain_eicar_file()
            elif action == "create_eicar_file":
                self.create_and_scan_eicar()
            elif action == "show_detection_analysis":
                self.analyze_detection_results()
            elif action == "complete_detection_tutorial":
                self.show_detection_completion()
            else:
                self.log(f"Unknown action: {action}", "warning")
        except Exception as e:
            self.log(f"Action execution failed: {e}", "error")

    def show_welcome_message(self):
        """Show tutorial welcome message."""
        if self.console:
            welcome_text = Text(
                "Welcome to your security learning journey! 🚀", style="bold green"
            )
            self.console.print(welcome_text)
            self.console.print(
                "You're about to learn skills used by professional security analysts."
            )
        else:
            print("Welcome to your security learning journey!")
            print(
                "You're about to learn skills used by professional security analysts."
            )

    def demonstrate_network_concepts(self):
        """Demonstrate basic network concepts."""
        if self.console:
            # Create a simple network traffic visualization
            network_table = Table(title="Sample Network Traffic")
            network_table.add_column("Time", style="cyan")
            network_table.add_column("Source", style="green")
            network_table.add_column("Destination", style="yellow")
            network_table.add_column("Protocol", style="blue")
            network_table.add_column("Info", style="white")

            network_table.add_row(
                "10:30:01", "192.168.1.100", "google.com", "HTTPS", "Web browsing"
            )
            network_table.add_row(
                "10:30:02", "192.168.1.100", "mail.example.com", "SMTP", "Sending email"
            )
            network_table.add_row(
                "10:30:05", "192.168.1.100", "malicious.site", "HTTP", "🚨 Suspicious!"
            )

            self.console.print(network_table)
            self.console.print(
                "Notice how we can see all network communications and spot suspicious activity!"
            )
        else:
            print("\nExample Network Traffic:")
            print("Time      Source          Destination      Protocol  Info")
            print("-" * 60)
            print("10:30:01  192.168.1.100   google.com       HTTPS     Web browsing")
            print("10:30:02  192.168.1.100   mail.example.com SMTP      Sending email")
            print("10:30:05  192.168.1.100   malicious.site   HTTP      🚨 Suspicious!")
            print(
                "\nNotice how we can see all network communications and spot suspicious activity!"
            )

    def show_tools_demonstration(self):
        """Demonstrate how security tools work."""
        self.log("Each tool has a specific role in your security monitoring:")
        self.log("• Zeek: 'I see a file being downloaded...'")
        self.log("• YARA: 'Let me check if this file is malicious...'")
        self.log(
            "• Suricata: 'I'm watching for attack patterns in the network traffic...'"
        )
        self.log("Together they provide comprehensive protection!", "success")

    def display_threat_examples(self):
        """Display examples of different threat types."""
        if self.console:
            threat_table = Table(title="Common Network Threats")
            threat_table.add_column("Threat Type", style="red")
            threat_table.add_column("Example", style="yellow")
            threat_table.add_column("Detection Method", style="green")

            threat_table.add_row("Malware", "virus.exe downloaded", "YARA rules")
            threat_table.add_row(
                "Port Scan", "Probing ports 1-1000", "Suricata patterns"
            )
            threat_table.add_row(
                "Data Theft", "Large file upload", "Zeek traffic analysis"
            )
            threat_table.add_row(
                "C&C Communication", "Regular beacons to attacker", "All tools combined"
            )

            self.console.print(threat_table)
        else:
            print("\nCommon Network Threats:")
            print("• Malware: virus.exe downloaded → Detected by YARA rules")
            print("• Port Scan: Probing ports 1-1000 → Detected by Suricata patterns")
            print("• Data Theft: Large file upload → Detected by Zeek traffic analysis")
            print(
                "• C&C Communication: Regular beacons → Detected by all tools combined"
            )

    def show_completion_message(self):
        """Show tutorial completion message."""
        self.log(
            "🎉 Congratulations! You've completed the Network Security Fundamentals tutorial!",
            "success",
        )
        self.log("You now understand the basics of network security monitoring.")
        self.log("Ready to try detecting some actual threats?")

    def explain_eicar_file(self):
        """Explain the EICAR test file."""
        eicar_signature = (
            "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
        )

        self.log("The EICAR test file contains this harmless text string:")
        self.log(f"'{eicar_signature}'")
        self.log(
            "Even though it's just text, all antivirus tools treat it as malware for testing!"
        )

    def create_and_scan_eicar(self):
        """Create EICAR file and demonstrate detection."""
        extract_dir = Path(self.config.get("EXTRACT_DIR", "/tmp"))
        eicar_path = extract_dir / "eicar_test.txt"
        eicar_content = (
            "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
        )

        try:
            # Ensure directory exists
            extract_dir.mkdir(parents=True, exist_ok=True)

            self.log("Creating EICAR test file...")

            # Create the file
            with open(eicar_path, "w") as f:
                f.write(eicar_content)

            self.log(f"✅ Created test file: {eicar_path}", "success")
            self.log("🔍 YARA scanner should detect this file shortly...")
            self.log("💡 Check the web dashboard to see the detection alert!")

            # Give user time to observe
            if self.console:
                Prompt.ask("Press Enter after checking the dashboard", default="")
            else:
                input("Press Enter after checking the dashboard...")

        except Exception as e:
            self.log(f"Failed to create test file: {e}", "error")

    def analyze_detection_results(self):
        """Analyze and explain detection results."""
        self.log("📊 Analyzing your detection results...")
        self.log("In a real detection, you would see:")
        self.log("• File path: Where the malware was found")
        self.log("• YARA rule: Which rule detected the threat")
        self.log("• Risk level: How dangerous the threat is")
        self.log("• Recommended action: What to do next")
        self.log("This information helps security teams respond quickly!")

    def show_detection_completion(self):
        """Show detection tutorial completion."""
        self.log(
            "🎉 Excellent work! You've completed your first threat detection!",
            "success",
        )
        self.log("You now know how to:")
        self.log("✅ Create test files for security validation")
        self.log("✅ Trigger malware detection systems")
        self.log("✅ Interpret detection results")
        self.log("✅ Use the security dashboard")
        self.log("Ready for more advanced tutorials?")

    def check_achievements(self):
        """Check for and award achievements."""
        achievements = []
        completed_count = len(self.user_progress["tutorials_completed"])
        total_time = self.user_progress["total_time_spent"]

        # Tutorial completion achievements
        if (
            completed_count >= 1
            and "first_tutorial" not in self.user_progress["achievements"]
        ):
            achievements.append("first_tutorial")

        if (
            completed_count >= 3
            and "tutorial_expert" not in self.user_progress["achievements"]
        ):
            achievements.append("tutorial_expert")

        # Time-based achievements
        if (
            total_time >= 1800
            and "dedicated_learner" not in self.user_progress["achievements"]
        ):  # 30 minutes
            achievements.append("dedicated_learner")

        # Add new achievements
        for achievement in achievements:
            if achievement not in self.user_progress["achievements"]:
                self.user_progress["achievements"].append(achievement)
                self.show_achievement(achievement)

    def show_achievement(self, achievement: str):
        """Show achievement notification."""
        achievement_info = {
            "first_tutorial": {
                "title": "🎯 First Steps",
                "description": "Completed your first tutorial!",
                "xp": 50,
            },
            "tutorial_expert": {
                "title": "🏆 Tutorial Expert",
                "description": "Completed 3 or more tutorials!",
                "xp": 150,
            },
            "dedicated_learner": {
                "title": "⏰ Dedicated Learner",
                "description": "Spent 30+ minutes learning!",
                "xp": 100,
            },
        }

        info = achievement_info.get(achievement, {})
        xp_bonus = info.get("xp", 0)
        self.user_progress["experience_points"] += xp_bonus

        if self.console:
            achievement_text = f"""
🎉 ACHIEVEMENT UNLOCKED! 🎉

{info.get('title', 'Unknown Achievement')}
{info.get('description', 'Great job!')}

Bonus XP: +{xp_bonus}
Total XP: {self.user_progress['experience_points']}
            """

            panel = Panel(
                achievement_text.strip(),
                title="🏆 Achievement Unlocked!",
                border_style="gold",
                padding=(1, 2),
            )
            self.console.print(panel)
        else:
            print(
                f"\n🎉 ACHIEVEMENT UNLOCKED: {info.get('title', 'Unknown Achievement')}"
            )
            print(info.get("description", "Great job!"))
            print(f"Bonus XP: +{xp_bonus}")
            print(f"Total XP: {self.user_progress['experience_points']}")

    def show_progress_summary(self):
        """Show user's learning progress summary."""
        if self.console:
            progress_table = Table(title="📈 Your Learning Progress")
            progress_table.add_column("Metric", style="cyan")
            progress_table.add_column("Value", style="green")

            progress_table.add_row(
                "Tutorials Completed",
                str(len(self.user_progress["tutorials_completed"])),
            )
            progress_table.add_row(
                "Experience Points", str(self.user_progress["experience_points"])
            )
            progress_table.add_row(
                "Achievements", str(len(self.user_progress["achievements"]))
            )
            progress_table.add_row(
                "Time Spent Learning",
                f"{self.user_progress['total_time_spent'] / 60:.1f} minutes",
            )

            self.console.print(progress_table)

            if self.user_progress["achievements"]:
                achievements_text = ", ".join(self.user_progress["achievements"])
                self.console.print(f"\n🏆 Achievements: {achievements_text}")
        else:
            print("\nYour Learning Progress:")
            print("-" * 30)
            print(
                f"Tutorials Completed: {len(self.user_progress['tutorials_completed'])}"
            )
            print(f"Experience Points: {self.user_progress['experience_points']}")
            print(f"Achievements: {len(self.user_progress['achievements'])}")
            print(
                f"Time Spent Learning: {self.user_progress['total_time_spent'] / 60:.1f} minutes"
            )

            if self.user_progress["achievements"]:
                achievements_text = ", ".join(self.user_progress["achievements"])
                print(f"🏆 Achievements: {achievements_text}")

    def log(self, message: str, level: str = "info"):
        """Log tutorial messages."""
        if self.console:
            if level == "success":
                self.console.print(f"✅ {message}", style="green")
            elif level == "warning":
                self.console.print(f"⚠️ {message}", style="yellow")
            elif level == "error":
                self.console.print(f"❌ {message}", style="red")
            else:
                self.console.print(f"📖 {message}", style="blue")
        else:
            print(f"[TUTORIAL] {message}")


def main():
    """Main function for testing tutorial system."""
    # Example configuration
    config = {
        "EXPERIENCE_LEVEL": "beginner",
        "PROJECT_ROOT": Path(__file__).parent.absolute(),
        "EXTRACT_DIR": Path(__file__).parent.absolute() / "extracted_files",
    }

    tutorial_manager = TutorialManager(config)

    while True:
        tutorial_id = tutorial_manager.show_tutorial_menu()
        if tutorial_id is None:
            break

        tutorial_manager.run_tutorial(tutorial_id)
        tutorial_manager.show_progress_summary()


if __name__ == "__main__":
    main()
