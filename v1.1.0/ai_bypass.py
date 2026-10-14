#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-BYPASS MANAGER v1.1.0 (Pure Python Edition)
Unified bypass: ChatGPT, Claude, Gemini & Google Antigravity.
Zero Dependencies: runs on standard Python library without pip install.
"""

import os
import sys
import time
import json
import socket
import struct
import platform
import subprocess
import shutil
import hashlib
import re
import mmap
import http.client
import ssl
import threading
import ctypes
from urllib.parse import urlparse

# ==============================================================================
# 1. PLATFORM CHECK & AUTOMATIC UAC ELEVATION (WINDOWS)
# ==============================================================================

CURRENT_OS = platform.system()
# Инициализация консоли
def init_console():
    if CURRENT_OS == "Windows":
        try:
            from ctypes import wintypes
            kernel32 = ctypes.windll.kernel32

            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleCP(65001)

            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
            if hasattr(sys.stdin, "reconfigure"):
                try:
                    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
                except Exception:
                    pass

            class CONSOLE_FONT_INFO_EX(ctypes.Structure):
                _fields_ = [
                    ("cbSize", wintypes.ULONG),
                    ("nFont", wintypes.DWORD),
                    ("dwFontSizeX", wintypes.SHORT),
                    ("dwFontSizeY", wintypes.SHORT),
                    ("FontFamily", wintypes.UINT),
                    ("FontWeight", wintypes.UINT),
                    ("FaceName", wintypes.WCHAR * 32),
                ]

            font = CONSOLE_FONT_INFO_EX()
            font.cbSize = ctypes.sizeof(CONSOLE_FONT_INFO_EX)
            font.FaceName = "Consolas"
            font.dwFontSizeY = 16
            font.FontFamily = 54
            font.FontWeight = 400

            h_con = kernel32.CreateFileW("CONOUT$", 0xC0000000, 3, None, 3, 0, None)
            if h_con != -1 and h_con != 0:
                kernel32.SetCurrentConsoleFontEx(h_con, False, ctypes.byref(font))
                mode = wintypes.DWORD()
                if kernel32.GetConsoleMode(h_con, ctypes.byref(mode)):
                    kernel32.SetConsoleMode(h_con, mode.value | 0x0004 | 0x0008)
                kernel32.CloseHandle(h_con)

            h_std = kernel32.GetStdHandle(-11)
            if h_std and h_std != -1:
                kernel32.SetCurrentConsoleFontEx(h_std, False, ctypes.byref(font))
                mode = wintypes.DWORD()
                if kernel32.GetConsoleMode(h_std, ctypes.byref(mode)):
                    kernel32.SetConsoleMode(h_std, mode.value | 0x0004 | 0x0008)

            try:
                import winreg
                sanitized_py = sys.executable.replace("\\", "_").replace(":", "")
                for subkey in [
                    r"Console",
                    r"Console\%SystemRoot%_System32_cmd.exe",
                    rf"Console\{sanitized_py}"
                ]:
                    try:
                        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, subkey) as k:
                            winreg.SetValueEx(k, "FaceName", 0, winreg.REG_SZ, "Consolas")
                            winreg.SetValueEx(k, "FontFamily", 0, winreg.REG_DWORD, 54)
                            winreg.SetValueEx(k, "FontSize", 0, winreg.REG_DWORD, 0x00100000)
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

init_console()

CLR_RESET   = "\033[0m"
CLR_CYAN    = "\033[96m"
CLR_GREEN   = "\033[92m"
CLR_YELLOW  = "\033[93m"
CLR_RED     = "\033[91m"
CLR_MAGENTA = "\033[95m"
CLR_GRAY    = "\033[90m"
CLR_WHITE   = "\033[97m"

def is_admin() -> bool:
    if CURRENT_OS == "Windows":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        return os.geteuid() == 0

def ensure_admin():
    if is_admin():
        return
    if CURRENT_OS == "Windows":
        script = os.path.abspath(sys.argv[0])
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        cmd_args = f'"{script}" {params}'.strip()
        print(f"\n{CLR_YELLOW}[*] Administrator privileges required. Requesting UAC elevation...{CLR_RESET}")
        try:
            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, cmd_args, None, 1)
            if ret > 32:
                sys.exit(0)
        except Exception:
            pass
        try:
            ps_cmd = f'Start-Process "{sys.executable}" -ArgumentList \'{cmd_args}\' -Verb RunAs'
            res = subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps_cmd])
            if res.returncode == 0:
                sys.exit(0)
        except Exception:
            pass
        print(f"\n{CLR_RED}[!] Error: Failed to obtain Administrator privileges.{CLR_RESET}")
        print("    Please run the script as Administrator.")
        input(f"\n{CLR_GRAY}Press Enter to exit...{CLR_RESET}")
        sys.exit(1)
    else:
        print("[!] Root privileges required to configure network rules.")
        print("    Rerun this script as Administrator", sys.argv[0])
        sys.exit(1)

# ==============================================================================
# 2. SERVER & DOMAIN CONFIGURATION
# ==============================================================================

UPSTREAM_SERVERS = [
    "83.220.169.155",
    "195.133.25.16",
    "212.109.195.93"
]

GEOHIDE_DNS = ["45.155.204.190", "37.230.192.51"]

COMSS_COMMENT = "AI-Bypass-SmartDNS"
DOH_COMMENT   = "AI-Bypass-DoH"

CHATGPT_DOMAINS = [
    "chatgpt.com", ".chatgpt.com",
    "openai.com", ".openai.com",
    "oaistatic.com", ".oaistatic.com",
    "oaiusercontent.com", ".oaiusercontent.com",
]

CLAUDE_DOMAINS = [
    "claude.ai", ".claude.ai",
    "anthropic.com", ".anthropic.com",
]

GEMINI_DOMAINS = [
    "gemini.google.com", ".gemini.google.com",
    "gemini.google", ".gemini.google",
    "alkalicore-pa.clients6.google.com", ".alkalicore-pa.clients6.google.com",
    "alkalimakersuite-pa.clients6.google.com", ".alkalimakersuite-pa.clients6.google.com",
    "webchannel-alkalimakersuite-pa.clients6.google.com", ".webchannel-alkalimakersuite-pa.clients6.google.com",
    "alkalimakersuite-pa.googleapis.com", ".alkalimakersuite-pa.googleapis.com",
    "alkalimakersuiteapplets.pa.googleapis.com", ".alkalimakersuiteapplets.pa.googleapis.com",
    "generativelanguage.googleapis.com", ".generativelanguage.googleapis.com",
    "aistudio.google.com", ".aistudio.google.com",
    "ai.studio", ".ai.studio",
    "ai.google.dev", ".ai.google.dev",
    "bard.google.com", ".bard.google.com",
    "generativeai.google", ".generativeai.google",
    "notebooklm.google.com", ".notebooklm.google.com",
    "notebooklm.google", ".notebooklm.google",
    "notebooklm-pa.googleapis.com", ".notebooklm-pa.googleapis.com",
    "makersuite.google.com", ".makersuite.google.com",
    "aisandbox-pa.googleapis.com", ".aisandbox-pa.googleapis.com",
    "deepmind.google", ".deepmind.google",
]

ANTIGRAVITY_DOMAINS = [
    "daily-cloudcode-pa.googleapis.com", ".daily-cloudcode-pa.googleapis.com",
    "cloudcode-pa.googleapis.com", ".cloudcode-pa.googleapis.com",
    "generativelanguage.googleapis.com", ".generativelanguage.googleapis.com",
]

CLOUDCODE_HOSTS = [
    "daily-cloudcode-pa.googleapis.com",
    "cloudcode-pa.googleapis.com",
]

LEGACY_COMMENTS = {
    "AI-Bypass-ChatGPT",
    "AI-Bypass-Claude",
    "AI-Bypass-Gemini",
    "ANTIGRAVITY-BYPASS-RUSSIA",
}

def _dedup(seq):
    seen = set()
    out = []
    for d in seq:
        if d not in seen:
            seen.add(d)
            out.append(d)
    return out

def _is_google_family(name: str) -> bool:
    """True if the domain belongs to the Google-family set we care about."""
    if not name:
        return False
    n = name.lower().rstrip(".")
    for suffix in ("google.com", "googleapis.com", "gstatic.com", "google.dev", "google"):
        if n == suffix or n.endswith("." + suffix):
            return True
    return False

# ==============================================================================
# 3. RAW RFC-1035 UDP DNS PROBING (ZERO DEPENDENCIES)
# ==============================================================================

def build_dns_query(domain: str, tid: int = 0xAAAA) -> bytes:
    header = struct.pack(">HHHHHH", tid & 0xFFFF, 0x0100, 1, 0, 0, 0)
    qname = b"".join(bytes([len(p)]) + p.encode("ascii") for p in domain.split(".")) + b"\x00"
    qtype_qclass = struct.pack(">HH", 1, 1)
    return header + qname + qtype_qclass

def _dns_skip_name_buf(buf: bytes, pos: int) -> int:
    hops = 0
    while pos < len(buf) and hops < 64:
        hops += 1
        l = buf[pos]
        if l == 0:
            return pos + 1
        if (l & 0xC0) == 0xC0:
            return pos + 2
        pos += 1 + l
    return len(buf)

def parse_a_records(buf: bytes) -> list:
    out = []
    if len(buf) < 12:
        return out
    qd, an = struct.unpack(">HH", buf[4:8])
    i = 12
    for _ in range(qd):
        i = _dns_skip_name_buf(buf, i)
        i += 4
    for _ in range(an):
        if i >= len(buf):
            break
        i = _dns_skip_name_buf(buf, i)
        if i + 10 > len(buf):
            break
        rtype, _, _, rdlen = struct.unpack(">HHIH", buf[i:i+10])
        i += 10
        if i + rdlen > len(buf):
            break
        if rtype == 1 and rdlen == 4:
            out.append(".".join(str(b) for b in buf[i:i+4]))
        i += rdlen
    return out

_GOOGLE_PREFIXES = {
    (64, 233), (66, 102), (66, 249), (72, 14), (74, 125),
    (142, 250), (142, 251), (172, 217), (173, 194), (192, 178),
    (216, 58), (216, 239),
}

def looks_google(ip: str) -> bool:
    try:
        a, b, _, _ = (int(x) for x in ip.split("."))
    except Exception:
        return False
    return (a, b) in _GOOGLE_PREFIXES

def probe_dns_server(ip: str, domain: str = "chatgpt.com", timeout: float = 1.2):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(timeout)
    start_time = time.perf_counter()
    try:
        query = build_dns_query(domain)
        sock.sendto(query, (ip, 53))
        resp, _ = sock.recvfrom(1024)
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        if len(resp) > 12 and (resp[3] & 0x0F) == 0:
            ancount = struct.unpack(">H", resp[6:8])[0]
            if ancount > 0:
                return True, elapsed_ms
    except Exception:
        pass
    finally:
        sock.close()
    return False, 9999

def find_best_server() -> str:
    print(f"\n{CLR_CYAN}[*] Testing DNS servers latency and availability...{CLR_RESET}")
    results = []
    for srv in UPSTREAM_SERVERS:
        print(f"    Testing {srv}... ", end="", flush=True)
        ok, ms = probe_dns_server(srv)
        if ok:
            print(f"{CLR_GREEN}OK ({ms} ms){CLR_RESET}")
            results.append((srv, ms))
        else:
            print(f"{CLR_RED}Timeout{CLR_RESET}")

    if not results:
        fallback = UPSTREAM_SERVERS[0]
        print(f"\n{CLR_YELLOW}[!] Servers did not respond to quick probe. Using fallback: {fallback}{CLR_RESET}")
        return fallback

    results.sort(key=lambda x: x[1])
    best = results[0]
    print(f"\n{CLR_GREEN}[+] Selected fastest server: {best[0]} ({best[1]} ms latency){CLR_RESET}")
    return best[0]

def query_geohide_dns(host: str, timeout: float = 2.0) -> list:
    found = []
    for ns in GEOHIDE_DNS:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            q = build_dns_query(host, tid=0x4B1D)
            s.settimeout(timeout)
            s.sendto(q, (ns, 53))
            data, _ = s.recvfrom(4096)
            for ip in parse_a_records(data):
                if not looks_google(ip) and ip not in found:
                    found.append(ip)
        except Exception as e:
            _doh_log(f"geohide dns {host} via {ns}: {e}")
        finally:
            s.close()
    return found

# ==============================================================================
# 3.5. LOCAL DOH FORWARDER FOR GEMINI & ANTIGRAVITY (RFC 8484)
# ==============================================================================

DOH_ENDPOINTS = [
    "https://dns.dns-ai.ru/dns-query",
    "https://dns-ai.ru/dns-query",
    "https://dns.comss.one/dns-query",
]
DOH_BOOTSTRAP   = ["192.144.59.14", "186.246.49.127", "94.232.43.149"]
DOH_LISTEN      = "127.0.0.1"
DOH_PORT        = 53

DOH_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), "AIBypass", "doh")
DOH_PID = os.path.join(DOH_DIR, "server.pid")
DOH_LOG = os.path.join(DOH_DIR, "server.log")
_doh_log_lock = threading.Lock()

TASK_NAME = "AIBypass-DoH"

def _doh_ensure_dir():
    os.makedirs(DOH_DIR, exist_ok=True)

def _doh_log(msg: str):
    _doh_ensure_dir()
    with _doh_log_lock:
        try:
            with open(DOH_LOG, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
        except Exception:
            pass

class _DoHConn(http.client.HTTPSConnection):
    def __init__(self, host, bootstrap_ip, port, timeout):
        super().__init__(host, port, timeout=timeout,
                         context=ssl.create_default_context())
        self._bootstrap_ip = bootstrap_ip

    def connect(self):
        raw = socket.create_connection((self._bootstrap_ip, self.port), self.timeout)
        self.sock = self._context.wrap_socket(raw, server_hostname=self.host)

def _try_doh_endpoint(endpoint: str, query: bytes, timeout: float) -> bytes:
    parsed = urlparse(endpoint)
    host = parsed.hostname
    port = parsed.port or 443
    path = parsed.path or "/dns-query"
    last = None
    for ip in DOH_BOOTSTRAP:
        try:
            conn = _DoHConn(host, ip, port, timeout)
            conn.request("POST", path, body=query, headers={
                "Content-Type": "application/dns-message",
                "Accept": "application/dns-message",
                "Host": host,
            })
            resp = conn.getresponse()
            status = resp.status
            ct = (resp.getheader("Content-Type") or "").lower()
            body = resp.read()
            conn.close()
            if status != 200:
                last = f"HTTP {status}"; continue
            if not ct.startswith("application/dns-message"):
                last = f"Content-Type {ct!r}"; continue
            if len(body) < 12 or body[:2] != query[:2]:
                last = "txid mismatch"; continue
            return body
        except Exception as e:
            last = repr(e)
    raise RuntimeError(f"DoH failed: {last}")

def doh_query(query: bytes, timeout: float = 3.0) -> bytes:
    last_err = "no endpoint"
    for ep in DOH_ENDPOINTS:
        try:
            return _try_doh_endpoint(ep, query, timeout)
        except Exception as e:
            last_err = f"{ep}: {e}"
    raise RuntimeError(f"all DoH endpoints failed; last: {last_err}")

def _dns_cache_key(q: bytes):
    if len(q) < 12:
        return None
    i, labels = 12, []
    while i < len(q):
        L = q[i]
        if L == 0:
            i += 1; break
        if L & 0xC0:
            return None
        i += 1
        if i + L > len(q):
            return None
        labels.append(q[i:i + L].lower())
        i += L
    if i + 4 > len(q):
        return None
    return (b".".join(labels), struct.unpack(">H", q[i:i + 2])[0])

def _dns_skip_name(p: bytes, i: int) -> int:
    while i < len(p):
        L = p[i]
        if L == 0:
            return i + 1
        if L & 0xC0:
            return i + 2
        i += 1 + L
    return i

def _dns_min_ttl(resp: bytes) -> int:
    if len(resp) < 12:
        return 60
    qd, an = struct.unpack(">HH", resp[4:8])
    i = 12
    for _ in range(qd):
        i = _dns_skip_name(resp, i) + 4
    ttl = 3600
    for _ in range(an):
        if i >= len(resp):
            break
        i = _dns_skip_name(resp, i)
        if i + 10 > len(resp):
            break
        _, _, rttl, rdlen = struct.unpack(">HHIH", resp[i:i + 10])
        i += 10
        if rttl < ttl:
            ttl = rttl
        i += rdlen
    return max(1, ttl)

def _query_udp_single(query: bytes, server: str, timeout: float) -> bytes:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    try:
        s.sendto(query, (server, 53))
        resp, _ = s.recvfrom(4096)
        if len(resp) >= 12 and resp[:2] == query[:2]:
            return resp
    finally:
        s.close()
    return None

def _udp_fallback_improved(query: bytes, qname: str, is_google: bool, timeout: float = 1.5) -> bytes:
    """Prefer geohide non-Google answers for Google-family domains; else Comss."""
    if is_google:
        for srv in GEOHIDE_DNS:
            try:
                resp = _query_udp_single(query, srv, timeout)
                if resp:
                    addrs = parse_a_records(resp)
                    non_google = [a for a in addrs if not looks_google(a)]
                    if non_google:
                        return resp
            except Exception:
                continue
    for srv in UPSTREAM_SERVERS:
        try:
            resp = _query_udp_single(query, srv, timeout)
            if resp:
                return resp
        except Exception:
            continue
    return None

def discover_substituters(test_domains: list, timeout: float = 3.0) -> list:
    """Return NS IPs that return non-Google A records for any test domain.
    Geohide queried first (preferred), then Comss. Retries each provider once."""
    providers = []
    for srv in GEOHIDE_DNS + UPSTREAM_SERVERS:
        substituted = False
        for d in test_domains:
            if substituted:
                break
            for attempt in (0, 1):
                try:
                    q = build_dns_query(d, tid=0x4B00 + attempt)
                    resp = _query_udp_single(q, srv, timeout)
                    if not resp:
                        continue
                    addrs = parse_a_records(resp)
                    non_google = [a for a in addrs if not looks_google(a)]
                    if non_google:
                        _doh_log(f"substituter: {srv} → {d} = {non_google}")
                        providers.append(srv)
                        substituted = True
                        break
                except Exception as e:
                    _doh_log(f"discover_substituters {srv} {d}: {e}")
                    continue
    return providers

def _make_nodata_response(query: bytes) -> bytes:
    """Return NOERROR/NODATA for an AAAA question; keep the question section."""
    if len(query) < 12:
        return query
    end = _dns_skip_name(query, 12) + 4
    if end > len(query):
        return query
    r = bytearray(query[:end])
    r[2] = (query[2] & 0x01) | 0x80
    r[3] = 0x80
    r[6:12] = b"\x00" * 6
    return bytes(r)

class _DnsCache:
    def __init__(self, cap: int = 4096):
        self._d = {}
        self._lock = threading.Lock()
        self._cap = cap

    def get(self, key):
        with self._lock:
            e = self._d.get(key)
            if not e:
                return None
            resp, exp = e
            if time.time() >= exp:
                del self._d[key]
                return None
            return resp

    def put(self, key, resp, ttl):
        with self._lock:
            if len(self._d) >= self._cap:
                oldest = min(self._d, key=lambda k: self._d[k][1])
                del self._d[oldest]
            self._d[key] = (resp, time.time() + max(5, ttl))

def _handle_doh_query(sock, query: bytes, addr, cache: "_DnsCache"):
    if len(query) < 12:
        return
    key = _dns_cache_key(query)
    qtype = None
    qname = ""
    if key:
        qname = key[0].decode("ascii", "ignore")
        qtype = key[1]

    if qtype in (28, 64, 65) and _is_google_family(qname):
        try:
            sock.sendto(_make_nodata_response(query), addr)
        except Exception:
            pass
        return

    if key:
        cached = cache.get(key)
        if cached:
            r = bytearray(cached)
            r[0:2] = query[0:2]
            try:
                sock.sendto(bytes(r), addr)
            except Exception:
                pass
            return

    resp = None
    try:
        resp = doh_query(query)
    except Exception as e:
        _doh_log(f"DoH error: {e}")

    if resp is None:
        resp = _udp_fallback_improved(query, qname, _is_google_family(qname))

    if resp is None:
        try:
            r = bytearray(query)
            r[2] = (r[2] & 0x01) | 0x80
            r[3] = 0x02
            r[6:12] = b"\x00" * 6
            sock.sendto(bytes(r), addr)
        except Exception:
            pass
        return

    if key and qtype in (1, 28):
        try:
            cache.put(key, resp, _dns_min_ttl(resp))
        except Exception:
            pass
    try:
        sock.sendto(resp, addr)
    except Exception:
        pass

def _disable_udp_conn_reset(sock: socket.socket):
    """Windows: ICMP port-unreachable must not close our UDP socket."""
    if CURRENT_OS != "Windows":
        return
    try:
        SIO_UDP_CONNRESET = 0x9800000C
        bytes_returned = ctypes.c_ulong(0)
        disable = ctypes.c_ulong(0)
        ctypes.windll.ws2_32.WSAIoctl(
            sock.fileno(),
            SIO_UDP_CONNRESET,
            ctypes.byref(disable), ctypes.sizeof(disable),
            None, 0,
            ctypes.byref(bytes_returned),
            None, None
        )
    except Exception as e:
        _doh_log(f"SIO_UDP_CONNRESET failed: {e}")

def doh_server_main() -> int:
    _doh_ensure_dir()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    _disable_udp_conn_reset(sock)
    try:
        sock.bind((DOH_LISTEN, DOH_PORT))
    except OSError as e:
        _doh_log(f"FATAL bind {DOH_LISTEN}:{DOH_PORT}: {e}")
        return 1
    try:
        with open(DOH_PID, "w") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass
    cache = _DnsCache()
    sock.settimeout(0.5)
    _doh_log(f"DoH forwarder up on {DOH_LISTEN}:{DOH_PORT} pid={os.getpid()}")
    try:
        while True:
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError as e:
                _doh_log(f"recvfrom error (continuing): {e}")
                time.sleep(0.1)
                continue
            threading.Thread(target=_handle_doh_query,
                             args=(sock, data, addr, cache),
                             daemon=True).start()
    finally:
        sock.close()
        try:
            if os.path.exists(DOH_PID):
                os.remove(DOH_PID)
        except Exception:
            pass
        _doh_log("DoH forwarder down")
    return 0

_doh_running_cache: dict = {"ts": 0.0, "result": False}
_doh_running_lock = threading.Lock()

def doh_server_running(max_age: float = 1.5) -> bool:
    """Return True only if OUR forwarder is alive (PID present + port answers).

    Result is cached for *max_age* seconds so repeated calls from print_status()
    don't spawn a new tasklist process on every menu redraw.
    Pass max_age=0 to force a fresh check (used in doh_server_start loop).
    """
    now = time.time()
    with _doh_running_lock:
        if max_age > 0 and now - _doh_running_cache["ts"] < max_age:
            return _doh_running_cache["result"]

    result = _doh_server_running_uncached()

    with _doh_running_lock:
        _doh_running_cache["ts"] = time.time()
        _doh_running_cache["result"] = result
    return result

def _doh_server_running_uncached() -> bool:
    pid = doh_server_pid()
    if pid is None:
        return False
    # Verify the process is actually alive (Windows: tasklist check)
    if CURRENT_OS == "Windows":
        try:
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/NH", "/FO", "CSV"],
                capture_output=True, text=True, errors="replace"
            ).stdout
            if str(pid) not in out:
                return False
        except Exception:
            pass
    # Probe the port
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(1.0)
        s.sendto(build_dns_query("probe.local"), (DOH_LISTEN, DOH_PORT))
        s.recvfrom(1024)
        return True
    except Exception:
        return False
    finally:
        s.close()

def doh_server_pid():
    try:
        with open(DOH_PID) as f:
            return int(f.read().strip())
    except Exception:
        return None

def doh_server_start() -> bool:
    if doh_server_running(max_age=0):
        return True
    _doh_ensure_dir()
    python = sys.executable
    if python.lower().endswith("python.exe"):
        pyw = python[:-10] + "pythonw.exe"
        if os.path.exists(pyw):
            python = pyw
    script = os.path.abspath(sys.argv[0])
    DETACHED_PROCESS = 0x00000008
    CREATE_NEW_PROCESS_GROUP = 0x00000200
    try:
        log = open(DOH_LOG, "a", encoding="utf-8")
        subprocess.Popen(
            [python, script, "--doh-server"],
            stdout=log, stderr=log, stdin=subprocess.DEVNULL,
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
        )
    except Exception as e:
        print(f"  {CLR_RED}[!] Cannot spawn DoH forwarder: {e}{CLR_RESET}")
        return False
    for _ in range(20):
        time.sleep(0.25)
        if doh_server_running(max_age=0):
            return True
    print(f"  {CLR_RED}[!] DoH forwarder did not answer on {DOH_LISTEN}:{DOH_PORT}{CLR_RESET}")
    print(f"      see {DOH_LOG}")
    return False

def doh_server_stop() -> bool:
    pid = doh_server_pid()
    if pid:
        try:
            subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                           capture_output=True, timeout=3)
        except Exception:
            pass
    for _ in range(10):
        if not doh_server_running(max_age=0):
            try:
                if os.path.exists(DOH_PID):
                    os.remove(DOH_PID)
            except Exception:
                pass
            return True
        time.sleep(0.2)
    return False

def scheduled_task_exists() -> bool:
    try:
        res = subprocess.run(["schtasks", "/Query", "/TN", TASK_NAME],
                             capture_output=True)
        return res.returncode == 0
    except Exception:
        return False

def install_scheduled_task() -> bool:
    python = sys.executable
    if python.lower().endswith("python.exe"):
        pyw = python[:-10] + "pythonw.exe"
        if os.path.exists(pyw):
            python = pyw
    script = os.path.abspath(sys.argv[0])
    try:
        subprocess.run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
                       capture_output=True)
    except Exception:
        pass
    cmd = f'"{python}" "{script}" --doh-server'
    try:
        res = subprocess.run(
            ["schtasks", "/Create", "/SC", "ONLOGON", "/TN", TASK_NAME,
             "/TR", cmd, "/RL", "HIGHEST", "/F"],
            capture_output=True, text=True, errors="replace"
        )
        return res.returncode == 0
    except Exception:
        return False

def uninstall_scheduled_task():
    try:
        subprocess.run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
                       capture_output=True)
    except Exception:
        pass

def ensure_forwarder_if_needed():
    rules = get_active_nrpt_rules()
    needs_doh = any("127.0.0.1" in (r.get("NameServers") or "") for r in rules)
    if not needs_doh:
        return
    if doh_server_running():
        return
    if doh_server_start():
        print(f"{CLR_GREEN}[+] DoH forwarder auto-started (NRPT was referencing 127.0.0.1){CLR_RESET}")
    else:
        print(f"{CLR_RED}[!] NRPT references 127.0.0.1 but DoH forwarder failed to start.{CLR_RESET}")
        print(f"    Google domains will not resolve. Run [3] Remove AI Bypass if this persists.")

# ==============================================================================
# 3.6. SNI PINNING FOR CLOUD CODE (GEOHIDE DNS + TLS PROBE)
# ==============================================================================

HOSTS_FILE = os.path.join(
    os.environ.get("SystemRoot", r"C:\Windows"),
    "System32", "drivers", "etc", "hosts"
)
HOSTS_MARK_BEGIN = "# BEGIN AI-Bypass-CloudCode"
HOSTS_MARK_END   = "# END AI-Bypass-CloudCode"

ROUTES_STATE = os.path.join(DOH_DIR, "cloudcode_routes.json")

def tls_probe(ip: str, sni: str, timeout: float = 3.0) -> bool:
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((ip, 443), timeout=timeout) as raw:
            with ctx.wrap_socket(raw, server_hostname=sni) as tls:
                tls.settimeout(timeout)
                req = (f"HEAD / HTTP/1.1\r\nHost: {sni}\r\n"
                       f"User-Agent: probe\r\nConnection: close\r\n\r\n")
                tls.sendall(req.encode("ascii"))
                data = tls.recv(256)
                if not data.startswith(b"HTTP/"):
                    return False
                try:
                    code = int(data.split(b" ", 2)[1])
                    return code < 500
                except Exception:
                    return True
    except Exception as e:
        _doh_log(f"tls_probe {ip} sni={sni}: {e}")
        return False

def pick_cloudcode_ip(host: str):
    candidates = []
    for ip in query_geohide_dns(host):
        candidates.append(("geohide-dns", ip))
        print(f"  {CLR_GRAY}[i] geohide DNS {host} → {ip}{CLR_RESET}")
    for ip in GEOHIDE_DNS:
        candidates.append(("geohide-frontend", ip))

    for source, ip in candidates:
        if tls_probe(ip, host):
            print(f"  {CLR_GREEN}[+] {host} → {ip} ({source}){CLR_RESET}")
            return ip
    return None

def _read_hosts():
    try:
        with open(HOSTS_FILE, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""

def _strip_hosts_block(text):
    out, inside = [], False
    for line in text.splitlines(keepends=True):
        s = line.strip()
        if s == HOSTS_MARK_BEGIN:
            inside = True
            continue
        if s == HOSTS_MARK_END:
            inside = False
            continue
        if not inside:
            out.append(line)
    return "".join(out)

def _safe_write_hosts(new_text):
    current = _read_hosts()
    if current == new_text:
        return True

    last_err = None

    # Attempt 1: atomic replace via tmp (fast path, no locks during write)
    try:
        tmp = HOSTS_FILE + ".aibypass.tmp"
        try:
            with open(tmp, "w", encoding="utf-8", newline="") as f:
                f.write(new_text)
            os.replace(tmp, HOSTS_FILE)
            _doh_log("hosts: written via atomic replace")
            return True
        finally:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
    except Exception as e:
        last_err = f"atomic replace: {e}"
        _doh_log(f"hosts: atomic replace failed: {e}")

    # Attempt 2: clear read-only and write in place
    try:
        if os.path.exists(HOSTS_FILE):
            try:
                import stat as _stat
                os.chmod(HOSTS_FILE, _stat.S_IWRITE | _stat.S_IREAD)
            except Exception:
                pass
        with open(HOSTS_FILE, "w", encoding="utf-8", newline="") as f:
            f.write(new_text)
        # Verify the write landed
        check = _read_hosts()
        if check == new_text:
            _doh_log("hosts: written in place")
            return True
        last_err = f"in-place verify mismatch (got {len(check)} bytes, expected {len(new_text)})"
        _doh_log(f"hosts: {last_err}")
    except Exception as e:
        last_err = f"in-place: {e}"
        _doh_log(f"hosts: in-place failed: {e}")

    _doh_log(f"hosts: all write attempts failed: {last_err}")
    return False

def write_cloudcode_hosts(pins: dict) -> bool:
    original = _read_hosts()
    stripped = _strip_hosts_block(original).rstrip("\n")
    block_lines = [HOSTS_MARK_BEGIN]
    for host, ip in pins.items():
        block_lines.append(f"{ip} {host}")
    block_lines.append(HOSTS_MARK_END)
    # Append block at end so existing entries (127.0.0.1 localhost etc.) stay first
    combined = stripped + "\n" + "\n".join(block_lines) + "\n"
    return _safe_write_hosts(combined)

def clear_cloudcode_hosts() -> bool:
    original = _read_hosts()
    stripped = _strip_hosts_block(original)
    if stripped == original:
        return True
    return _safe_write_hosts(stripped)

def _default_gateway():
    out = run_powershell(
        "Get-NetRoute -DestinationPrefix '0.0.0.0/0' -AddressFamily IPv4 "
        "-PolicyStore ActiveStore -ErrorAction SilentlyContinue | "
        "Sort-Object RouteMetric | Select-Object -First 1 | "
        "ForEach-Object { \"$($_.InterfaceIndex);$($_.NextHop)\" }"
    )
    if not out or ";" not in out:
        return None
    try:
        idx, gw = out.split(";", 1)
        return int(idx.strip()), gw.strip()
    except Exception:
        return None

def _load_routes_state():
    try:
        with open(ROUTES_STATE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_routes_state(state):
    try:
        os.makedirs(os.path.dirname(ROUTES_STATE), exist_ok=True)
        with open(ROUTES_STATE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass

def add_host_routes(ips) -> bool:
    info = _default_gateway()
    if not info:
        _doh_log("add_host_routes: default gateway not found")
        return False
    iface, gw = info
    state = _load_routes_state()
    ok = True
    for ip in ips:
        existing = run_powershell(
            f"Get-NetRoute -DestinationPrefix '{ip}/32' -AddressFamily IPv4 "
            f"-PolicyStore ActiveStore -ErrorAction SilentlyContinue | "
            f"Select-Object -First 1 -ExpandProperty NextHop"
        ).strip()
        if existing:
            continue
        run_powershell(
            f"New-NetRoute -DestinationPrefix '{ip}/32' -InterfaceIndex {iface} "
            f"-NextHop '{gw}' -RouteMetric 1 -PolicyStore ActiveStore"
        )
        check = run_powershell(
            f"Get-NetRoute -DestinationPrefix '{ip}/32' -AddressFamily IPv4 "
            f"-PolicyStore ActiveStore -ErrorAction SilentlyContinue | "
            f"Select-Object -First 1 -ExpandProperty InterfaceIndex"
        ).strip()
        if check == str(iface):
            state[ip] = {"iface": iface, "gw": gw}
            _doh_log(f"route added: {ip}/32 via {gw} iface {iface}")
        else:
            _doh_log(f"route add failed: {ip}/32 (check='{check}')")
            ok = False
    _save_routes_state(state)
    return ok

def remove_host_routes():
    state = _load_routes_state()
    for ip, meta in state.items():
        run_powershell(
            f"Remove-NetRoute -DestinationPrefix '{ip}/32' -AddressFamily IPv4 "
            f"-InterfaceIndex {meta.get('iface','')} -NextHop '{meta.get('gw','')}' "
            f"-PolicyStore ActiveStore -Confirm:$false -ErrorAction SilentlyContinue"
        )
        _doh_log(f"route removed: {ip}/32")
    try:
        if os.path.exists(ROUTES_STATE):
            os.remove(ROUTES_STATE)
    except Exception:
        pass

# ==============================================================================
# 4. WINDOWS NRPT POLICY MANAGEMENT
# ==============================================================================

def run_powershell(command: str) -> str:
    try:
        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        return proc.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def get_active_nrpt_rules():
    script = """
    Get-DnsClientNrptRule -ErrorAction SilentlyContinue | ForEach-Object {
        [PSCustomObject]@{
            Name = $_.Name
            Comment = $_.Comment
            Namespace = ($_.Namespace -join ';')
            NameServers = ($_.NameServers -join ';')
        }
    } | ConvertTo-Json -Compress
    """
    raw = run_powershell(script)
    if not raw:
        return []
    try:
        data = json.loads(raw)
        rules_list = []
        if isinstance(data, dict):
            rules_list = [data]
        elif isinstance(data, list):
            rules_list = data
        for r in rules_list:
            if not isinstance(r, dict):
                continue
            r["Name"] = str(r.get("Name") or "")
            r["Comment"] = str(r.get("Comment") or "")
            r["Namespace"] = str(r.get("Namespace") or "")
            r["NameServers"] = str(r.get("NameServers") or "")
        return rules_list
    except Exception:
        pass
    return []

def clear_dns_cache():
    run_powershell("Clear-DnsClientCache")

def remove_all_our_nrpt_rules() -> int:
    comments = [COMSS_COMMENT, DOH_COMMENT, COMSS_COMMENT + "-fallback"] + sorted(LEGACY_COMMENTS)
    comments_ps = ", ".join(f"'{c}'" for c in comments)
    script = f"""
    $c = 0
    Get-DnsClientNrptRule -ErrorAction SilentlyContinue | Where-Object {{
        $_.Comment -in @({comments_ps}) -or $_.Comment -like 'AI-Bypass-*'
    }} | ForEach-Object {{
        Remove-DnsClientNrptRule -Name $_.Name -Force -ErrorAction SilentlyContinue
        $c++
    }}
    $c
    """
    out = run_powershell(script).strip()
    try:
        return int(out.splitlines()[-1])
    except Exception:
        return 0

def apply_nrpt_rule(domains, nameserver, comment) -> bool:
    domains_ps = "@(" + ", ".join(f'"{d}"' for d in domains) + ")"
    run_powershell(f'Add-DnsClientNrptRule -Namespace {domains_ps} -Nameserver "{nameserver}" -Comment "{comment}"')
    return True

# ==============================================================================
# 5. PRE-PATCH PROCESS CHECK (SAFE IDE TERMINATION)
# ==============================================================================

IDE_PROCESS_NAMES = [
    "antigravity.exe",
    "code.exe",
    "language_server_windows_x64.exe",
    "language_server_windows_arm64.exe",
    "language_server.exe",
]

def get_running_ide_processes():
    try:
        out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True, errors="replace").stdout
        running = []
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split('","')
            if parts:
                pname = parts[0].strip('"').lower()
                for target in IDE_PROCESS_NAMES:
                    if pname == target.lower() and pname not in running:
                        running.append(pname)
        return running
    except Exception:
        return []

def ensure_ide_closed() -> bool:
    running = get_running_ide_processes()
    if not running:
        return True

    print(f"\n{CLR_YELLOW}[!] Running editor processes detected: {', '.join(running)}{CLR_RESET}")
    print("    (Files must be released to patch binaries and clear cache)")
    ans = input(f"{CLR_WHITE}Close Antigravity / VS Code now? [Y/n]: {CLR_RESET}").strip().lower()

    if ans in ("n", "no"):
        print(f"{CLR_RED}[-] Operation cancelled. Please close editors manually and retry.{CLR_RESET}")
        return False

    print("[*] Terminating processes...", end="", flush=True)
    for pname in running:
        subprocess.run(["taskkill", "/F", "/IM", pname], capture_output=True)
    time.sleep(0.6)
    print(f" {CLR_GREEN}[OK]{CLR_RESET}")
    return True

# ==============================================================================
# 6. GOOGLE ANTIGRAVITY ENGINE (PURE PYTHON MMAP PATCHER)
# ==============================================================================

OPCODE_X64_ORIG_RE = re.compile(rb"\x80\x78\x08\x00\x74[\s\S]\x48\x8b[\s\S]\x24[\s\S]\x48\x89[\s\S]\x60")
OPCODE_X64_PATCHED_RE = re.compile(rb"\xc6\x40\x08\x01\x90\x90\x48\x8b[\s\S]\x24[\s\S]\x48\x89[\s\S]\x60")
OPCODE_X64_FIX = b"\xc6\x40\x08\x01\x90\x90"

OPCODE_ARM64_ORIG_RE = re.compile(rb"\x03\x20\x40\x39[\x03\x23\x43\x63\x83\xa3\xc3\xe3][\s\S]{2}\x36(?:[\s\S]{4}){1,2}\x03\x10\x06\xa9")
OPCODE_ARM64_PATCHED_RE = re.compile(rb"\x23\x00\x80\x52\x03\x20\x00\x39(?:[\s\S]{4}){1,2}\x03\x10\x06\xa9")
OPCODE_ARM64_FIX = b"\x23\x00\x80\x52\x03\x20\x00\x39"

DAILY_ENDPOINT = "https://daily-cloudcode-pa.googleapis.com"
CLOUD_CODE_KEY = "jetski.cloudCodeUrl"

SETTINGS_FOLDERS = ["Antigravity", "Antigravity IDE", "Code"]
SETTINGS_BACKUP_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), "AIBypass", "settings-backup")

def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def find_antigravity_targets():
    local_appdata = os.environ.get("LOCALAPPDATA", "")
    prog_files = os.environ.get("ProgramFiles", "")
    prog_files_x86 = os.environ.get("ProgramFiles(x86)", "")
    userprofile = os.environ.get("USERPROFILE", "")

    roots = [
        os.path.join(local_appdata, "Programs", "Antigravity"),
        os.path.join(local_appdata, "Programs", "antigravity"),
        os.path.join(local_appdata, "Programs", "Antigravity IDE"),
        os.path.join(local_appdata, "agy"),
        os.path.join(prog_files, "Antigravity"),
        os.path.join(prog_files, "Antigravity IDE"),
        os.path.join(prog_files_x86, "Antigravity"),
        os.path.join(prog_files_x86, "Antigravity IDE"),
    ]

    ext_dirs = [
        os.path.join(userprofile, ".vscode", "extensions"),
        os.path.join(userprofile, ".vscodium", "extensions"),
    ]
    for ed in ext_dirs:
        if os.path.isdir(ed):
            try:
                for entry in os.listdir(ed):
                    lower = entry.lower()
                    if "antigravity" in lower or "google.antigravity" in lower:
                        roots.append(os.path.join(ed, entry))
            except Exception:
                pass

    found = []
    bin_names = ["language_server_windows_x64.exe", "language_server_windows_arm64.exe", "language_server.exe"]

    for r in roots:
        if not os.path.isdir(r):
            continue
        for root, dirs, files in os.walk(r):
            for f in files:
                if f.lower() in bin_names:
                    full_p = os.path.join(root, f)
                    if full_p not in found:
                        found.append(full_p)
    return found

def patch_binary(filepath: str) -> str:
    if not os.path.isfile(filepath):
        return "not_found"

    backup_dir = os.path.join(os.path.dirname(filepath), ".ag-backups")
    os.makedirs(backup_dir, exist_ok=True)
    journal_file = os.path.join(backup_dir, "current.json")
    backup_file = os.path.join(backup_dir, "original.bak")

    with open(filepath, "rb") as f:
        data = bytearray(f.read())

    if OPCODE_X64_PATCHED_RE.search(data) or OPCODE_ARM64_PATCHED_RE.search(data):
        return "already_patched"

    match = OPCODE_X64_ORIG_RE.search(data)
    fix_bytes = OPCODE_X64_FIX
    if not match:
        match = OPCODE_ARM64_ORIG_RE.search(data)
        fix_bytes = OPCODE_ARM64_FIX

    if not match:
        return "no_match"

    orig_sha = hashlib.sha256(data).hexdigest()

    if not os.path.exists(backup_file):
        # Первая установка: пишем свежий бэкап
        with open(backup_file, "wb") as bf:
            bf.write(data)
        _doh_log(f"patch {filepath}: fresh backup written, sha={orig_sha[:12]}")
    else:
        # Бэкап есть. Проверяем, совпадает ли он с текущим stock-файлом.
        try:
            with open(backup_file, "rb") as bf:
                existing = bf.read()
            existing_sha = hashlib.sha256(existing).hexdigest()
        except Exception as e:
            _doh_log(f"patch {filepath}: cannot read existing backup: {e}")
            return "backup_unreadable"

        if existing_sha != orig_sha:
            # Апстрим обновил приложение. Архивируем старый бэкап, пишем новый.
            archive = backup_file + f".{existing_sha[:12]}.old"
            try:
                os.replace(backup_file, archive)
                _doh_log(f"patch {filepath}: archived old backup → {archive}")
            except Exception as e:
                _doh_log(f"patch {filepath}: cannot archive old backup: {e}")
                return "backup_archive_failed"
            with open(backup_file, "wb") as bf:
                bf.write(data)
            _doh_log(f"patch {filepath}: fresh backup for new version, sha={orig_sha[:12]}")
        else:
            _doh_log(f"patch {filepath}: backup already matches, reusing")

    start = match.start()
    data[start:start + len(fix_bytes)] = fix_bytes
    mod_sha = hashlib.sha256(data).hexdigest()

    tmp_path = filepath + ".tmp"
    with open(tmp_path, "wb") as tf:
        tf.write(data)
    os.replace(tmp_path, filepath)

    journal_data = {
        "schema": 1,
        "original": orig_sha,
        "modified": mod_sha,
        "profile": "mgr-gate-v1"
    }
    with open(journal_file, "w", encoding="utf-8") as jf:
        json.dump(journal_data, jf, indent=2)

    return "patched"

def rollback_binary(filepath: str) -> str:
    backup_dir = os.path.join(os.path.dirname(filepath), ".ag-backups")
    backup_file = os.path.join(backup_dir, "original.bak")
    journal_file = os.path.join(backup_dir, "current.json")

    if not os.path.isfile(backup_file):
        return "no_backup"

    tmp_path = filepath + ".tmp"
    shutil.copy2(backup_file, tmp_path)
    os.replace(tmp_path, filepath)

    try:
        os.remove(journal_file)
        os.remove(backup_file)
    except Exception:
        pass

    return "restored"

def backup_settings():
    os.makedirs(SETTINGS_BACKUP_DIR, exist_ok=True)
    appdata = os.environ.get("APPDATA", "")
    for f in SETTINGS_FOLDERS:
        sp = os.path.join(appdata, f, "User", "settings.json")
        if os.path.isfile(sp):
            bp = os.path.join(SETTINGS_BACKUP_DIR, f + ".json")
            if not os.path.exists(bp):
                try:
                    shutil.copy2(sp, bp)
                except Exception:
                    pass

def update_antigravity_settings() -> bool:
    appdata = os.environ.get("APPDATA", "")
    changed = False

    for f in SETTINGS_FOLDERS:
        sp = os.path.join(appdata, f, "User", "settings.json")
        if os.path.isfile(sp):
            try:
                with open(sp, "r", encoding="utf-8") as sf:
                    text = sf.read()
                # Match only uncommented occurrences of the key (JSONC safety):
                # a line starting with optional whitespace + // is a comment — skip it.
                key_pattern = rf'(?m)^(?![ \t]*//).*("{re.escape(CLOUD_CODE_KEY)}"\s*:\s*)"[^"]*"'
                if re.search(key_pattern, text):
                    text = re.sub(
                        key_pattern,
                        lambda m: m.group(0)[:m.start(1) - m.start()] + m.group(1) + f'"{DAILY_ENDPOINT}"',
                        text
                    )
                elif CLOUD_CODE_KEY not in text:
                    # Key absent entirely — inject before closing brace
                    text = text.rstrip()
                    if text.endswith("}"):
                        inner = text[:-1].rstrip()
                        comma = "," if inner.strip() != "{" and not inner.endswith(",") else ""
                        text = f'{inner}{comma}\n    "{CLOUD_CODE_KEY}": "{DAILY_ENDPOINT}"\n}}'
                # else: key exists only in comments — leave file untouched
                else:
                    continue
                with open(sp, "w", encoding="utf-8") as sf:
                    sf.write(text)
                changed = True
            except Exception:
                pass
    return changed

def restore_settings():
    appdata = os.environ.get("APPDATA", "")
    for f in SETTINGS_FOLDERS:
        bp = os.path.join(SETTINGS_BACKUP_DIR, f + ".json")
        sp = os.path.join(appdata, f, "User", "settings.json")
        if not os.path.isfile(bp):
            continue
        try:
            with open(bp, "r", encoding="utf-8") as bf:
                original = bf.read()
            m = re.search(rf'"{re.escape(CLOUD_CODE_KEY)}"\s*:\s*"([^"]*)"', original)
            if os.path.isfile(sp):
                with open(sp, "r", encoding="utf-8") as sf:
                    current = sf.read()
                if m:
                    new_text = re.sub(
                        rf'("{re.escape(CLOUD_CODE_KEY)}"\s*:\s*)"[^"]*"',
                        rf'\g<1>"{m.group(1)}"',
                        current
                    )
                else:
                    new_text = re.sub(
                        rf'"{re.escape(CLOUD_CODE_KEY)}"\s*:\s*"[^"]*"\s*,?\s*',
                        "",
                        current
                    )
                    new_text = re.sub(
                        rf',\s*"{re.escape(CLOUD_CODE_KEY)}"\s*:\s*"[^"]*"',
                        "",
                        new_text
                    )
                if new_text != current:
                    with open(sp, "w", encoding="utf-8") as sf:
                        sf.write(new_text)
            try:
                os.remove(bp)
            except Exception:
                pass
        except Exception:
            pass

def clear_v8_caches():
    appdata = os.environ.get("APPDATA", "")
    for t in ["Antigravity", "Antigravity IDE"]:
        cache_dir = os.path.join(appdata, t, "Code Cache")
        if os.path.isdir(cache_dir):
            try:
                shutil.rmtree(cache_dir, ignore_errors=True)
            except Exception:
                pass

def set_antigravity_env():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "CLOUD_CODE_URL", 0, winreg.REG_SZ, DAILY_ENDPOINT)
        winreg.CloseKey(key)
    except Exception:
        pass

def remove_antigravity_env():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
        try:
            winreg.DeleteValue(key, "CLOUD_CODE_URL")
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
    except Exception:
        pass

# ==============================================================================
# 7. UNIFIED AI BYPASS (INSTALL / REMOVE / SWITCH)
# ==============================================================================

def install_ai_bypass():
    print(f"\n{CLR_CYAN}=== INSTALL AI BYPASS ==={CLR_RESET}")
    print("    ChatGPT + Claude → Comss SmartDNS")
    print("    Gemini + Antigravity API → direct substituter NS (or DoH fallback)")
    print("    Antigravity Cloud Code → SNI pin (geohide DNS discovery)")
    print("    Plus: patch language_server, redirect endpoints, clear V8 cache\n")

    if not ensure_ide_closed():
        return

    best_server = find_best_server()

    print(f"\n{CLR_CYAN}[*] Starting DoH forwarder...{CLR_RESET}")
    doh_ok = doh_server_start()
    if doh_ok:
        print(f"  {CLR_GREEN}[+] DoH forwarder running on {DOH_LISTEN}:{DOH_PORT}{CLR_RESET}")
        if install_scheduled_task():
            print(f"  {CLR_GREEN}[+] Autostart registered (Task Scheduler: {TASK_NAME}){CLR_RESET}")
        else:
            print(f"  {CLR_YELLOW}[!] Could not register autostart; DoH will stop after reboot{CLR_RESET}")
    else:
        print(f"  {CLR_RED}[!] DoH forwarder failed. Google domains will fall back to direct NS.{CLR_RESET}")
        print(f"      See {DOH_LOG}")

    print(f"\n{CLR_CYAN}[*] Patching Antigravity binaries...{CLR_RESET}")
    targets = find_antigravity_targets()
    if not targets:
        print(f"  {CLR_YELLOW}[!] No language_server binaries found{CLR_RESET}")
    else:
        for t in targets:
            res = patch_binary(t)
            if res == "patched":
                print(f"  {CLR_GREEN}[+] Patched: {t}{CLR_RESET}")
            elif res == "already_patched":
                print(f"  {CLR_GREEN}[i] Already patched: {t}{CLR_RESET}")
            elif res == "backup_unreadable":
                print(f"  {CLR_RED}[!] Backup unreadable, cannot patch: {t}{CLR_RESET}")
            elif res == "backup_archive_failed":
                print(f"  {CLR_RED}[!] Cannot archive old backup, aborting: {t}{CLR_RESET}")
            else:
                print(f"  {CLR_YELLOW}[–] Not applicable: {t}{CLR_RESET}")

    backup_settings()
    if update_antigravity_settings():
        print(f"  {CLR_GREEN}[+] settings.json: jetski.cloudCodeUrl → daily endpoint{CLR_RESET}")
    set_antigravity_env()
    print(f"  {CLR_GREEN}[+] CLOUD_CODE_URL environment variable set{CLR_RESET}")

    clear_v8_caches()
    print(f"  {CLR_GREEN}[+] V8 Code Cache cleared{CLR_RESET}")

    # ----------------------------------------------------------------------
    # NRPT: exactly two rules
    #   AI-Bypass-SmartDNS → ChatGPT + Claude domains → Comss
    #   AI-Bypass-DoH      → Gemini + Antigravity API domains → substituters
    # ----------------------------------------------------------------------
    print(f"\n{CLR_CYAN}[*] Applying NRPT rules...{CLR_RESET}")
    removed = remove_all_our_nrpt_rules()
    if removed:
        print(f"  {CLR_GRAY}[i] Removed {removed} legacy rule(s){CLR_RESET}")

    comss_domains = _dedup(CHATGPT_DOMAINS + CLAUDE_DOMAINS)
    google_domains = _dedup(GEMINI_DOMAINS + ANTIGRAVITY_DOMAINS)

    apply_nrpt_rule(comss_domains, best_server, COMSS_COMMENT)
    print(f"  {CLR_GREEN}[+] ChatGPT + Claude → {best_server}{CLR_RESET}")

    print(f"\n{CLR_CYAN}[*] Discovering direct substituters for Google AI hosts...{CLR_RESET}")
    test_hosts = ["gemini.google.com", "aistudio.google.com", "generativelanguage.googleapis.com"]
    subs = discover_substituters(test_hosts)
    if subs:
        print(f"  {CLR_GREEN}[+] Substituter NS: {', '.join(subs)}{CLR_RESET}")
        apply_nrpt_rule(google_domains, ";".join(subs), DOH_COMMENT)
        print(f"  {CLR_GREEN}[+] Gemini + Antigravity API → direct NS ({len(subs)} servers){CLR_RESET}")
    elif doh_ok:
        print(f"  {CLR_YELLOW}[i] No direct substituter; using local DoH forwarder{CLR_RESET}")
        apply_nrpt_rule(google_domains, DOH_LISTEN, DOH_COMMENT)
    else:
        print(f"  {CLR_RED}[!] No substituter and no DoH: Google AI hosts will not work{CLR_RESET}")
        apply_nrpt_rule(google_domains, best_server, COMSS_COMMENT + "-fallback")

    # ----------------------------------------------------------------------
    # Cloud Code hosts pin (bypasses NRPT for the IDE's API host)
    # ----------------------------------------------------------------------
    print(f"\n{CLR_CYAN}[*] Pinning Cloud Code API to working IP (geohide DNS discovery)...{CLR_RESET}")
    pins = {}
    for host in CLOUDCODE_HOSTS:
        ip = pick_cloudcode_ip(host)
        if ip:
            pins[host] = ip
        else:
            print(f"  {CLR_YELLOW}[!] No working IP found for {host}{CLR_RESET}")
    if pins:
        if write_cloudcode_hosts(pins):
            print(f"  {CLR_GREEN}[+] hosts entries written ({len(pins)}){CLR_RESET}")
            add_host_routes(set(pins.values()))
            print(f"  {CLR_GREEN}[+] /32 routes through default gateway added{CLR_RESET}")
        else:
            print(f"  {CLR_RED}[!] hosts write failed — /32 routes skipped{CLR_RESET}")
            print(f"      Windows не дал записать C:\\Windows\\System32\\drivers\\etc\\hosts.")
            print(f"      Смотри хвост лога: {DOH_LOG}")
            print(f"      Пока IDE может работать на старом пине, если он был; иначе — переустанови.")
    else:
        print(f"  {CLR_RED}[!] Pinning skipped — Cloud Code API will still be rejected by Google{CLR_RESET}")

    clear_dns_cache()
    print(f"\n{CLR_GREEN}[+] DONE! AI Bypass installed.{CLR_RESET}")
    print(f"    Restart your browser and IDE for changes to fully apply.")

def switch_smartdns_server():
    print(f"\n{CLR_CYAN}=== SWITCH SMARTDNS SERVER ==={CLR_RESET}")
    rules = get_active_nrpt_rules()
    comss_rule = next((r for r in rules if r.get("Comment") == COMSS_COMMENT
                       or (r.get("Comment") or "").startswith(COMSS_COMMENT)), None)
    legacy_comss = [r for r in rules if (r.get("Comment") or "") in LEGACY_COMMENTS
                    and "127.0.0.1" not in (r.get("NameServers") or "")]

    if not comss_rule and not legacy_comss:
        print(f"{CLR_YELLOW}[!] No SmartDNS rule active. Run [1] Install AI Bypass first.{CLR_RESET}")
        return

    best_server = find_best_server()
    print(f"\n{CLR_CYAN}[*] Updating SmartDNS rule...{CLR_RESET}")

    for r in legacy_comss:
        run_powershell(f'Remove-DnsClientNrptRule -Name "{r["Name"]}" -Force -ErrorAction SilentlyContinue')

    if comss_rule:
        run_powershell(f'Remove-DnsClientNrptRule -Name "{comss_rule["Name"]}" -Force -ErrorAction SilentlyContinue')

    comss_domains = _dedup(CHATGPT_DOMAINS + CLAUDE_DOMAINS)
    apply_nrpt_rule(comss_domains, best_server, COMSS_COMMENT)

    fallback_rule = next((r for r in rules if (r.get("Comment") or "") == COMSS_COMMENT + "-fallback"), None)
    if fallback_rule and not doh_server_running():
        run_powershell(f'Remove-DnsClientNrptRule -Name "{fallback_rule["Name"]}" -Force -ErrorAction SilentlyContinue')
        doh_domains = _dedup(GEMINI_DOMAINS + ANTIGRAVITY_DOMAINS)
        apply_nrpt_rule(doh_domains, best_server, COMSS_COMMENT + "-fallback")

    clear_dns_cache()
    print(f"\n{CLR_GREEN}[+] DONE! SmartDNS → {best_server}. DNS cache cleared.{CLR_RESET}")

def remove_ai_bypass():
    print(f"\n{CLR_CYAN}=== REMOVE AI BYPASS (Full Rollback) ==={CLR_RESET}")

    if not ensure_ide_closed():
        return

    print(f"\n{CLR_CYAN}[*] Rolling back Antigravity binaries...{CLR_RESET}")
    targets = find_antigravity_targets()
    restored = 0
    for t in targets:
        res = rollback_binary(t)
        if res == "restored":
            print(f"  {CLR_GREEN}[+] Restored: {t}{CLR_RESET}")
            restored += 1
        elif res == "no_backup":
            print(f"  {CLR_GRAY}[–] No backup: {t}{CLR_RESET}")
    if restored == 0:
        print(f"  {CLR_GRAY}[i] No patched binaries found{CLR_RESET}")

    remove_antigravity_env()
    print(f"  {CLR_GREEN}[+] CLOUD_CODE_URL environment variable removed{CLR_RESET}")

    restore_settings()
    print(f"  {CLR_GREEN}[+] settings.json endpoint restored{CLR_RESET}")

    clear_v8_caches()
    print(f"  {CLR_GREEN}[+] V8 Code Cache cleared{CLR_RESET}")

    print(f"\n{CLR_CYAN}[*] Removing NRPT rules...{CLR_RESET}")
    n = remove_all_our_nrpt_rules()
    print(f"  {CLR_GREEN}[+] Removed {n} NRPT rule(s){CLR_RESET}")

    clear_dns_cache()

    clear_cloudcode_hosts()
    remove_host_routes()
    print(f"  {CLR_GREEN}[+] Cloud Code hosts entries and /32 routes removed{CLR_RESET}")

    uninstall_scheduled_task()
    print(f"  {CLR_GREEN}[+] Autostart task removed{CLR_RESET}")
    if doh_server_running():
        if doh_server_stop():
            print(f"  {CLR_GREEN}[+] DoH forwarder stopped{CLR_RESET}")

    try:
        if os.path.isdir(SETTINGS_BACKUP_DIR):
            shutil.rmtree(SETTINGS_BACKUP_DIR, ignore_errors=True)
    except Exception:
        pass

    try:
        if os.path.isdir(DOH_DIR):
            shutil.rmtree(DOH_DIR, ignore_errors=True)
    except Exception:
        pass

    try:
        appdata_aibypass = os.path.join(os.environ.get("LOCALAPPDATA", ""), "AIBypass")
        if os.path.isdir(appdata_aibypass) and not os.listdir(appdata_aibypass):
            os.rmdir(appdata_aibypass)
    except Exception:
        pass

    print(f"\n{CLR_GREEN}[+] DONE! AI Bypass removed completely.{CLR_RESET}")
    print(f"    Restart your browser and IDE for changes to fully apply.")

# ==============================================================================
# 8. STATUS & DIAGNOSTICS
# ==============================================================================

def _has_comss_rule(rules) -> bool:
    for r in rules:
        c = r.get("Comment") or ""
        if c == COMSS_COMMENT or c == COMSS_COMMENT + "-fallback":
            return True
        if c in LEGACY_COMMENTS and "127.0.0.1" not in (r.get("NameServers") or ""):
            return True
    return False

def _has_doh_rule(rules) -> bool:
    for r in rules:
        c = r.get("Comment") or ""
        if c == DOH_COMMENT:
            return True
        if "127.0.0.1" in (r.get("NameServers") or ""):
            return True
    return False

def _cloudcode_pins_summary() -> str:
    text = _read_hosts()
    inside = False
    count = 0
    for line in text.splitlines():
        s = line.strip()
        if s == HOSTS_MARK_BEGIN:
            inside = True; continue
        if s == HOSTS_MARK_END:
            inside = False; continue
        if inside and s:
            count += 1
    if count == 0:
        return "off"
    return f"on ({count} host{'s' if count != 1 else ''})"

def print_status():
    rules = get_active_nrpt_rules()
    comss_on = _has_comss_rule(rules)
    doh_on = _has_doh_rule(rules)

    print(f"{CLR_GRAY}------------------- CURRENT STATUS -------------------{CLR_RESET}")

    if doh_server_running():
        task = "autostart: on" if scheduled_task_exists() else "autostart: off"
        print(f"  DoH forwarder:     {CLR_GREEN}running (127.0.0.1:53){CLR_RESET}  [{task}]")
    else:
        print(f"  DoH forwarder:     {CLR_GRAY}stopped{CLR_RESET}")

    pins = _cloudcode_pins_summary()
    if pins == "off":
        print(f"  Cloud Code pin:    {CLR_GRAY}off{CLR_RESET}")
    else:
        print(f"  Cloud Code pin:    {CLR_GREEN}{pins}{CLR_RESET}")

    if comss_on:
        servers = set()
        for r in rules:
            c = r.get("Comment") or ""
            if c == COMSS_COMMENT or c == COMSS_COMMENT + "-fallback" or c in LEGACY_COMMENTS:
                for ns in (r.get("NameServers") or "").split(";"):
                    ns = ns.strip()
                    if ns and ns != "127.0.0.1":
                        servers.add(ns)
        srv = ", ".join(servers) if servers else "Comss SmartDNS"
        print(f"  ChatGPT + Claude:  {CLR_GREEN}[ON] → {srv}{CLR_RESET}")
    else:
        print(f"  ChatGPT + Claude:  {CLR_GRAY}[OFF]{CLR_RESET}")

    # Gemini + Antigravity API: check where the NRPT rule actually points
    if doh_on:
        ns = next((r.get("NameServers") or "" for r in rules if r.get("Comment") == DOH_COMMENT), "")
        if "127.0.0.1" in ns:
            if doh_server_running():
                print(f"  Gemini + Antigrav: {CLR_GREEN}[ON] → DoH forwarder{CLR_RESET}")
            else:
                print(f"  Gemini + Antigrav: {CLR_RED}[BROKEN] → DoH forwarder is down!{CLR_RESET}")
        else:
            srv_list = [x for x in ns.split(";") if x]
            shown = ", ".join(srv_list[:2]) + (" ..." if len(srv_list) > 2 else "")
            print(f"  Gemini + Antigrav: {CLR_GREEN}[ON] → direct NS: {shown}{CLR_RESET}")
    elif comss_on:
        print(f"  Gemini + Antigrav: {CLR_YELLOW}[PARTIAL] via Comss fallback{CLR_RESET}")
    else:
        print(f"  Gemini + Antigrav: {CLR_GRAY}[OFF]{CLR_RESET}")

    if pins != "off" and comss_on:
        print(f"  Antigravity IDE:   {CLR_GREEN}[ON] → SNI pin + patch{CLR_RESET}")
    elif comss_on:
        print(f"  Antigravity IDE:   {CLR_YELLOW}[PARTIAL] patch applied, no pin{CLR_RESET}")
    else:
        print(f"  Antigravity IDE:   {CLR_GRAY}[OFF]{CLR_RESET}")

    print(f"{CLR_GRAY}------------------------------------------------------{CLR_RESET}\n")

def show_details():
    print(f"\n{CLR_CYAN}=== DETAILS ==={CLR_RESET}\n")

    print(f"{CLR_WHITE}Antigravity binaries:{CLR_RESET}")
    targets = find_antigravity_targets()
    if not targets:
        print(f"  {CLR_GRAY}none found{CLR_RESET}")
    for t in targets:
        state = "unknown"
        color = CLR_YELLOW
        try:
            with open(t, "rb") as f:
                content = f.read()
                if OPCODE_X64_PATCHED_RE.search(content) or OPCODE_ARM64_PATCHED_RE.search(content):
                    state = "patched"
                    color = CLR_GREEN
                elif OPCODE_X64_ORIG_RE.search(content) or OPCODE_ARM64_ORIG_RE.search(content):
                    state = "stock"
                    color = CLR_GRAY
                else:
                    state = "unrecognized"
        except Exception:
            state = "read error"
            color = CLR_RED
        print(f"  {color}[{state}]{CLR_RESET} {t}")

    print(f"\n{CLR_WHITE}DoH forwarder:{CLR_RESET}")
    if doh_server_running():
        print(f"  {CLR_GREEN}running{CLR_RESET} on 127.0.0.1:53")
    else:
        print(f"  {CLR_GRAY}stopped{CLR_RESET}")
    print(f"  autostart task:   {'registered' if scheduled_task_exists() else 'not registered'}")
    print(f"  log file:         {DOH_LOG}")

    print(f"\n{CLR_WHITE}NRPT rules:{CLR_RESET}")
    rules = get_active_nrpt_rules()
    our = [r for r in rules if (r.get("Comment") or "") in ({COMSS_COMMENT, DOH_COMMENT, COMSS_COMMENT + "-fallback"} | LEGACY_COMMENTS)]
    if not our:
        print(f"  {CLR_GRAY}none{CLR_RESET}")
    for r in our:
        ns = r.get("NameServers") or ""
        ns_count = len([x for x in ns.split(";") if x.strip()])
        print(f"  {CLR_GREEN}•{CLR_RESET} [{r.get('Comment')}] → {ns} ({ns_count} ns)")

    print(f"\n{CLR_WHITE}Cloud Code hosts pins:{CLR_RESET}")
    hosts_text = _read_hosts()
    inside = False
    found_pins = False
    for line in hosts_text.splitlines():
        s = line.strip()
        if s == HOSTS_MARK_BEGIN:
            inside = True; continue
        if s == HOSTS_MARK_END:
            inside = False; continue
        if inside and s:
            print(f"  {CLR_GREEN}•{CLR_RESET} {s}")
            found_pins = True
    if not found_pins:
        print(f"  {CLR_GRAY}none{CLR_RESET}")

    print(f"\n{CLR_WHITE}Cloud Code /32 routes:{CLR_RESET}")
    rstate = _load_routes_state()
    if not rstate:
        print(f"  {CLR_GRAY}none{CLR_RESET}")
    for ip, meta in rstate.items():
        print(f"  {CLR_GREEN}•{CLR_RESET} {ip}/32 via {meta.get('gw')} iface {meta.get('iface')}")

    print(f"\n{CLR_WHITE}Cloud Code geohide discovery (live):{CLR_RESET}")
    for host in CLOUDCODE_HOSTS:
        ips = query_geohide_dns(host, timeout=1.5)
        if ips:
            print(f"  {CLR_GREEN}•{CLR_RESET} {host}: {', '.join(ips)}")
        else:
            print(f"  {CLR_GRAY}•{CLR_RESET} {host}: no non-Google A records")

    print(f"\n{CLR_WHITE}Gemini substituter (live):{CLR_RESET}")
    for srv in GEOHIDE_DNS + UPSTREAM_SERVERS:
        try:
            q = build_dns_query("gemini.google.com", tid=0x5A00)
            resp = _query_udp_single(q, srv, 3.0)
            if resp:
                addrs = parse_a_records(resp)
                nongoogle = [a for a in addrs if not looks_google(a)]
                if nongoogle:
                    print(f"  {CLR_GREEN}•{CLR_RESET} {srv} → {', '.join(nongoogle)}  (substituted)")
                else:
                    print(f"  {CLR_GRAY}•{CLR_RESET} {srv} → {', '.join(addrs) or 'empty'}  (real Google)")
            else:
                print(f"  {CLR_YELLOW}•{CLR_RESET} {srv} → no response")
        except Exception as e:
            print(f"  {CLR_RED}•{CLR_RESET} {srv} → {e}")

    print(f"\n{CLR_WHITE}DoH endpoints (live probe):{CLR_RESET}")
    probe_query = build_dns_query("gemini.google.com", tid=0x1234)
    for ep in DOH_ENDPOINTS:
        try:
            resp = _try_doh_endpoint(ep, probe_query, timeout=3.0)
            addrs = parse_a_records(resp)
            mark = CLR_GREEN + "OK" + CLR_RESET
            print(f"  {mark}  {ep}  → {', '.join(addrs) or 'no A records'}")
        except Exception as e:
            print(f"  {CLR_RED}ERR{CLR_RESET} {ep}  → {e}")

    print(f"\n{CLR_WHITE}DoH log tail:{CLR_RESET}")
    if os.path.isfile(DOH_LOG):
        try:
            with open(DOH_LOG, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()[-15:]
            for line in lines:
                print(f"  {CLR_GRAY}{line.rstrip()}{CLR_RESET}")
        except Exception:
            print(f"  {CLR_RED}cannot read{CLR_RESET}")
    else:
        print(f"  {CLR_GRAY}no log yet{CLR_RESET}")

# ==============================================================================
# 9. MAIN MENU
# ==============================================================================

def main_menu():
    ensure_forwarder_if_needed()
    while True:
        os.system("cls" if CURRENT_OS == "Windows" else "clear")
        print(f"{CLR_CYAN}==============================================================={CLR_RESET}")
        print(f"{CLR_CYAN}         AI-BYPASS MANAGER v1.1.0 (Pure Python Edition)        {CLR_RESET}")
        print(f"{CLR_CYAN}==============================================================={CLR_RESET}")
        print(" Unified bypass for ChatGPT, Claude, Gemini & Google Antigravity\n")

        print_status()

        print(f"{CLR_WHITE}ACTION MENU:{CLR_RESET}")
        print(f"  {CLR_GREEN}[1] Install AI Bypass{CLR_RESET}    (browsers + Antigravity, one shot)")
        print(f"  {CLR_YELLOW}[2] Switch SmartDNS{CLR_RESET}       (re-probe Comss server)")
        print(f"  {CLR_RED}[3] Remove AI Bypass{CLR_RESET}     (full rollback, single button)")
        print(f"  {CLR_CYAN}[4] Details{CLR_RESET}              (binaries, rules, pins, DoH log)")
        print(f"  {CLR_GRAY}[0] Exit{CLR_RESET}\n")

        action = input(f"{CLR_WHITE}Select action [0-4]: {CLR_RESET}").strip()

        if action == "1":
            install_ai_bypass()
        elif action == "2":
            switch_smartdns_server()
        elif action == "3":
            remove_ai_bypass()
        elif action == "4":
            show_details()
        elif action == "0":
            print(f"\n{CLR_CYAN}Goodbye!{CLR_RESET}\n")
            break
        else:
            print(f"\n{CLR_RED}Invalid choice. Select 0, 1, 2, 3, or 4.{CLR_RESET}")
            time.sleep(0.8)
            continue

        input(f"\n{CLR_GRAY}Press Enter to return to menu...{CLR_RESET}")

# ==============================================================================
# 10. PLATFORM ROUTER & ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    try:
        if "--doh-server" in sys.argv:
            sys.exit(doh_server_main())
        if CURRENT_OS == "Windows":
            ensure_admin()
            main_menu()
        else:
            print(f"{CLR_CYAN}==============================================================={CLR_RESET}")
            print(f"{CLR_CYAN}         AI-BYPASS MANAGER v1.1.0 ({CURRENT_OS})              {CLR_RESET}")
            print(f"{CLR_CYAN}==============================================================={CLR_RESET}\n")
            print(f"{CLR_YELLOW}[i] Native support for {CURRENT_OS} is planned for future releases.{CLR_RESET}")
            print("    - For macOS & Linux, see: https://github.com/vezlin1/antigravity-bypass-russia\n")
            sys.exit(0)
    except KeyboardInterrupt:
        print(f"\n{CLR_CYAN}\nSession finished by user.{CLR_RESET}")
        sys.exit(0)
    except Exception as e:
        import traceback
        print(f"\n{CLR_RED}[!] An unexpected error occurred:{CLR_RESET}\n")
        traceback.print_exc()
        print(f"\n{CLR_YELLOW}Please take a screenshot of this error for debugging.{CLR_RESET}")
        input(f"\n{CLR_GRAY}Press Enter to exit...{CLR_RESET}")
        sys.exit(1)