#!/usr/bin/env python3
"""Check if .com domains are available for registration."""

from __future__ import annotations
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, List, Dict

# Indicators that a domain is available (not registered)
AVAILABLE_INDICATORS = [
    "No match for",
    "NOT FOUND",
    "No Data Found",
    "Domain not found",
    "is available",
    "Status: free",
    "No entries found",
    "DOMAIN NOT FOUND",
]

# Quick check via DNS first (faster, but less accurate)
def dns_available(domain: str) -> Optional[bool]:
    """Quick DNS check - returns None if uncertain, True if likely available."""
    try:
        result = subprocess.run(
            ["nslookup", domain],
            capture_output=True,
            text=True,
            timeout=5
        )
        # If NXDOMAIN or no answer, might be available
        if "NXDOMAIN" in result.stdout or "can't find" in result.stdout.lower():
            return True
        return None  # DNS exists, but still check whois
    except:
        return None


def whois_available(domain: str) -> bool:
    """Check domain availability via whois. Returns True if available."""
    try:
        result = subprocess.run(
            ["whois", domain],
            capture_output=True,
            text=True,
            timeout=15
        )
        output = result.stdout + result.stderr
        
        for indicator in AVAILABLE_INDICATORS:
            if indicator.lower() in output.lower():
                return True
        
        return False
    except subprocess.TimeoutExpired:
        return False
    except:
        return False


def check_domain(domain: str, quick: bool = False) -> dict:
    """Check a single domain. Returns dict with domain and availability status."""
    domain = domain.lower().strip()
    if not domain.endswith(".com"):
        domain += ".com"
    
    if quick:
        # DNS-only check (fast but may have false positives)
        dns_result = dns_available(domain)
        if dns_result is True:
            return {"domain": domain, "available": True, "method": "dns"}
    
    # Full whois check
    available = whois_available(domain)
    return {"domain": domain, "available": available, "method": "whois"}


def check_domains(domains: List[str], quick: bool = False, max_workers: int = 5) -> List[Dict]:
    """Check multiple domains in parallel."""
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(check_domain, d, quick): d for d in domains}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as e:
                domain = futures[future]
                results.append({"domain": domain, "available": False, "error": str(e)})
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check .com domain availability")
    parser.add_argument("domains", nargs="+", help="Domain names to check (with or without .com)")
    parser.add_argument("--quick", action="store_true", help="Quick DNS-only check (faster but less accurate)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    results = check_domains(args.domains, quick=args.quick)
    
    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            status = "✅ AVAILABLE" if r["available"] else "❌ TAKEN"
            print(f"{r['domain']}: {status}")
