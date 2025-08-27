"""
Enhanced YARA Rule Management with Caching and Optimization
Created: 2025
"""

import hashlib
import logging
import mmap
import os
import pickle
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yara


@dataclass
class RuleMetadata:
    """Metadata for a YARA rule"""
    name: str
    path: Path
    hash: str
    compile_time: float
    tags: Set[str] = field(default_factory=set)
    severity: str = "medium"
    enabled: bool = True


@dataclass
class ScanResult:
    """Result of a YARA scan"""
    file_path: str
    rule_name: str
    tags: List[str]
    meta: Dict[str, Any]
    strings: List[Tuple[int, str, bytes]]
    namespace: str
    scan_time: float


class RuleCompilationCache:
    """Cache for compiled YARA rules with memory management"""
    
    def __init__(self, cache_dir: Path, max_cache_size: int = 100 * 1024 * 1024):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_cache_size = max_cache_size
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
        # In-memory cache for frequently used rules
        self._memory_cache: Dict[str, Tuple[yara.Rules, float]] = {}
        self._access_times: Dict[str, float] = {}
        self._cache_hits = 0
        self._cache_misses = 0
    
    def _get_cache_key(self, rule_path: Path) -> str:
        """Generate cache key based on rule file content"""
        stat = rule_path.stat()
        key_data = f"{rule_path}:{stat.st_mtime}:{stat.st_size}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def get_compiled_rules(self, rule_path: Path) -> Optional[yara.Rules]:
        """Get compiled rules from cache or compile and cache"""
        with self._lock:
            cache_key = self._get_cache_key(rule_path)
            
            # Check memory cache first
            if cache_key in self._memory_cache:
                rules, _ = self._memory_cache[cache_key]
                self._access_times[cache_key] = time.time()
                self._cache_hits += 1
                return rules
            
            # Check disk cache
            cache_file = self.cache_dir / f"{cache_key}.yarc"
            if cache_file.exists():
                try:
                    rules = yara.load(str(cache_file))
                    self._memory_cache[cache_key] = (rules, time.time())
                    self._access_times[cache_key] = time.time()
                    self._cache_hits += 1
                    self._evict_if_needed()
                    return rules
                except Exception as e:
                    self.logger.warning(f"Failed to load cached rules: {e}")
                    cache_file.unlink(missing_ok=True)
            
            self._cache_misses += 1
            return None
    
    def cache_compiled_rules(self, rule_path: Path, rules: yara.Rules):
        """Cache compiled rules to disk and memory"""
        with self._lock:
            cache_key = self._get_cache_key(rule_path)
            cache_file = self.cache_dir / f"{cache_key}.yarc"
            
            try:
                # Save to disk
                rules.save(str(cache_file))
                
                # Add to memory cache
                self._memory_cache[cache_key] = (rules, time.time())
                self._access_times[cache_key] = time.time()
                
                self._evict_if_needed()
                
            except Exception as e:
                self.logger.error(f"Failed to cache rules: {e}")
    
    def _evict_if_needed(self):
        """Evict least recently used items if cache is too large"""
        # Simple LRU eviction for memory cache
        if len(self._memory_cache) > 50:  # Max 50 rules in memory
            # Sort by access time and remove oldest
            sorted_keys = sorted(self._access_times.items(), key=lambda x: x[1])
            for key, _ in sorted_keys[:10]:  # Remove 10 oldest
                del self._memory_cache[key]
                del self._access_times[key]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": hit_rate,
            "memory_cache_size": len(self._memory_cache),
            "disk_cache_files": len(list(self.cache_dir.glob("*.yarc")))
        }


