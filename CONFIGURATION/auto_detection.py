#!/usr/bin/env python3
"""
Automatic Configuration Detection System
Intelligently detects system capabilities and generates optimal configurations
"""

import json
import logging
import os
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import netifaces

try:
    import yara

    YARA_AVAILABLE = True
except ImportError:
    YARA_AVAILABLE = False


class SystemDetector:
    """Advanced system detection with intelligent configuration generation."""

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.platform = platform.system().lower()
        self.logger = self._setup_logger()
        self.detected_config = {}
        self.environment_info = {}

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for detection system."""
        logger = logging.getLogger("auto_detection")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def detect_system_environment(self) -> Dict[str, Any]:
        """Comprehensive system environment detection."""
        self.logger.info("Starting comprehensive system detection...")

        env_info = {
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "architecture": platform.architecture(),
                "python_version": platform.python_version(),
            },
            "paths": self._detect_system_paths(),
            "tools": self._detect_security_tools(),
            "network": self._detect_network_configuration(),
            "resources": self._detect_system_resources(),
            "permissions": self._check_permissions(),
            "virtualization": self._detect_virtualization(),
        }

        self.environment_info = env_info
        return env_info

    def _detect_system_paths(self) -> Dict[str, Any]:
        """Detect important system paths and directories."""
        paths = {
            "home": Path.home(),
            "temp": (
                Path("/tmp")
                if self.platform != "windows"
                else Path(os.environ.get("TEMP", "C:\\temp"))
            ),
            "config_dirs": self._get_config_directories(),
            "data_dirs": self._get_data_directories(),
            "cache_dirs": self._get_cache_directories(),
            "log_dirs": self._get_log_directories(),
        }

        # Detect writable directories
        for category, dir_list in paths.items():
            if isinstance(dir_list, list):
                writable_dirs = []
                for directory in dir_list:
                    if self._is_directory_writable(directory):
                        writable_dirs.append(str(directory))
                paths[f"{category}_writable"] = writable_dirs

        return paths

    def _get_config_directories(self) -> List[Path]:
        """Get platform-specific configuration directories."""
        if self.platform == "windows":
            return [
                Path(os.environ.get("APPDATA", "")),
                Path(os.environ.get("LOCALAPPDATA", "")),
                self.project_root / "config",
            ]
        elif self.platform == "darwin":
            return [
                Path.home() / "Library" / "Application Support",
                Path("/usr/local/etc"),
                Path("/etc"),
                self.project_root / "config",
            ]
        else:  # Linux
            return [
                Path.home() / ".config",
                Path("/etc"),
                Path("/usr/local/etc"),
                self.project_root / "config",
            ]

    def _get_data_directories(self) -> List[Path]:
        """Get platform-specific data directories."""
        if self.platform == "windows":
            return [
                Path(os.environ.get("LOCALAPPDATA", "")) / "ZeekYARAEducational",
                self.project_root / "DATA",
            ]
        elif self.platform == "darwin":
            return [
                Path.home() / "Library" / "Application Support" / "ZeekYARAEducational",
                Path("/usr/local/var"),
                self.project_root / "DATA",
            ]
        else:  # Linux
            return [
                Path.home() / ".local" / "share" / "zeek-yara-educational",
                Path("/var/lib/zeek-yara-educational"),
                self.project_root / "DATA",
            ]

    def _get_cache_directories(self) -> List[Path]:
        """Get platform-specific cache directories."""
        if self.platform == "windows":
            return [
                Path(os.environ.get("LOCALAPPDATA", ""))
                / "ZeekYARAEducational"
                / "Cache",
                self.project_root / "cache",
            ]
        elif self.platform == "darwin":
            return [
                Path.home() / "Library" / "Caches" / "ZeekYARAEducational",
                self.project_root / "cache",
            ]
        else:  # Linux
            return [
                Path.home() / ".cache" / "zeek-yara-educational",
                Path("/tmp/zeek-yara-educational"),
                self.project_root / "cache",
            ]

    def _get_log_directories(self) -> List[Path]:
        """Get platform-specific log directories."""
        if self.platform == "windows":
            return [
                Path(os.environ.get("LOCALAPPDATA", ""))
                / "ZeekYARAEducational"
                / "Logs",
                self.project_root / "logs",
            ]
        elif self.platform == "darwin":
            return [
                Path.home() / "Library" / "Logs" / "ZeekYARAEducational",
                Path("/usr/local/var/log"),
                self.project_root / "logs",
            ]
        else:  # Linux
            return [
                Path.home() / ".local" / "share" / "zeek-yara-educational" / "logs",
                Path("/var/log/zeek-yara-educational"),
                self.project_root / "logs",
            ]

    def _detect_security_tools(self) -> Dict[str, Any]:
        """Detect available security tools and their configurations."""
        tools = {
            "zeek": self._detect_zeek(),
            "yara": self._detect_yara(),
            "suricata": self._detect_suricata(),
            "python_modules": self._detect_python_modules(),
            "system_tools": self._detect_system_tools(),
        }

        return tools

    def _detect_zeek(self) -> Dict[str, Any]:
        """Enhanced Zeek detection with version and capability analysis."""
        zeek_info = {
            "available": False,
            "binary_path": None,
            "version": None,
            "config_path": None,
            "scripts_path": None,
            "capabilities": [],
            "installation_method": None,
        }

        # Check for zeek binary
        zeek_path = shutil.which("zeek")
        if not zeek_path:
            zeek_path = shutil.which("bro")  # Legacy name

        if zeek_path:
            zeek_info["available"] = True
            zeek_info["binary_path"] = zeek_path

            # Get version
            try:
                result = subprocess.run(
                    [zeek_path, "--version"], capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    version_line = result.stdout.strip().split("\n")[0]
                    zeek_info["version"] = version_line
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass

            # Detect installation paths
            zeek_info.update(self._detect_zeek_paths(zeek_path))

            # Detect capabilities
            zeek_info["capabilities"] = self._detect_zeek_capabilities(zeek_path)

            # Detect installation method
            zeek_info["installation_method"] = self._detect_zeek_installation_method(
                zeek_path
            )

        return zeek_info

    def _detect_zeek_paths(self, zeek_path: str) -> Dict[str, Optional[str]]:
        """Detect Zeek configuration and script paths."""
        paths = {"config_path": None, "scripts_path": None, "logs_path": None}

        try:
            # Try to get zeek configuration
            result = subprocess.run(
                [zeek_path, "--print-id"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "ZEEKPATH" in line or "BROPATH" in line:
                        script_paths = (
                            line.split("=")[1].strip() if "=" in line else None
                        )
                        if script_paths:
                            paths["scripts_path"] = script_paths.split(":")[0]
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass

        # Common Zeek installation paths
        common_paths = [
            "/usr/local/zeek",
            "/opt/zeek",
            "/usr/share/zeek",
            "/usr/local/bro",
            "/opt/bro",
        ]

        for base_path in common_paths:
            if Path(base_path).exists():
                if Path(base_path + "/share/zeek").exists():
                    paths["scripts_path"] = str(Path(base_path + "/share/zeek"))
                elif Path(base_path + "/share/bro").exists():
                    paths["scripts_path"] = str(Path(base_path + "/share/bro"))

                if Path(base_path + "/etc").exists():
                    paths["config_path"] = str(Path(base_path + "/etc"))

        return paths

    def _detect_zeek_capabilities(self, zeek_path: str) -> List[str]:
        """Detect Zeek capabilities and available plugins."""
        capabilities = []

        try:
            # Check if Zeek supports file extraction
            result = subprocess.run(
                [zeek_path, "--help"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                if "extract" in result.stdout.lower():
                    capabilities.append("file_extraction")
                if "protocol" in result.stdout.lower():
                    capabilities.append("protocol_analysis")
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass

        return capabilities

    def _detect_zeek_installation_method(self, zeek_path: str) -> Optional[str]:
        """Detect how Zeek was installed."""
        zeek_path_obj = Path(zeek_path)

        if "/homebrew" in str(zeek_path_obj) or "/usr/local/bin" in str(zeek_path_obj):
            return "homebrew"
        elif "/opt" in str(zeek_path_obj):
            return "manual"
        elif "/usr/bin" in str(zeek_path_obj):
            return "package_manager"
        elif "conda" in str(zeek_path_obj):
            return "conda"

        return "unknown"

    def _detect_yara(self) -> Dict[str, Any]:
        """Enhanced YARA detection with Python module analysis."""
        yara_info = {
            "available": False,
            "binary_path": None,
            "python_module": YARA_AVAILABLE,
            "version": None,
            "rules_paths": [],
            "compilation_support": False,
        }

        # Check for yara binary
        yara_path = shutil.which("yara")
        if yara_path:
            yara_info["available"] = True
            yara_info["binary_path"] = yara_path

            # Get version
            try:
                result = subprocess.run(
                    [yara_path, "--version"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    yara_info["version"] = result.stdout.strip()
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass

        # Check Python module
        if YARA_AVAILABLE:
            try:
                yara_info["version"] = (
                    yara.__version__ if hasattr(yara, "__version__") else "unknown"
                )
                yara_info["compilation_support"] = True
            except BaseException:
                pass

        # Detect common YARA rules directories
        yara_info["rules_paths"] = self._find_yara_rules_directories()

        return yara_info

    def _find_yara_rules_directories(self) -> List[str]:
        """Find common YARA rules directories."""
        common_paths = [
            "/usr/share/yara",
            "/usr/local/share/yara",
            "/opt/yara/rules",
            str(Path.home() / ".yara"),
            str(self.project_root / "rules"),
        ]

        if self.platform == "windows":
            common_paths.extend(
                [
                    "C:\\Program Files\\YARA\\rules",
                    str(Path(os.environ.get("APPDATA", "")) / "YARA" / "rules"),
                ]
            )
        elif self.platform == "darwin":
            common_paths.extend(
                [
                    "/usr/local/Cellar/yara/*/share/yara",
                    str(Path.home() / "Library" / "Application Support" / "YARA"),
                ]
            )

        existing_paths = []
        for path in common_paths:
            if "*" in path:
                # Handle glob patterns
                from glob import glob

                existing_paths.extend(glob(path))
            elif Path(path).exists():
                existing_paths.append(path)

        return existing_paths

    def _detect_suricata(self) -> Dict[str, Any]:
        """Enhanced Suricata detection with configuration analysis."""
        suricata_info = {
            "available": False,
            "binary_path": None,
            "version": None,
            "config_path": None,
            "rules_paths": [],
            "log_path": None,
            "eve_json_support": False,
            "lua_support": False,
        }

        # Check for suricata binary
        suricata_path = shutil.which("suricata")
        if suricata_path:
            suricata_info["available"] = True
            suricata_info["binary_path"] = suricata_path

            # Get version and features
            try:
                result = subprocess.run(
                    [suricata_path, "--build-info"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    build_info = result.stdout

                    # Extract version
                    for line in build_info.split("\n"):
                        if "This is Suricata version" in line:
                            suricata_info["version"] = line.split("version")[1].strip()
                            break

                    # Check for features
                    if "Lua support" in build_info:
                        suricata_info["lua_support"] = True
                    if "JSON output" in build_info or "eve" in build_info.lower():
                        suricata_info["eve_json_support"] = True
            except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                pass

            # Detect configuration and rules paths
            suricata_info.update(self._detect_suricata_paths())

        return suricata_info

    def _detect_suricata_paths(self) -> Dict[str, Any]:
        """Detect Suricata configuration and rules paths."""
        paths = {"config_path": None, "rules_paths": [], "log_path": None}

        # Common Suricata configuration paths
        config_paths = [
            "/etc/suricata/suricata.yaml",
            "/usr/local/etc/suricata/suricata.yaml",
            "/opt/suricata/etc/suricata.yaml",
            str(self.project_root / "config" / "suricata.yaml"),
        ]

        for config_path in config_paths:
            if Path(config_path).exists():
                paths["config_path"] = config_path
                break

        # Common rules directories
        rules_paths = [
            "/etc/suricata/rules",
            "/usr/local/etc/suricata/rules",
            "/var/lib/suricata/rules",
            "/opt/suricata/rules",
            str(self.project_root / "rules" / "suricata"),
        ]

        for rules_path in rules_paths:
            if Path(rules_path).exists():
                paths["rules_paths"].append(rules_path)

        # Common log directories
        log_paths = [
            "/var/log/suricata",
            "/usr/local/var/log/suricata",
            "/opt/suricata/log",
            str(self.project_root / "logs" / "suricata"),
        ]

        for log_path in log_paths:
            if Path(log_path).exists():
                paths["log_path"] = log_path
                break

        return paths

    def _detect_python_modules(self) -> Dict[str, Any]:
        """Detect available Python modules and their versions."""
        modules = {}

        required_modules = [
            "yara",
            "watchdog",
            "magic",
            "fastapi",
            "uvicorn",
            "pydantic",
            "sqlalchemy",
            "requests",
            "rich",
            "netifaces",
        ]

        for module_name in required_modules:
            try:
                module = __import__(module_name)
                version = getattr(module, "__version__", "unknown")
                modules[module_name] = {
                    "available": True,
                    "version": version,
                    "path": getattr(module, "__file__", "unknown"),
                }
            except ImportError:
                modules[module_name] = {
                    "available": False,
                    "version": None,
                    "path": None,
                }

        return modules

    def _detect_system_tools(self) -> Dict[str, Any]:
        """Detect useful system tools."""
        tools = {}

        system_tools = [
            "git",
            "curl",
            "wget",
            "tar",
            "zip",
            "unzip",
            "sqlite3",
            "netstat",
            "ss",
            "tcpdump",
            "tshark",
        ]

        for tool in system_tools:
            tool_path = shutil.which(tool)
            tools[tool] = {"available": tool_path is not None, "path": tool_path}

        return tools

    def _detect_network_configuration(self) -> Dict[str, Any]:
        """Detect network interfaces and configuration."""
        network_info = {
            "interfaces": [],
            "default_interface": None,
            "monitoring_capable": [],
            "has_wireless": False,
            "has_ethernet": False,
        }

        try:
            interfaces = netifaces.interfaces()

            for interface in interfaces:
                # Skip loopback and virtual interfaces for monitoring
                if interface.startswith(("lo", "docker", "veth", "br-", "virbr")):
                    continue

                iface_info = {
                    "name": interface,
                    "addresses": {},
                    "type": self._guess_interface_type(interface),
                    "monitoring_capable": self._check_monitoring_capability(interface),
                }

                # Get addresses
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    iface_info["addresses"]["ipv4"] = addrs[netifaces.AF_INET]
                if netifaces.AF_INET6 in addrs:
                    iface_info["addresses"]["ipv6"] = addrs[netifaces.AF_INET6]

                network_info["interfaces"].append(iface_info)

                # Set flags for interface types
                if iface_info["type"] == "wireless":
                    network_info["has_wireless"] = True
                elif iface_info["type"] == "ethernet":
                    network_info["has_ethernet"] = True

                # Determine default interface (first with IPv4 address)
                if (
                    network_info["default_interface"] is None
                    and "ipv4" in iface_info["addresses"]
                    and iface_info["addresses"]["ipv4"]
                ):
                    network_info["default_interface"] = interface

                # Track monitoring-capable interfaces
                if iface_info["monitoring_capable"]:
                    network_info["monitoring_capable"].append(interface)

        except Exception as e:
            self.logger.warning(f"Network detection failed: {e}")

        return network_info

    def _guess_interface_type(self, interface: str) -> str:
        """Guess the interface type based on naming conventions."""
        interface_lower = interface.lower()

        if any(
            prefix in interface_lower for prefix in ["wlan", "wifi", "wl", "ath", "iwl"]
        ):
            return "wireless"
        elif any(
            prefix in interface_lower for prefix in ["eth", "en", "em", "enp", "ens"]
        ):
            return "ethernet"
        elif any(prefix in interface_lower for prefix in ["ppp", "tun", "tap"]):
            return "virtual"
        elif "lo" in interface_lower:
            return "loopback"
        else:
            return "unknown"

    def _check_monitoring_capability(self, interface: str) -> bool:
        """Check if interface supports monitoring mode (simplified check)."""
        # This is a simplified check - real monitoring capability detection
        # would require more sophisticated testing
        try:
            if self.platform == "linux":
                # Check if interface supports monitor mode
                result = subprocess.run(
                    ["iwconfig", interface], capture_output=True, text=True, timeout=5
                )
                return result.returncode == 0 and "IEEE 802.11" in result.stdout
            else:
                # For non-Linux platforms, assume basic monitoring capability
                return True
        except (
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
            FileNotFoundError,
        ):
            return True  # Assume capable if we can't check

    def _detect_system_resources(self) -> Dict[str, Any]:
        """Detect system resources and capabilities."""
        import psutil

        resources = {
            "cpu_count": psutil.cpu_count(),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "memory_total": psutil.virtual_memory().total,
            "memory_available": psutil.virtual_memory().available,
            "disk_usage": {},
            "load_average": None,
            "recommended_threads": None,
            "recommended_memory_limit": None,
        }

        # Get disk usage for relevant paths
        for path in [str(self.project_root), "/tmp", str(Path.home())]:
            try:
                usage = psutil.disk_usage(path)
                resources["disk_usage"][path] = {
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": (usage.used / usage.total) * 100,
                }
            except BaseException:
                pass

        # Get load average (Unix-like systems)
        try:
            if hasattr(os, "getloadavg"):
                resources["load_average"] = os.getloadavg()
        except BaseException:
            pass

        # Calculate recommendations
        cpu_count = resources["cpu_count"] or 1
        memory_gb = resources["memory_total"] / (1024**3)

        # Recommended threads: 1-2 per CPU core, max 8
        resources["recommended_threads"] = min(max(cpu_count, 2), 8)

        # Recommended memory limit: 25% of available memory, min 512MB, max 4GB
        memory_limit = max(0.25 * resources["memory_available"], 512 * 1024 * 1024)
        resources["recommended_memory_limit"] = min(memory_limit, 4 * 1024**3)

        return resources

    def _check_permissions(self) -> Dict[str, Any]:
        """Check various system permissions."""
        permissions = {
            "root_access": os.geteuid() == 0 if hasattr(os, "geteuid") else False,
            "network_monitoring": False,
            "file_creation": {},
            "directory_access": {},
        }

        # Check network monitoring permissions (simplified)
        if self.platform != "windows":
            permissions["network_monitoring"] = permissions["root_access"]
        else:
            # Windows requires different checks
            permissions["network_monitoring"] = True  # Assume available

        # Check file creation permissions for important directories
        test_dirs = [
            str(self.project_root),
            str(self.project_root / "logs"),
            str(self.project_root / "DATA"),
            (
                "/tmp"
                if self.platform != "windows"
                else os.environ.get("TEMP", "C:\\temp")
            ),
        ]

        for test_dir in test_dirs:
            permissions["file_creation"][test_dir] = self._is_directory_writable(
                test_dir
            )

        return permissions

    def _detect_virtualization(self) -> Dict[str, Any]:
        """Detect if running in virtualized environment."""
        virtualization = {
            "detected": False,
            "type": None,
            "hypervisor": None,
            "container": False,
        }

        try:
            # Check for common virtualization indicators
            if Path("/proc/cpuinfo").exists():
                with open("/proc/cpuinfo", "r") as f:
                    cpuinfo = f.read()
                    if "hypervisor" in cpuinfo.lower():
                        virtualization["detected"] = True
                        if "vmware" in cpuinfo.lower():
                            virtualization["type"] = "vmware"
                        elif "xen" in cpuinfo.lower():
                            virtualization["type"] = "xen"
                        elif "kvm" in cpuinfo.lower():
                            virtualization["type"] = "kvm"

            # Check for container environments
            if Path("/.dockerenv").exists():
                virtualization["container"] = True
                virtualization["type"] = "docker"
            elif os.environ.get("container") == "podman":
                virtualization["container"] = True
                virtualization["type"] = "podman"

        except BaseException:
            pass

        return virtualization

    def _is_directory_writable(self, directory: str) -> bool:
        """Check if directory is writable."""
        try:
            test_path = Path(directory)
            if not test_path.exists():
                test_path.mkdir(parents=True, exist_ok=True)

            # Try to create a test file
            test_file = test_path / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            return True
        except (PermissionError, OSError):
            return False

    def generate_optimal_configuration(self) -> Dict[str, Any]:
        """Generate optimal configuration based on detected environment."""
        if not self.environment_info:
            self.detect_system_environment()

        config = self._generate_base_configuration()
        config.update(self._generate_path_configuration())
        config.update(self._generate_tool_configuration())
        config.update(self._generate_network_configuration())
        config.update(self._generate_performance_configuration())
        config.update(self._generate_security_configuration())
        config.update(self._generate_educational_configuration())

        self.detected_config = config
        return config

    def _generate_base_configuration(self) -> Dict[str, Any]:
        """Generate base configuration settings."""
        return {
            "version": "1.0.0",
            "generated_by": "auto_detection",
            "generation_date": str(Path(__file__).stat().st_mtime),
            "platform": self.environment_info["platform"],
            "auto_configured": True,
            "configuration_source": "system_detection",
        }

    def _generate_path_configuration(self) -> Dict[str, Any]:
        """Generate path configuration based on detected directories."""
        paths = self.environment_info["paths"]

        # Select best directories for each purpose
        config = {}

        # Data directory
        data_dirs = paths.get("data_dirs_writable", [])
        if data_dirs:
            config["DATA_DIR"] = data_dirs[0]
        else:
            config["DATA_DIR"] = str(self.project_root / "DATA")

        # Configuration directory
        config_dirs = paths.get("config_dirs_writable", [])
        if config_dirs:
            config["CONFIG_DIR"] = config_dirs[0]
        else:
            config["CONFIG_DIR"] = str(self.project_root / "CONFIGURATION")

        # Log directory
        log_dirs = paths.get("log_dirs_writable", [])
        if log_dirs:
            config["LOG_DIR"] = log_dirs[0]
        else:
            config["LOG_DIR"] = str(self.project_root / "logs")

        # Cache directory
        cache_dirs = paths.get("cache_dirs_writable", [])
        if cache_dirs:
            config["CACHE_DIR"] = cache_dirs[0]
        else:
            config["CACHE_DIR"] = str(self.project_root / "cache")

        # Derived paths
        config.update(
            {
                "EXTRACT_DIR": str(
                    Path(config["DATA_DIR"]) / "runtime" / "extracted-files"
                ),
                "RULES_DIR": str(self.project_root / "rules"),
                "DB_FILE": str(
                    Path(config["DATA_DIR"]) / "persistent" / "databases" / "alerts.db"
                ),
                "LOG_FILE": str(Path(config["LOG_DIR"]) / "yara_scan.log"),
                "PID_FILE": str(Path(config["DATA_DIR"]) / "runtime" / "app.pid"),
            }
        )

        return config

    def _generate_tool_configuration(self) -> Dict[str, Any]:
        """Generate tool-specific configuration."""
        tools = self.environment_info["tools"]
        config = {"TOOLS_AVAILABLE": {}}

        # Zeek configuration
        zeek = tools.get("zeek", {})
        if zeek.get("available"):
            config["ZEEK_ENABLED"] = True
            config["ZEEK_BINARY"] = zeek.get("binary_path")
            config["ZEEK_SCRIPTS_DIR"] = zeek.get("scripts_path")
            config["TOOLS_AVAILABLE"]["zeek"] = True
        else:
            config["ZEEK_ENABLED"] = False
            config["TOOLS_AVAILABLE"]["zeek"] = False

        # YARA configuration
        yara = tools.get("yara", {})
        if yara.get("python_module") or yara.get("available"):
            config["YARA_ENABLED"] = True
            config["YARA_BINARY"] = yara.get("binary_path")
            config["YARA_PYTHON_MODULE"] = yara.get("python_module", False)
            config["TOOLS_AVAILABLE"]["yara"] = True
        else:
            config["YARA_ENABLED"] = False
            config["TOOLS_AVAILABLE"]["yara"] = False

        # Suricata configuration
        suricata = tools.get("suricata", {})
        if suricata.get("available"):
            config["SURICATA_ENABLED"] = True
            config["SURICATA_BINARY"] = suricata.get("binary_path")
            config["SURICATA_CONFIG"] = suricata.get("config_path")
            config["SURICATA_RULES_DIR"] = suricata.get("rules_paths", [None])[0]
            config["SURICATA_LOG_DIR"] = suricata.get("log_path")
            config["SURICATA_EVE_JSON"] = suricata.get("eve_json_support", False)
            config["TOOLS_AVAILABLE"]["suricata"] = True
        else:
            config["SURICATA_ENABLED"] = False
            config["TOOLS_AVAILABLE"]["suricata"] = False

        return config

    def _generate_network_configuration(self) -> Dict[str, Any]:
        """Generate network configuration."""
        network = self.environment_info["network"]
        config = {}

        # Default interface
        if network.get("default_interface"):
            config["NETWORK_INTERFACE"] = network["default_interface"]
        elif network.get("interfaces"):
            config["NETWORK_INTERFACE"] = network["interfaces"][0]["name"]
        else:
            config["NETWORK_INTERFACE"] = "auto"

        # Monitoring capabilities
        config["MONITORING_INTERFACES"] = network.get("monitoring_capable", [])
        config["HAS_WIRELESS"] = network.get("has_wireless", False)
        config["HAS_ETHERNET"] = network.get("has_ethernet", False)

        # API configuration
        config.update(
            {
                "API_HOST": "127.0.0.1",
                "API_PORT": 8000,
                "API_ENABLED": True,
                "WEB_INTERFACE": True,
            }
        )

        return config

    def _generate_performance_configuration(self) -> Dict[str, Any]:
        """Generate performance-related configuration."""
        resources = self.environment_info["resources"]

        config = {
            "THREADS": resources.get("recommended_threads", 2),
            "MAX_MEMORY_MB": int(
                resources.get("recommended_memory_limit", 1024**3) / (1024**2)
            ),
            "MAX_FILE_SIZE": 20 * 1024 * 1024,  # 20MB
            "SCAN_INTERVAL": 10,
            "BATCH_SIZE": 50,
            "QUEUE_SIZE": 1000,
        }

        # Adjust based on available resources
        memory_gb = resources.get("memory_total", 0) / (1024**3)
        cpu_count = resources.get("cpu_count", 1)

        if memory_gb < 4:
            # Low memory system
            config["THREADS"] = min(config["THREADS"], 2)
            config["MAX_FILE_SIZE"] = 10 * 1024 * 1024  # 10MB
            config["BATCH_SIZE"] = 25
        elif memory_gb > 16:
            # High memory system
            config["THREADS"] = min(cpu_count * 2, 12)
            config["MAX_FILE_SIZE"] = 100 * 1024 * 1024  # 100MB
            config["BATCH_SIZE"] = 100

        return config

    def _generate_security_configuration(self) -> Dict[str, Any]:
        """Generate security-related configuration."""
        permissions = self.environment_info["permissions"]

        config = {
            "REQUIRE_ROOT": permissions.get("network_monitoring", False),
            "ENABLE_NETWORK_MONITORING": permissions.get("network_monitoring", False),
            "SECURE_MODE": True,
            "LOG_LEVEL": "INFO",
            "AUDIT_LOGGING": True,
            "FILE_INTEGRITY_CHECK": True,
        }

        # Adjust based on virtualization
        virtualization = self.environment_info["virtualization"]
        if virtualization.get("container"):
            config["CONTAINER_MODE"] = True
            config["REQUIRE_ROOT"] = False
        else:
            config["CONTAINER_MODE"] = False

        return config

    def _generate_educational_configuration(self) -> Dict[str, Any]:
        """Generate educational platform specific configuration."""
        return {
            "PLATFORM_MODE": "educational",
            "TUTORIAL_MODE": True,
            "BEGINNER_MODE": True,
            "INTERACTIVE_HELP": True,
            "SHOW_EXPLANATIONS": True,
            "GUIDED_WORKFLOWS": True,
            "ACHIEVEMENT_TRACKING": True,
            "PROGRESS_REPORTING": True,
            "AUTO_START_SERVICES": False,
            "DETAILED_LOGGING": False,
            "EXPERIENCE_LEVEL": "beginner",
        }

    def save_configuration(self, output_path: Optional[Path] = None) -> Path:
        """Save the generated configuration to file."""
        if not self.detected_config:
            self.generate_optimal_configuration()

        if output_path is None:
            output_path = (
                self.project_root / "CONFIGURATION" / "auto_detected_config.json"
            )

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Add metadata
        config_with_metadata = {
            "# Auto-Generated Configuration": "Created by intelligent system detection",
            "detection_metadata": {
                "detection_date": str(Path(__file__).stat().st_mtime),
                "platform": self.environment_info["platform"]["system"],
                "tools_detected": list(self.environment_info["tools"].keys()),
                "auto_configuration_version": "1.0.0",
            },
            **self.detected_config,
        }

        # Save configuration
        with open(output_path, "w") as f:
            json.dump(config_with_metadata, f, indent=4, sort_keys=True)

        self.logger.info(f"Configuration saved to: {output_path}")
        return output_path

    def validate_configuration(self, config: Optional[Dict] = None) -> Dict[str, Any]:
        """Validate the generated configuration."""
        if config is None:
            config = self.detected_config

        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": [],
        }

        # Check required paths exist and are writable
        path_checks = [
            ("DATA_DIR", "data directory"),
            ("LOG_DIR", "log directory"),
            ("EXTRACT_DIR", "extraction directory"),
        ]

        for path_key, description in path_checks:
            if path_key in config:
                path = Path(config[path_key])
                if not self._is_directory_writable(str(path)):
                    validation_results["errors"].append(
                        f"{description} not writable: {path}"
                    )
                    validation_results["valid"] = False

        # Check tool availability vs configuration
        tools = self.environment_info.get("tools", {})

        if config.get("ZEEK_ENABLED") and not tools.get("zeek", {}).get("available"):
            validation_results["warnings"].append(
                "Zeek is enabled but not detected on system"
            )

        if config.get("YARA_ENABLED") and not (
            tools.get("yara", {}).get("available")
            or tools.get("yara", {}).get("python_module")
        ):
            validation_results["warnings"].append(
                "YARA is enabled but not detected on system"
            )

        if config.get("SURICATA_ENABLED") and not tools.get("suricata", {}).get(
            "available"
        ):
            validation_results["warnings"].append(
                "Suricata is enabled but not detected on system"
            )

        # Performance recommendations
        resources = self.environment_info.get("resources", {})
        if resources.get("memory_total", 0) < 2 * 1024**3:  # Less than 2GB
            validation_results["recommendations"].append(
                "Consider increasing system memory for better performance"
            )

        if config.get("THREADS", 0) > resources.get("cpu_count", 1) * 2:
            validation_results["recommendations"].append(
                "Thread count may be too high for available CPU cores"
            )

        return validation_results


def main():
    """Main function for testing the auto-detection system."""
    detector = SystemDetector()

    print("Starting comprehensive system detection...")
    env_info = detector.detect_system_environment()

    print("\n=== System Environment ===")
    print(
        f"Platform: {
            env_info['platform']['system']} {
            env_info['platform']['release']}"
    )
    print(f"Python: {env_info['platform']['python_version']}")
    print(f"Architecture: {env_info['platform']['architecture'][0]}")

    print("\n=== Security Tools ===")
    for tool, info in env_info["tools"].items():
        if isinstance(info, dict) and "available" in info:
            status = "✅ Available" if info["available"] else "❌ Not Found"
            version = info.get("version", "Unknown version")
            print(f"{tool.upper()}: {status} ({version})")

    print("\n=== Network Interfaces ===")
    for interface in env_info["network"]["interfaces"]:
        print(
            f"{interface['name']}: {interface['type']} "
            f"({'monitoring capable' if interface['monitoring_capable'] else 'standard'})"
        )

    print("\n=== System Resources ===")
    resources = env_info["resources"]
    print(f"CPU Cores: {resources['cpu_count']}")
    print(f"Memory: {resources['memory_total'] / (1024**3):.1f} GB")
    print(f"Recommended Threads: {resources['recommended_threads']}")

    print("\nGenerating optimal configuration...")
    config = detector.generate_optimal_configuration()

    print("\nValidating configuration...")
    validation = detector.validate_configuration(config)

    if validation["valid"]:
        print("✅ Configuration is valid")
    else:
        print("❌ Configuration has errors:")
        for error in validation["errors"]:
            print(f"  - {error}")

    if validation["warnings"]:
        print("\n⚠️ Warnings:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")

    if validation["recommendations"]:
        print("\n💡 Recommendations:")
        for rec in validation["recommendations"]:
            print(f"  - {rec}")

    # Save configuration
    config_path = detector.save_configuration()
    print(f"\n✅ Configuration saved to: {config_path}")


if __name__ == "__main__":
    main()
