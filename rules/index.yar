/*
 * Zeek-YARA Integration Rule Index
 * Created: April 24, 2025
 * Author: Security Team
 * 
 * This file includes all YARA rules organized by category
 */

// Ransomware detection
include "./active/ransomware/ransomware_behaviors.yar"

// Malicious document detection 
include "./active/document_malware/maldoc_techniques.yar"

// Network behavior and C2 detection
include "./active/network_behavior/c2_behaviors.yar"

// Evasion techniques detection
include "./active/evasion_techniques/anti_analysis.yar"

// Basic test rules (EICAR)
include "./active/malware/test_rules.yar"
