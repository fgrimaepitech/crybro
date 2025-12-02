"""CryBro CLI - Main entry point."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

from crybro.anvil import anvil_manager

app = typer.Typer(
    name="crybro",
    help="🔗 A CLI for local crypto development with Anvil",
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()

# Script extensions to look for
SCRIPT_EXTENSIONS = {".py", ".js", ".ts", ".sh", ".sol"}


def get_scripts(directory: Path = Path.cwd(), recursive: bool = True) -> list[Path]:
    """Get all script files in the given directory (and subdirectories if recursive)."""
    scripts = []
    pattern = "**/*" if recursive else "*"
    for ext in SCRIPT_EXTENSIONS:
        scripts.extend(directory.glob(f"{pattern}{ext}"))
    # Sort by path, putting root-level scripts first
    return sorted(scripts, key=lambda p: (len(p.parts), p))


def display_banner():
    """Display the CryBro banner."""
    banner = """
   ██████╗██████╗ ██╗   ██╗██████╗ ██████╗  ██████╗ 
  ██╔════╝██╔══██╗╚██╗ ██╔╝██╔══██╗██╔══██╗██╔═══██╗
  ██║     ██████╔╝ ╚████╔╝ ██████╔╝██████╔╝██║   ██║
  ██║     ██╔══██╗  ╚██╔╝  ██╔══██╗██╔══██╗██║   ██║
  ╚██████╗██║  ██║   ██║   ██████╔╝██║  ██║╚██████╔╝
   ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ 
    """
    console.print(banner, style="bold cyan")


def display_env_info(private_key: str, address: str, rpc_url: str):
    """Display environment information."""
    # Truncate private key for display
    pk_display = f"{private_key[:10]}...{private_key[-8:]}"
    
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="bold yellow")
    table.add_column("Value", style="green")
    
    table.add_row("PRIVATE_KEY", pk_display)
    table.add_row("DEPLOYER_ADDRESS", address)
    table.add_row("ETH_RPC_URL", rpc_url)
    
    console.print(Panel(table, title="[bold]Environment Variables", border_style="cyan"))


@app.command()
def start(
    port: int = typer.Option(8545, "--port", "-p", help="Port to run Anvil on"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", "-i/-I", help="Run in interactive mode"),
):
    # Handle default values when called programmatically
    if not isinstance(port, int):
        port = 8545
    if not isinstance(interactive, bool):
        interactive = True
    """
    🚀 Start Anvil and enter interactive mode.
    
    Launches a local Ethereum node and captures the first private key.
    """
    display_banner()
    
    # Start Anvil
    instance = anvil_manager.start(port=port)
    
    console.print()
    console.print("[bold green]✓ Anvil started successfully![/]")
    console.print()
    
    display_env_info(instance.private_key, instance.address, instance.rpc_url)
    
    if interactive:
        console.print()
        console.print("[bold]Available commands:[/]")
        console.print("  [cyan]list[/] or [cyan]ls[/]        - List available scripts")
        console.print("  [cyan]run <script>[/]     - Run a script")
        console.print("  [cyan]env[/]              - Show environment variables")
        console.print("  [cyan]env add NAME=VAL[/] - Add an environment variable")
        console.print("  [cyan]exit[/] or [cyan]quit[/]    - Stop Anvil and exit")
        console.print()
        
        interactive_loop()
    else:
        # Just keep running until interrupted
        console.print("[dim]Press Ctrl+C to stop Anvil[/]")
        try:
            instance.process.wait()
        except KeyboardInterrupt:
            anvil_manager.stop()


def interactive_loop():
    """Run the interactive command loop."""
    while True:
        try:
            console.print()
            cmd = console.input("[bold cyan]crybro>[/] ").strip()
            
            if not cmd:
                continue
            
            parts = cmd.split(maxsplit=1)
            command = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            if command in ("exit", "quit", "q"):
                anvil_manager.stop()
                console.print("[bold green]Goodbye! 👋[/]")
                break
            
            elif command in ("list", "ls"):
                list_scripts_cmd()
            
            elif command == "run":
                if args:
                    run_script_cmd(args)
                else:
                    console.print("[yellow]Usage: run <script_name>[/]")
            
            elif command == "env":
                if args.startswith("add "):
                    # env add NAME=VALUE
                    env_arg = args[4:].strip()
                    if "=" in env_arg:
                        name, value = env_arg.split("=", 1)
                        name = name.strip()
                        value = value.strip()
                        os.environ[name] = value
                        console.print(f"[green]✓[/] Set [bold]{name}[/] = [cyan]{value}[/]")
                    else:
                        console.print("[yellow]Usage: env add NAME=VALUE[/]")
                elif args:
                    console.print("[yellow]Unknown env command. Use 'env' to show or 'env add NAME=VALUE' to add.[/]")
                elif anvil_manager.instance:
                    display_env_info(
                        anvil_manager.instance.private_key,
                        anvil_manager.instance.address,
                        anvil_manager.instance.rpc_url,
                    )
            
            elif command == "help":
                console.print("[bold]Commands:[/]")
                console.print("  [cyan]list[/] or [cyan]ls[/]        - List available scripts")
                console.print("  [cyan]run <script>[/]     - Run a script")
                console.print("  [cyan]env[/]              - Show environment variables")
                console.print("  [cyan]env add NAME=VAL[/] - Add an environment variable")
                console.print("  [cyan]exit[/] or [cyan]quit[/]    - Stop Anvil and exit")
            
            else:
                console.print(f"[yellow]Unknown command: {command}. Type 'help' for available commands.[/]")
        
        except KeyboardInterrupt:
            console.print()
            anvil_manager.stop()
            console.print("[bold green]Goodbye! 👋[/]")
            break
        except EOFError:
            anvil_manager.stop()
            break


def list_scripts_cmd():
    """List all scripts in the current directory and subdirectories."""
    scripts = get_scripts()
    cwd = Path.cwd()
    
    if not scripts:
        console.print("[yellow]No scripts found in current directory or subdirectories.[/]")
        console.print(f"[dim]Looking for: {', '.join(SCRIPT_EXTENSIONS)}[/]")
        return
    
    table = Table(title="Available Scripts", show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Script", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("Size", style="dim")
    
    for idx, script in enumerate(scripts, 1):
        ext = script.suffix
        size = script.stat().st_size
        size_str = f"{size:,} B" if size < 1024 else f"{size/1024:.1f} KB"
        # Show relative path from cwd
        try:
            rel_path = script.relative_to(cwd)
        except ValueError:
            rel_path = script
        table.add_row(str(idx), str(rel_path), ext, size_str)
    
    console.print(table)


def run_script_cmd(script_name: str):
    """Run a script by name or number."""
    scripts = get_scripts()
    script_path: Optional[Path] = None
    cwd = Path.cwd()
    
    # Try to find by number
    if script_name.isdigit():
        idx = int(script_name) - 1
        if 0 <= idx < len(scripts):
            script_path = scripts[idx]
    
    # Try to find by relative path or name
    if script_path is None:
        for s in scripts:
            try:
                rel_path = s.relative_to(cwd)
            except ValueError:
                rel_path = s
            # Match by full relative path, name only, or stem
            if str(rel_path) == script_name or s.name == script_name or s.stem == script_name:
                script_path = s
                break
    
    # Try direct path
    if script_path is None:
        direct_path = Path(script_name)
        if direct_path.exists():
            script_path = direct_path
    
    if script_path is None:
        console.print(f"[red]Script not found: {script_name}[/]")
        return
    
    console.print(f"[cyan]Running:[/] {script_path.name}")
    console.print("─" * 50)
    
    # Determine how to run the script
    ext = script_path.suffix
    
    try:
        if ext == ".py":
            subprocess.run([sys.executable, str(script_path)], check=False)
        elif ext == ".js":
            subprocess.run(["node", str(script_path)], check=False)
        elif ext == ".ts":
            # Try ts-node, then tsx, then npx ts-node
            for cmd in [["ts-node", str(script_path)], ["tsx", str(script_path)], ["npx", "ts-node", str(script_path)]]:
                try:
                    subprocess.run(cmd, check=False)
                    break
                except FileNotFoundError:
                    continue
        elif ext == ".sh":
            subprocess.run(["bash", str(script_path)], check=False)
        elif ext == ".sol":
            # Run with forge script, using the captured private key and RPC
            forge_cmd = [
                "forge", "script", str(script_path),
                "--rpc-url", os.environ.get("ETH_RPC_URL", "http://127.0.0.1:8545"),
                "--private-key", os.environ.get("PRIVATE_KEY", ""),
                "--broadcast",
            ]
            subprocess.run(forge_cmd, check=False)
        else:
            subprocess.run([str(script_path)], check=False)
    except FileNotFoundError as e:
        console.print(f"[red]Error running script: {e}[/]")
    
    console.print("─" * 50)
    console.print("[dim]Script finished.[/]")


@app.command("list")
def list_cmd():
    """📋 List all script files in the current directory."""
    list_scripts_cmd()


@app.command("run")
def run_cmd(
    script: str = typer.Argument(..., help="Script name, number, or path to run"),
):
    """▶️  Run a script file."""
    run_script_cmd(script)


@app.command("env")
def env_cmd():
    """🔐 Show current environment variables."""
    pk = os.environ.get("PRIVATE_KEY", "Not set")
    addr = os.environ.get("DEPLOYER_ADDRESS", "Not set")
    rpc = os.environ.get("ETH_RPC_URL", "Not set")
    
    if pk == "Not set":
        console.print("[yellow]Anvil not running. Use 'crybro start' first.[/]")
    else:
        display_env_info(pk, addr, rpc)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """
    🔗 CryBro - Local crypto development CLI
    
    Start Anvil, capture private keys, and run your scripts.
    """
    # If no command provided, run start
    if ctx.invoked_subcommand is None:
        start()


if __name__ == "__main__":
    app()

