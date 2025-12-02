"""Anvil process management."""

import os
import re
import subprocess
import signal
import sys
import time
from dataclasses import dataclass
from typing import Optional

from rich.console import Console

console = Console()


@dataclass
class AnvilInstance:
    """Represents a running Anvil instance."""
    
    process: subprocess.Popen
    private_key: str
    address: str
    rpc_url: str = "http://127.0.0.1:8545"


class AnvilManager:
    """Manages the Anvil local Ethereum node."""
    
    def __init__(self):
        self.instance: Optional[AnvilInstance] = None
    
    def start(self, port: int = 8545) -> AnvilInstance:
        """Start Anvil and capture the first private key."""
        
        # Check if anvil is installed
        try:
            subprocess.run(
                ["anvil", "--version"],
                capture_output=True,
                check=True
            )
        except FileNotFoundError:
            console.print(
                "[bold red]Error:[/] Anvil not found. "
                "Please install Foundry: https://getfoundry.sh"
            )
            sys.exit(1)
        
        console.print(f"[cyan]Starting Anvil on port {port}...[/]")
        
        # Start anvil process
        process = subprocess.Popen(
            ["anvil", "--port", str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        
        private_key = None
        address = None
        
        # Read output until we find the private keys
        output_lines = []
        start_time = time.time()
        timeout = 10  # seconds
        
        while time.time() - start_time < timeout:
            if process.stdout is None:
                break
                
            line = process.stdout.readline()
            if not line:
                break
            
            output_lines.append(line)
            
            # Look for first private key (format: (0) 0x...)
            if private_key is None:
                pk_match = re.search(r"\(0\)\s+(0x[a-fA-F0-9]{64})", line)
                if pk_match:
                    private_key = pk_match.group(1)
            
            # Look for first address
            if address is None:
                addr_match = re.search(r"\(0\)\s+(0x[a-fA-F0-9]{40})\s+\(", line)
                if addr_match:
                    address = addr_match.group(1)
            
            # Stop when we see "Listening on"
            if "Listening on" in line:
                break
        
        if private_key is None:
            console.print("[bold red]Error:[/] Could not capture private key from Anvil")
            process.terminate()
            sys.exit(1)
        
        if address is None:
            address = "unknown"
        
        rpc_url = f"http://127.0.0.1:{port}"
        
        self.instance = AnvilInstance(
            process=process,
            private_key=private_key,
            address=address,
            rpc_url=rpc_url,
        )
        
        # Set environment variables
        os.environ["PRIVATE_KEY"] = private_key
        os.environ["ETH_RPC_URL"] = rpc_url
        os.environ["DEPLOYER_ADDRESS"] = address
        
        return self.instance
    
    def stop(self):
        """Stop the Anvil process."""
        if self.instance and self.instance.process:
            self.instance.process.terminate()
            try:
                self.instance.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.instance.process.kill()
            console.print("[yellow]Anvil stopped.[/]")
            self.instance = None
    
    def is_running(self) -> bool:
        """Check if Anvil is running."""
        if self.instance is None:
            return False
        return self.instance.process.poll() is None


# Global manager instance
anvil_manager = AnvilManager()


def cleanup_handler(signum, frame):
    """Handle cleanup on exit."""
    anvil_manager.stop()
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, cleanup_handler)
signal.signal(signal.SIGTERM, cleanup_handler)

