rule anti_debugging_techniques {
    meta:
        description = "Detects anti-debugging techniques used by malware"
        author = "Security Team"
        date = "2025-04-24"
        version = "1.0"
        reference = "Internal research on anti-analysis methods"
    
    strings:
        // Debugger detection
        $dbg1 = "IsDebuggerPresent" ascii wide nocase
        $dbg2 = "CheckRemoteDebuggerPresent" ascii wide nocase
        $dbg3 = "NtQueryInformationProcess" ascii wide nocase
        $dbg4 = "FindWindow" ascii wide nocase
        $dbg5 = "OutputDebugString" ascii wide nocase
        $dbg6 = "ProcessDebugPort" ascii wide nocase
        
        // Timing checks
        $time1 = "GetTickCount" ascii wide nocase
        $time2 = "QueryPerformanceCounter" ascii wide nocase
        $time3 = "GetSystemTime" ascii wide nocase
        $time4 = "timeGetTime" ascii wide nocase
        
        // VM detection
        $vm1 = "vmware" ascii wide nocase
        $vm2 = "virtualbox" ascii wide nocase
        $vm3 = "vbox" ascii wide nocase
        $vm4 = "qemu" ascii wide nocase
        $vm5 = "bochs" ascii wide nocase
        $vm6 = "parallels" ascii wide nocase
        
        // Sandbox detection
        $sandbox1 = "SbieDll.dll" ascii wide nocase
        $sandbox2 = "SandboxieControlWndClass" ascii wide nocase
        $sandbox3 = "cmdvrt32.dll" ascii wide nocase
        $sandbox4 = "Sandboxie" ascii wide nocase
        $sandbox5 = "cwsandbox" ascii wide nocase
        $sandbox6 = "panda_url_filtering" ascii wide nocase
        
        // Exception handling for anti-debug
        $except1 = "SetUnhandledExceptionFilter" ascii wide nocase
        $except2 = "AddVectoredExceptionHandler" ascii wide nocase
        $except3 = "__try" ascii wide
        $except4 = "except" ascii wide
        $except5 = "catch" ascii wide
    
    condition:
        uint16(0) == 0x5A4D and // PE file
        (
            // Debugger detection techniques
            (2 of ($dbg*)) or
            // VM detection techniques
            (2 of ($vm*)) or
            // Sandbox detection
            (1 of ($sandbox*)) or
            // Timing checks with exception handling
            (1 of ($time*) and 1 of ($except*)) or
            // Mixed evasion techniques
            (1 of ($dbg*) and 1 of ($vm*) and 1 of ($time*))
        )
}

rule code_injection_techniques {
    meta:
        description = "Detects code injection techniques used by malware"
        author = "Security Team"
        date = "2025-04-24"
        version = "1.0"
        reference = "Internal research on code injection methods"
    
    strings:
        // Process manipulation
        $proc1 = "CreateProcess" ascii wide nocase
        $proc2 = "OpenProcess" ascii wide nocase
        $proc3 = "NtOpenProcess" ascii wide nocase
        $proc4 = "ZwOpenProcess" ascii wide nocase
        $proc5 = "ProcessHandle" ascii wide nocase
        
        // Memory operations
        $mem1 = "VirtualAlloc" ascii wide nocase
        $mem2 = "VirtualProtect" ascii wide nocase
        $mem3 = "WriteProcessMemory" ascii wide nocase
        $mem4 = "ReadProcessMemory" ascii wide nocase
        $mem5 = "NtAllocateVirtualMemory" ascii wide nocase
        $mem6 = "ZwAllocateVirtualMemory" ascii wide nocase
        $mem7 = "VirtualAllocEx" ascii wide nocase
        
        // Thread operations
        $thread1 = "CreateThread" ascii wide nocase
        $thread2 = "CreateRemoteThread" ascii wide nocase
        $thread3 = "NtCreateThreadEx" ascii wide nocase
        $thread4 = "ZwCreateThreadEx" ascii wide nocase
        $thread5 = "RtlCreateUserThread" ascii wide nocase
        $thread6 = "SuspendThread" ascii wide nocase
        $thread7 = "ResumeThread" ascii wide nocase
        
        // DLL operations
        $dll1 = "LoadLibrary" ascii wide nocase
        $dll2 = "LdrLoadDll" ascii wide nocase
        $dll3 = "GetProcAddress" ascii wide nocase
        $dll4 = "GetModuleHandle" ascii wide nocase
        $dll5 = "FreeLibrary" ascii wide nocase
        
        // Hooking operations
        $hook1 = "SetWindowsHookEx" ascii wide nocase
        $hook2 = "GetWindowsHookEx" ascii wide nocase
        $hook3 = "UnhookWindowsHookEx" ascii wide nocase
        $hook4 = "CallNextHookEx" ascii wide nocase
    
    condition:
        uint16(0) == 0x5A4D and // PE file
        (
            // Classic process injection
            (1 of ($proc*) and 1 of ($mem*) and 1 of ($thread*)) or
            // DLL injection
            (1 of ($proc*) and 1 of ($mem*) and 1 of ($dll*)) or
            // Thread manipulation
            (1 of ($thread*) and 2 of ($mem*)) or
            // Hooking techniques
            (1 of ($hook*) and 1 of ($dll*)) or
            // Advanced injection techniques
            (2 of ($mem*) and 1 of ($thread*) and 1 of ($dll*))
        )
}

rule obfuscation_techniques {
    meta:
        description = "Detects obfuscation techniques used by malware"
        author = "Security Team"
        date = "2025-04-24"
        version = "1.0"
        reference = "Internal research on code obfuscation methods"
    
    strings:
        // String obfuscation
        $str1 = "StrReverse" ascii wide nocase
        $str2 = "CharCode" ascii wide nocase
        $str3 = "FromCharCode" ascii wide nocase
        $str4 = "xor" ascii wide nocase
        $str5 = "base64" ascii wide nocase
        $str6 = "encode" ascii wide nocase
        $str7 = "decode" ascii wide nocase
        
        // Dynamic API loading
        $api1 = "GetProcAddress" ascii wide nocase
        $api2 = "LoadLibrary" ascii wide nocase
        $api3 = "GetModuleHandle" ascii wide nocase
        $api4 = "FreeLibrary" ascii wide nocase
        
        // String manipulation patterns
        $manip1 = "+=" ascii wide
        $manip2 = "concat" ascii wide nocase
        $manip3 = "substring" ascii wide nocase
        $manip4 = "replace" ascii wide nocase
        $manip5 = "split" ascii wide nocase
        
        // Data transformation
        $trans1 = "shift" ascii wide nocase
        $trans2 = "rotate" ascii wide nocase
        $trans3 = "reverse" ascii wide nocase
        $trans4 = "^" ascii wide
        $trans5 = "~" ascii wide
        $trans6 = ">>" ascii wide
        $trans7 = "<<" ascii wide
        
        // Stack strings
        $stack = { C7 45 ?? ?? ?? ?? ?? C7 45 ?? ?? ?? ?? ?? C7 45 ?? ?? ?? ?? ?? }
    
    condition:
        (
            // String obfuscation methods
            (2 of ($str*)) or
            // Dynamic API loading with string manipulation
            (1 of ($api*) and 2 of ($str*)) or
            // Heavy string manipulation
            (3 of ($manip*)) or
            // Data transformation techniques
            (2 of ($trans*) and 1 of ($str*)) or
            // Stack strings
            ($stack)
        )
}