class ImprovedRuleManager:
    """Enhanced YARA rule manager with caching and optimization"""
    
    def __init__(
        self,
        rules_dir: Path,
        cache_dir: Path = Path("/tmp/yara_cache"),
        enable_cache: bool = True
    ):
        self.rules_dir = Path(rules_dir)
        self.cache_dir = cache_dir
        self.enable_cache = enable_cache
        self.logger = logging.getLogger(__name__)
        
        # Rule metadata
        self.rule_metadata: Dict[str, RuleMetadata] = {}
        
        # Compilation cache
        self.cache = RuleCompilationCache(cache_dir) if enable_cache else None
        
        # Compiled rules (namespace -> rules)
        self.compiled_rules: Dict[str, yara.Rules] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Performance metrics
        self.compile_times: List[float] = []
        
        # Load and compile rules
        self.reload_rules()
    
    def reload_rules(self):
        """Reload all rules from directory"""
        with self._lock:
            start_time = time.perf_counter()
            self.compiled_rules.clear()
            self.rule_metadata.clear()
            
            # Find all .yar and .yara files
            rule_files = list(self.rules_dir.rglob("*.yar")) + \
                        list(self.rules_dir.rglob("*.yara"))
            
            self.logger.info(f"Found {len(rule_files)} rule files")
            
            for rule_file in rule_files:
                try:
                    self._load_rule_file(rule_file)
                except Exception as e:
                    self.logger.error(f"Failed to load {rule_file}: {e}")
            
            elapsed = time.perf_counter() - start_time
            self.logger.info(f"Loaded {len(self.compiled_rules)} rule sets in {elapsed:.2f}s")
    
    def _load_rule_file(self, rule_path: Path):
        """Load and compile a single rule file"""
        # Generate namespace from path
        namespace = rule_path.relative_to(self.rules_dir).parent.as_posix()
        if namespace == ".":
            namespace = "default"
        
        # Try to get from cache
        if self.cache and self.enable_cache:
            rules = self.cache.get_compiled_rules(rule_path)
            if rules:
                self.compiled_rules[namespace] = rules
                self._extract_metadata(rule_path, namespace)
                return
        
        # Compile rules
        start_time = time.perf_counter()
        try:
            rules = yara.compile(filepath=str(rule_path))
            compile_time = time.perf_counter() - start_time
            self.compile_times.append(compile_time)
            
            # Cache if enabled
            if self.cache and self.enable_cache:
                self.cache.cache_compiled_rules(rule_path, rules)
            
            # Store compiled rules
            self.compiled_rules[namespace] = rules
            
            # Extract metadata
            self._extract_metadata(rule_path, namespace)
            
            self.logger.debug(f"Compiled {rule_path} in {compile_time:.3f}s")
            
        except yara.Error as e:
            self.logger.error(f"YARA compilation error for {rule_path}: {e}")
            raise
    
    def _extract_metadata(self, rule_path: Path, namespace: str):
        """Extract metadata from rule file"""
        # Basic metadata extraction (can be enhanced)
        file_hash = hashlib.md5(rule_path.read_bytes()).hexdigest()
        
        metadata = RuleMetadata(
            name=rule_path.stem,
            path=rule_path,
            hash=file_hash,
            compile_time=time.time(),
            tags={namespace},
            severity=self._determine_severity(rule_path.name),
            enabled=True
        )
        
        self.rule_metadata[rule_path.stem] = metadata
    
    def _determine_severity(self, filename: str) -> str:
        """Determine rule severity from filename"""
        filename_lower = filename.lower()
        if any(x in filename_lower for x in ['critical', 'ransomware']):
            return 'critical'
        elif any(x in filename_lower for x in ['high', 'malware']):
            return 'high'
        elif any(x in filename_lower for x in ['low', 'info']):
            return 'low'
        return 'medium'
    
    def scan_file(
        self,
        file_path: str,
        timeout: int = 30,
        fast_mode: bool = False
    ) -> List[ScanResult]:
        """Scan a file with all compiled rules"""
        results = []
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Use memory-mapped file for large files
        file_size = file_path.stat().st_size
        use_mmap = file_size > 10 * 1024 * 1024  # 10MB threshold
        
        scan_start = time.perf_counter()
        
        try:
            if use_mmap:
                # Memory-mapped scanning for large files
                with open(file_path, 'rb') as f:
                    with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                        results = self._scan_data(mmapped_file, str(file_path), timeout, fast_mode)
            else:
                # Regular scanning for small files
                file_data = file_path.read_bytes()
                results = self._scan_data(file_data, str(file_path), timeout, fast_mode)
            
        except Exception as e:
            self.logger.error(f"Scan error for {file_path}: {e}")
            raise
        
        scan_time = time.perf_counter() - scan_start
        
        # Add scan time to results
        for result in results:
            result.scan_time = scan_time
        
        return results
    
    def _scan_data(
        self,
        data: bytes,
        file_path: str,
        timeout: int,
        fast_mode: bool
    ) -> List[ScanResult]:
        """Scan data with all rule sets"""
        results = []
        
        with self._lock:
            for namespace, rules in self.compiled_rules.items():
                try:
                    matches = rules.match(
                        data=data,
                        timeout=timeout,
                        fast=fast_mode
                    )
                    
                    for match in matches:
                        result = ScanResult(
                            file_path=file_path,
                            rule_name=match.rule,
                            tags=match.tags,
                            meta=match.meta,
                            strings=[(s.offset, s.identifier, s.instances[0]) 
                                    for s in match.strings if s.instances],
                            namespace=namespace,
                            scan_time=0  # Will be set by caller
                        )
                        results.append(result)
                        
                except yara.TimeoutError:
                    self.logger.warning(f"Scan timeout for {file_path} with {namespace}")
                except Exception as e:
                    self.logger.error(f"Scan error with {namespace}: {e}")
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get rule manager statistics"""
        stats = {
            "total_rules": len(self.rule_metadata),
            "compiled_namespaces": len(self.compiled_rules),
            "enabled_rules": sum(1 for r in self.rule_metadata.values() if r.enabled),
            "avg_compile_time": sum(self.compile_times) / len(self.compile_times) 
                               if self.compile_times else 0,
            "severity_distribution": {}
        }
        
        # Count rules by severity
        for metadata in self.rule_metadata.values():
            severity = metadata.severity
            stats["severity_distribution"][severity] = \
                stats["severity_distribution"].get(severity, 0) + 1
        
        # Add cache statistics if available
        if self.cache:
            stats["cache_stats"] = self.cache.get_statistics()
        
        return stats
    
    def enable_rule(self, rule_name: str):
        """Enable a specific rule"""
        if rule_name in self.rule_metadata:
            self.rule_metadata[rule_name].enabled = True
    
    def disable_rule(self, rule_name: str):
        """Disable a specific rule"""
        if rule_name in self.rule_metadata:
            self.rule_metadata[rule_name].enabled = False
    
    def get_rule_info(self, rule_name: str) -> Optional[RuleMetadata]:
        """Get information about a specific rule"""
        return self.rule_metadata.get(rule_name)