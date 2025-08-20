# VulnBot: Autonomous Penetration Testing for a Multi-Agent Collaborative Framework

<p align="center">
  <a href=''><img src='https://img.shields.io/badge/license-MIT-000000.svg'></a> 
  <a href='https://arxiv.org/abs/2501.13411'><img src='https://img.shields.io/badge/arXiv-2501.13411-<color>.svg'></a> 
</p>

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Citation](#citation)
- [Contact](#contact)

---

## Overview

**Note:**
- ⭐ **If you find this project useful, please consider giving it a <font color='orange'>STAR</font>!** ⭐
- If you encounter any <font color='red'>errors</font> or <font color='red'>issues</font>, feel free to open an issue or submit a pull request.

VulnBot is an advanced automated penetration testing framework that utilizes Large Language Models (LLMs) to replicate the workflow of human penetration testing teams within a multi-agent system. This innovative approach enhances efficiency, collaboration, and adaptability in security assessments.

![VulnBot Framework](images/model.png)

*This RAG implementation is based on [Langchain-Chatchat](https://github.com/chatchat-space/Langchain-Chatchat). Special thanks to the authors.*

---

## Quick Start

### 🎉 New: Simplified Configuration System

VulnBot now uses a **single `config.yaml` file** instead of multiple configuration files, making setup and management much easier!

### Prerequisites

Ensure your environment meets the following requirements before proceeding:

- **Programming Language:** Python 3.11.11
- **Package Manager:** Pip

### Installation

Install VulnBot using one of the following methods:

#### Build from Source

1. Clone the VulnBot repository:

   ```sh
   git clone https://github.com/KHenryAegis/VulnBot
   ```

2. Navigate to the project directory:

   ```sh
   cd VulnBot
   ```

3. Install the dependencies:

   ```sh
   pip install -r requirements.txt
   ```

### Configuration Guide

VulnBot uses a **single configuration file** (`config.yaml`) for all settings. This simplified approach makes configuration management much easier.

#### Sample Configuration

Create a `config.yaml` file in the project root with the following structure:

```yaml
# VulnBot Configuration - All settings in one file

# Basic Settings
basic:
  log_verbose: true
  log_path: logs
  mode: auto  # auto, manual, semi
  http_default_timeout: 300
  
  # Feature toggles
  enable_rag: false
  enable_knowledge_base: false
  enable_tavily_search: true
  
  # Paths
  kb_root_path: data/knowledge_base
  
  # Network settings
  default_bind_host: 0.0.0.0
  
  # Kali Linux connection
  kali:
    hostname: 10.0.0.150
    port: 22
    username: root
    password: root
  
  # API Server
  api_server:
    host: 0.0.0.0
    port: 7861
    public_host: 127.0.0.1
    public_port: 7861
  
  # WebUI Server  
  webui_server:
    host: 0.0.0.0
    port: 8501

# Database Configuration
database:
  mysql:
    host: localhost
    port: 3306
    user: root
    password: 'your_mysql_password'
    database: vulnbot_db
    socket: /tmp/mysql.sock  # Optional: Unix socket for local connections
    charset: utf8mb4
    connect_timeout: 30
    pool_size: 10
    max_overflow: 20

# Knowledge Base Configuration (for RAG)
knowledge_base:
  default_vs_type: milvus
  kb_name: vulnbot_knowledge
  chunk_size: 750
  overlap_size: 150
  top_n: 1
  top_k: 3
  score_threshold: 0.5
  
  # Milvus settings
  milvus:
    uri: http://localhost:19530
    user: ''
    password: ''

# LLM Model Configuration
llm:
  api_key: 'your_openai_api_key'
  llm_model: openai
  base_url: 'https://api.openai.com/v1'  # or your custom endpoint
  llm_model_name: gpt-4o-mini
  embedding_models: maidalun1020/bce-embedding-base_v1
  embedding_type: local
  context_length: 32768
  temperature: 0.5
  history_len: 5
  timeout: 600

# Tavily Search Configuration (for vulnerability research)
tavily:
  enabled: true
  api_key: "your_tavily_api_key"
  search_depth: advanced  # basic or advanced
  max_results: 5
  timeout: 30
  
  # Security-focused domains (automatically included)
  security_domains:
    - cve.mitre.org
    - nvd.nist.gov
    - github.com
    - exploit-db.com
```

#### Configuration Options

**Mode Settings:**
- `auto`: Fully automated penetration testing
- `manual`: Manual confirmation for each step  
- `semi`: Semi-automated with some manual steps

**Feature Toggles:**
- `enable_rag`: Enable Retrieval-Augmented Generation (requires Milvus)
- `enable_knowledge_base`: Enable knowledge base features
- `enable_tavily_search`: Enable Tavily web search for vulnerability research

**Database Options:**
- Use `socket` for local MySQL connections (faster than TCP)
- Configure `host`/`port` for remote database connections

#### Quick Configuration Test

Verify your configuration works:

```sh
python -c "from config.config import config; print(f'✅ Config loaded! Mode: {config.mode}')"
```

#### Migrating from Old Configuration

If you're upgrading from a previous version with multiple config files (`basic_config.yaml`, `db_config.yaml`, etc.), you can:

1. **Use the migration script** (automatic):
   ```sh
   python migrate_config.py
   ```

2. **Manual migration**: Copy your settings to the new `config.yaml` structure shown above

3. **Test the new config**: Run the configuration test above

The new system is **backward compatible** - your existing code will continue to work!

### Database Management

VulnBot now includes database utilities to help manage MySQL connections:

```sh
# Initialize database tables
python cli.py db init

# Test database connection
python cli.py db test

# Connect to MySQL using configured settings
python cli.py db connect

# Show database connection info
python cli.py db info
```

### Initialize the Project

Before using VulnBot, initialize the project:

```sh
python cli.py init
```

### Start the RAG Module

```sh
python cli.py start -a
```

### Run VulnBot

To execute VulnBot, use:

```sh
python cli.py vulnbot -m {max_interactions}
```

Replace `{max_interactions}` with the desired number of interactions.

---

## Citation

If you use VulnBot for academic purposes, please cite our [paper](https://arxiv.org/abs/2501.13411):

```
@misc{kong2025vulnbotautonomouspenetrationtesting,
      title={VulnBot: Autonomous Penetration Testing for a Multi-Agent Collaborative Framework}, 
      author={He Kong and Die Hu and Jingguo Ge and Liangxiong Li and Tong Li and Bingzhen Wu},
      year={2025},
      eprint={2501.13411},
      archivePrefix={arXiv},
      primaryClass={cs.SE},
      url={https://arxiv.org/abs/2501.13411}, 
}
```

---

## Contact

If you have any questions or suggestions, please open an issue on GitHub. Contributions, discussions, and improvements are always welcome!

## Patched
If "btw i use nixos" user read this, this is for you.
If not, install `nix` in linux/wsl/macos. Link: https://nixos.org/download/ or setup MySQL manually in other distro.
Pick shell.nix and add these lines:
```nix
{ pkgs ? import <nixpkgs> { config.allowUnfree = true; } }:
pkgs.mkShell {
   buildInputs = with pkgs; [
      mysql80
      python311Full.uv
      ...
   ]
   shellHook = ''
     # Set up library paths for compiled Python packages
    export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:${pkgs.libffi}/lib:${pkgs.openssl.out}/lib:${pkgs.glibc}/lib:$LD_LIBRARY_PATH"
    
    # Add headers for Python package compilation
    export C_INCLUDE_PATH="${pkgs.linuxHeaders}/include:${pkgs.libevdev}/include:${pkgs.libinput}/include:$C_INCLUDE_PATH"
    export PKG_CONFIG_PATH="${pkgs.libevdev}/lib/pkgconfig:${pkgs.libinput}/lib/pkgconfig:$PKG_CONFIG_PATH"
    
    # MySQL setup
    export MYSQL_HOME="$PWD/.mysql"
    export MYSQL_DATADIR="$MYSQL_HOME/data"
    
    # Create MySQL directories if they don't exist
    mkdir -p "$MYSQL_DATADIR"
    
    # Initialize MySQL database if not already done
    if [ ! -d "$MYSQL_DATADIR/mysql" ]; then
      echo "Initializing MySQL database..."
      mysqld --initialize-insecure --user=$USER --datadir="$MYSQL_DATADIR"
    fi
    
    echo "MySQL server available. To start: mysqld --datadir=$MYSQL_DATADIR --socket=$MYSQL_HOME/mysql.sock --pid-file=$MYSQL_HOME/mysql.pid"
    echo "To connect: mysql --socket=$MYSQL_HOME/mysql.sock"
   '';
}

Then edit db_config.yaml to match your MySQL settings, including socket location after `nix-shell --run "bash"`.

Start database with command at "To start: mysqld ...", and use socket path instead of username/password

Run these commands to setup db `nix-shell --run "mysql --socket=<socket-path-showed-above>/.mysql/mysql.sock -u root -e 'CREATE DATABASE IF NOT EXISTS vulnbot_db;'"`

Run `nix-shell --run "bash"` and
```bash
uv venv --python 3.11.11
uv pip install -r requirements.txt
python cli.py init
...
```