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
  
  # Kali Linux connection, Kali server must enable SSH
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

# Database Configuration, use docker-compose.yml to build server immediately
database:
  mysql:
    host: 10.0.0.50
    port: 3306
    user: root
    password: '123'
    database: vulnbot_db
    # socket: /tmp/mysql.sock  # Optional: Unix socket for local connections
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

## Setup detailed
1. Clone this repo
```
git clone https://github.com/JakeClark38a/VulnBot
cd VulnBot
```
2. Create config.yaml like above.
3. Open MySQL server (server that cloned)