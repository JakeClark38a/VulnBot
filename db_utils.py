#!/usr/bin/env python3
"""
Database utility script for VulnBot
Provides commands to initialize, connect, and manage the MySQL database
"""

import click
import subprocess
import sys
from pathlib import Path

try:
    from config.config import Configs
    from utils.session import create_tables, build_db_url
    from utils.log_common import build_logger
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the VulnBot root directory")
    sys.exit(1)

logger = build_logger()


@click.group(help="Database utilities for VulnBot")
def db():
    pass


@db.command("init")
def init_db():
    """Initialize database tables"""
    try:
        create_tables()
        logger.success("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        sys.exit(1)


@db.command("connect")
def connect_db():
    """Connect to MySQL database using configured settings"""
    mysql_config = Configs.db_config.mysql
    
    if mysql_config.get('socket') and mysql_config['socket'] != "":
        # Connect using Unix socket
        cmd = [
            "mysql",
            f"--socket={mysql_config['socket']}",
            f"--user={mysql_config['user']}",
            f"--database={mysql_config['database']}"
        ]
        if mysql_config.get('password') and mysql_config['password'] != "":
            cmd.append(f"--password={mysql_config['password']}")
    else:
        # Connect using TCP
        cmd = [
            "mysql",
            f"--host={mysql_config['host']}",
            f"--port={mysql_config['port']}",
            f"--user={mysql_config['user']}",
            f"--database={mysql_config['database']}"
        ]
        if mysql_config.get('password') and mysql_config['password'] != "":
            cmd.append(f"--password={mysql_config['password']}")
    
    logger.info(f"Connecting to database: {mysql_config['database']}")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)
    except FileNotFoundError:
        logger.error("MySQL client not found. Please install MySQL client tools.")
        sys.exit(1)


@db.command("info")
def db_info():
    """Show database connection information"""
    mysql_config = Configs.db_config.mysql
    db_url = build_db_url()
    
    logger.info("Database Configuration:")
    logger.info(f"  Database: {mysql_config['database']}")
    logger.info(f"  User: {mysql_config['user']}")
    
    if mysql_config.get('socket') and mysql_config['socket'] != "":
        logger.info(f"  Connection Type: Unix Socket")
        logger.info(f"  Socket Path: {mysql_config['socket']}")
    else:
        logger.info(f"  Connection Type: TCP")
        logger.info(f"  Host: {mysql_config['host']}")
        logger.info(f"  Port: {mysql_config['port']}")
    
    if mysql_config.get('charset'):
        logger.info(f"  Charset: {mysql_config['charset']}")
    
    logger.info(f"  Connection URL: {db_url}")


@db.command("test")
def test_connection():
    """Test database connection"""
    try:
        from utils.session import engine
        with engine.connect() as conn:
            result = conn.execute("SELECT 1 as test")
            if result.fetchone()[0] == 1:
                logger.success("Database connection test successful")
            else:
                logger.error("Database connection test failed")
                sys.exit(1)
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    db()
