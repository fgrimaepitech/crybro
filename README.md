<div align="center">

```
   ██████╗██████╗ ██╗   ██╗██████╗ ██████╗  ██████╗ 
  ██╔════╝██╔══██╗╚██╗ ██╔╝██╔══██╗██╔══██╗██╔═══██╗
  ██║     ██████╔╝ ╚████╔╝ ██████╔╝██████╔╝██║   ██║
  ██║     ██╔══██╗  ╚██╔╝  ██╔══██╗██╔══██╗██║   ██║
  ╚██████╗██║  ██║   ██║   ██████╔╝██║  ██║╚██████╔╝
   ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ 
```

**A CLI for local crypto development with Anvil**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

## Features

- 🚀 **Auto-start Anvil** - Launches a local Ethereum node automatically
- 🔐 **Private Key Capture** - Captures the first private key and sets it as an environment variable
- 📋 **Script Discovery** - Lists all scripts in your current directory
- ▶️ **Script Runner** - Run your scripts with the captured environment

## Prerequisites

- Python 3.10+
- [Foundry](https://getfoundry.sh) (for Anvil)

Install Foundry:
```bash
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

## Installation

```bash
cd crybro-cli
pip install -e .
```

## Usage

### Start Interactive Mode (default)

```bash
crybro
```

This will:
1. Start Anvil on port 8545
2. Capture the first private key
3. Set environment variables (`PRIVATE_KEY`, `ETH_RPC_URL`, `DEPLOYER_ADDRESS`)
4. Enter interactive mode

### Interactive Commands

Once in interactive mode:

| Command | Description |
|---------|-------------|
| `list` or `ls` | List all scripts (including subdirectories) |
| `run <script>` | Run a script by name, number, or path |
| `env` | Show current environment variables |
| `env add NAME=VALUE` | Add a new environment variable |
| `help` | Show available commands |
| `exit` or `quit` | Stop Anvil and exit |

### CLI Commands (non-interactive)

```bash
# Start with custom port
crybro start --port 8546

# List scripts without starting Anvil
crybro list

# Show environment
crybro env
```

### Environment Variables

When Anvil starts, these environment variables are set:

| Variable | Description |
|----------|-------------|
| `PRIVATE_KEY` | First private key from Anvil |
| `ETH_RPC_URL` | RPC URL (http://127.0.0.1:8545) |
| `DEPLOYER_ADDRESS` | Address of the first account |

### Supported Script Types

- `.py` - Python scripts
- `.js` - JavaScript (Node.js)
- `.ts` - TypeScript (ts-node/tsx)
- `.sh` - Shell scripts
- `.sol` - Solidity (runs with `forge script --broadcast`)

## Example Workflow

```bash
# Navigate to your project
cd my-crypto-project

# Start CryBro
crybro

# In interactive mode:
crybro> ls
# Shows scripts from current dir and subdirs:
#   1  deploy.py
#   2  scripts/Deploy.s.sol
#   3  scripts/Token.s.sol

crybro> env add ETHERSCAN_API_KEY=abc123
# ✓ Set ETHERSCAN_API_KEY = abc123

crybro> run 2
# Runs: forge script scripts/Deploy.s.sol --rpc-url ... --private-key ... --broadcast

crybro> exit
# Stops Anvil and exits
```

## License

MIT