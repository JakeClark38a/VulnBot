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

Before initializing VulnBot, you need to configure system settings. Refer to the [Configuration Guide](Configuration%20Guide.md) for detailed instructions on modifying:

- **Kali Linux configuration** (hostname, port, username, password)
- **MySQL database settings** (host, port, user, password, database, socket support)
- **LLM settings** (base_url, llm_model_name, api_key)
- **Enabling RAG** (set `enable_rag` to `true` and configure `milvus` and `kb_name`)

**New in this version**: MySQL socket connection support for improved local database performance. Use the `socket` field in `db_config.yaml` to connect via Unix socket instead of TCP.

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

Then edit db_config.yaml to match your MySQL settings, including socket support.

Run these commands to setup db `nix-shell --run "mysql --socket=/home/jc/attacker-tools/.mysql/mysql.sock -u root -e 'CREATE DATABASE IF NOT EXISTS vulnbot_db;'"`

Run `nix-shell --run "bash"` and
```bash
uv venv --python 3.11.11
uv pip install -r requirements.txt
python cli.py init
...
```