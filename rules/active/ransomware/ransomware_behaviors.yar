rule ransomware_file_operations {
    meta:
        description = "Detects common file operations used by ransomware"
        author = "Security Team"
        date = "2025-04-24"
        version = "1.0"
        reference = "Internal research on ransomware behavior"
    
    strings:
        // Common API calls for file enumeration and manipulation
        $file_enum1 = "FindFirstFileW" ascii wide nocase
        $file_enum2 = "FindNextFileW" ascii wide nocase
        $file_op1 = "CreateFileW" ascii wide nocase
        $file_op2 = "WriteFile" ascii wide nocase
        $file_op3 = "DeleteFileW" ascii wide nocase
        $file_op4 = "MoveFileW" ascii wide nocase
        $file_op5 = "SetFileAttributesW" ascii wide nocase
        
        // Volume and shadow copy related
        $shadow1 = "vssadmin" ascii wide nocase
        $shadow2 = "delete shadows" ascii wide nocase
        $shadow3 = "resize shadowstorage" ascii wide nocase
        $shadow4 = "wmic shadowcopy delete" ascii wide nocase
        
        // Common ransom note strings
        $note1 = "your files are encrypted" ascii wide nocase
        $note2 = "payment" ascii wide nocase
        $note3 = "bitcoin" ascii wide nocase
        $note4 = "decrypt" ascii wide nocase
        $note5 = "ransom" ascii wide nocase
        
        // Crypto API calls
        $crypto1 = "CryptEncrypt" ascii wide nocase
        $crypto2 = "CryptGenKey" ascii wide nocase
        $crypto3 = "CryptGenRandom" ascii wide nocase
    
    condition:
        uint16(0) == 0x5A4D and // PE file
        (
            // File operations pattern
            (3 of ($file_enum*) and 3 of ($file_op*)) or
            // Shadow copy deletion pattern
            (2 of ($shadow*)) or
            // Ransom note pattern with crypto operations
            (3 of ($note*) and 2 of ($crypto*))
        )
}

rule fileless_malware_indicators {
    meta:
        description = "Detects indicators of fileless malware execution methods"
        author = "Security Team"
        date = "2025-04-24"
        version = "1.0"
        reference = "Internal research on fileless malware techniques"
    
    strings:
        // PowerShell execution and obfuscation
        $ps1 = "powershell" ascii wide nocase
        $ps2 = "-encodedcommand" ascii wide nocase
        $ps3 = "-enc " ascii wide nocase
        $ps4 = "-noprofile" ascii wide nocase
        $ps5 = "-windowstyle hidden" ascii wide nocase
        $ps6 = "IEX(" ascii wide nocase
        $ps7 = "Invoke-Expression" ascii wide nocase
        $ps8 = "FromBase64String" ascii wide nocase
        
        // WMI persistence and execution
        $wmi1 = "wmic" ascii wide nocase
        $wmi2 = "Win32_ScheduledJob" ascii wide nocase
        $wmi3 = "WmiPrvSE.exe" ascii wide nocase
        $wmi4 = "Win32_Process" ascii wide nocase
        $wmi5 = "Create(" ascii wide nocase
        
        // Memory injection techniques
        $inject1 = "VirtualAlloc" ascii wide nocase
        $inject2 = "WriteProcessMemory" ascii wide nocase
        $inject3 = "CreateRemoteThread" ascii wide nocase
        $inject4 = "NtCreateThreadEx" ascii wide nocase
        $inject5 = "RtlCreateUserThread" ascii wide nocase
        
        // Registry run keys for persistence
        $reg1 = "CurrentVersion\\Run" ascii wide nocase
        $reg2 = "CurrentVersion\\RunOnce" ascii wide nocase
        $reg3 = "WriteRegStr" ascii wide nocase
        $reg4 = "RegSetValueEx" ascii wide nocase
        
        // Living off the land binaries
        $lol1 = "regsvr32" ascii wide nocase
        $lol2 = "rundll32" ascii wide nocase
        $lol3 = "certutil" ascii wide nocase
        $lol4 = "bitsadmin" ascii wide nocase
        $lol5 = "mshta.exe" ascii wide nocase
    
    condition:
        (
            // PowerShell-based fileless pattern
            (3 of ($ps*)) or
            // WMI-based pattern
            (3 of ($wmi*)) or
            // Memory injection pattern
            (2 of ($inject*)) or
            // Registry persistence with LOL binaries
            (2 of ($reg*) and 2 of ($lol*))
        )
}

rule memory_only_payload_indicators {
    meta:
        description = "Detects code that loads and executes payloads directly in memory"
        author = "Security Team"
        date = "2025-04-24"
        version = "1.0"
        reference = "Internal research on memory-only malware"
    
    strings:
        // Common shellcode loaders
        $loader1 = { 48 8D 0D ?? ?? ?? ?? E8 ?? ?? ?? ?? 48 85 C0 74 } // x64 memory allocation pattern
        $loader2 = { 89 E5 83 EC ?? 8B 45 ?? 89 45 ?? 8B 45 } // x86 stack frame setup pattern
        
        // API calls for in-memory execution
        $exec1 = "VirtualProtect" ascii wide nocase
        $exec2 = "VirtualAlloc" ascii wide nocase
        $exec3 = "RtlMoveMemory" ascii wide nocase
        $exec4 = "memcpy" ascii wide nocase
        $exec5 = "HeapAlloc" ascii wide nocase
        
        // Reflective loading
        $refl1 = "GetProcAddress" ascii wide nocase
        $refl2 = "LoadLibrary" ascii wide nocase
        $refl3 = "GetModuleHandle" ascii wide nocase
        $refl4 = "VirtualAllocEx" ascii wide nocase
        
        // Common obfuscation techniques
        $obf1 = "xor" ascii wide nocase
        $obf2 = "base64" ascii wide nocase
        $obf3 = "decrypt" ascii wide nocase
    
    condition:
        (1 of ($loader*)) and
        (2 of ($exec*)) and
        (2 of ($refl*)) and
        (1 of ($obf*))
}
