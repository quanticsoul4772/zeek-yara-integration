rule command_and_control_behaviors {
    meta:
        description = "Detects common command and control (C2) behaviors in executables"
        author = "Security Team"
        date = "2025-04-24"
        version = "1.0"
        reference = "Internal research on C2 communication patterns"
    
    strings:
        // Network communication functions
        $net1 = "WSASocket" ascii wide nocase
        $net2 = "connect" ascii wide nocase
        $net3 = "send" ascii wide nocase
        $net4 = "recv" ascii wide nocase
        $net5 = "socket" ascii wide nocase
        $net6 = "inet_addr" ascii wide nocase
        
        // HTTP related
        $http1 = "HTTP/1." ascii wide nocase
        $http2 = "GET " ascii wide nocase
        $http3 = "POST " ascii wide nocase
        $http4 = "User-Agent: " ascii wide nocase
        $http5 = "Mozilla/" ascii wide nocase
        $http6 = "Content-Type: " ascii wide nocase
        
        // DNS related
        $dns1 = "gethostbyname" ascii wide nocase
        $dns2 = "getaddrinfo" ascii wide nocase
        $dns3 = "GetHostName" ascii wide nocase
        $dns4 = "DnsQuery" ascii wide nocase
        
        // Suspicious behaviors
        $sus1 = "sleep" ascii wide nocase
        $sus2 = "CreateMutex" ascii wide nocase
        $sus3 = "IsDebuggerPresent" ascii wide nocase
        $sus4 = "CreateProcess" ascii wide nocase
        
        // Encoded commands
        $enc1 = "base64" ascii wide nocase
        $enc2 = "encode" ascii wide nocase
        $enc3 = "decode" ascii wide nocase
        $enc4 = "encrypt" ascii wide nocase
        $enc5 = "decrypt" ascii wide nocase
    
    condition:
        uint16(0) == 0x5A4D and // PE file
        (
            // Network communication with suspicious behavior
            (3 of ($net*) and 1 of ($sus*)) or
            // HTTP communication with encoding
            (2 of ($http*) and 1 of ($enc*)) or
            // DNS with suspicious behavior
            (2 of ($dns*) and 1 of ($sus*)) or
            // Multiple suspicious indicators
            (2 of ($net*) and 2 of ($http*) and 1 of ($enc*))
        )
}

rule dns_tunneling_indicators {
    meta:
        description = "Detects potential DNS tunneling behavior"
        author = "Security Team"
        date = "2025-04-24"
        version = "1.0"
        reference = "Internal research on DNS tunneling techniques"
    
    strings:
        // DNS API calls
        $dns_api1 = "DnsQuery" ascii wide nocase
        $dns_api2 = "gethostbyname" ascii wide nocase
        $dns_api3 = "getaddrinfo" ascii wide nocase
        $dns_api4 = "GetHostName" ascii wide nocase
        
        // Base64 encoding/decoding
        $enc1 = "base64" ascii wide nocase
        $enc2 = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/" ascii wide
        $enc3 = "ToBase64String" ascii wide nocase
        $enc4 = "FromBase64String" ascii wide nocase
        
        // DNS packet manipulation
        $dns_pkt1 = "TXT" ascii wide nocase
        $dns_pkt2 = "AAAA" ascii wide nocase
        $dns_pkt3 = "CNAME" ascii wide nocase
        $dns_pkt4 = "MX" ascii wide nocase
        
        // High frequency indicators
        $freq1 = "GetTickCount" ascii wide nocase
        $freq2 = "QueryPerformanceCounter" ascii wide nocase
        $freq3 = "SetTimer" ascii wide nocase
        
        // Data manipulation
        $data1 = "substring" ascii wide nocase
        $data2 = "split" ascii wide nocase
        $data3 = "concat" ascii wide nocase
        $data4 = "chunk" ascii wide nocase
        $data5 = "segment" ascii wide nocase
    
    condition:
        (
            // DNS API usage with encoding
            (2 of ($dns_api*) and 1 of ($enc*)) or
            // DNS record type manipulation with data handling
            (2 of ($dns_pkt*) and 2 of ($data*)) or
            // Frequent DNS operations
            (2 of ($dns_api*) and 1 of ($freq*)) or
            // Complete pattern
            (1 of ($dns_api*) and 1 of ($enc*) and 1 of ($dns_pkt*) and 1 of ($data*))
        )
}

rule beaconing_behavior {
    meta:
        description = "Detects potential command and control beaconing behavior"
        author = "Security Team"
        date = "2025-04-24"
        version = "1.0"
        reference = "Internal research on malware beaconing patterns"
    
    strings:
        // Timing functions
        $time1 = "Sleep" ascii wide nocase
        $time2 = "WaitForSingleObject" ascii wide nocase
        $time3 = "SetTimer" ascii wide nocase
        $time4 = "CreateTimerQueueTimer" ascii wide nocase
        $time5 = "GetTickCount" ascii wide nocase
        $time6 = "QueryPerformanceCounter" ascii wide nocase
        
        // Network functions
        $net1 = "connect" ascii wide nocase
        $net2 = "send" ascii wide nocase
        $net3 = "recv" ascii wide nocase
        $net4 = "HttpOpenRequest" ascii wide nocase
        $net5 = "InternetConnect" ascii wide nocase
        $net6 = "WinHttpConnect" ascii wide nocase
        
        // Loop indicators
        $loop1 = "while" ascii wide nocase
        $loop2 = "for" ascii wide nocase
        $loop3 = "do {" ascii wide nocase
        
        // Persistence indicators
        $pers1 = "CreateService" ascii wide nocase
        $pers2 = "RegSetValue" ascii wide nocase
        $pers3 = "StartServiceCtrlDispatcher" ascii wide nocase
        $pers4 = "SetWindowsHookEx" ascii wide nocase
        
        // Command execution
        $cmd1 = "CreateProcess" ascii wide nocase
        $cmd2 = "ShellExecute" ascii wide nocase
        $cmd3 = "WinExec" ascii wide nocase
    
    condition:
        uint16(0) == 0x5A4D and // PE file
        (
            // Classic beaconing pattern
            (2 of ($time*) and 2 of ($net*) and 1 of ($loop*)) or
            // Persistence with networking
            (1 of ($pers*) and 2 of ($net*) and 1 of ($time*)) or
            // Command execution with timing
            (1 of ($cmd*) and 2 of ($time*) and 1 of ($net*)) or
            // Complete C2 pattern
            (1 of ($time*) and 1 of ($net*) and 1 of ($loop*) and (1 of ($cmd*) or 1 of ($pers*)))
        )
}
