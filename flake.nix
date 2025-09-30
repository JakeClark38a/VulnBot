{
  description = "VulnBot - Autonomous Penetration Testing Framework";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          config.allowUnfree = true;
        };
        
        # Python with required packages
        pythonEnv = pkgs.python311.withPackages (ps: with ps; [
          pip
          setuptools
          wheel
          # Core dependencies that can be installed via nix
          pyyaml
          requests
          click
          sqlalchemy
          pymysql
          cryptography
          # Other common packages
          numpy
          pandas
        ]);

      in {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            # Python environment
            pythonEnv
            
            # MySQL client and server
            mysql80
            
            # Development tools
            git
            curl
            wget
            
            # Build tools for Python packages
            gcc
            pkg-config
            
            # Libraries needed for Python package compilation
            zlib
            libffi
            openssl
            glibc
            
            # Headers for development
            linuxHeaders
            
            # Additional utilities
            which
            ps
            nettools
          ];

          shellHook = ''
            echo "🚀 VulnBot Development Environment"
            echo "================================="
            
            # Set up library paths for compiled Python packages
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.zlib}/lib:${pkgs.libffi}/lib:${pkgs.openssl.out}/lib:${pkgs.glibc}/lib:$LD_LIBRARY_PATH"
            
            # Add headers for Python package compilation  
            export C_INCLUDE_PATH="${pkgs.linuxHeaders}/include:$C_INCLUDE_PATH"
            export PKG_CONFIG_PATH="${pkgs.pkg-config}/lib/pkgconfig:$PKG_CONFIG_PATH"
            
            # MySQL setup
            export MYSQL_HOME="$PWD/.mysql"
            export MYSQL_DATADIR="$MYSQL_HOME/data"
            export MYSQL_SOCKET="$MYSQL_HOME/mysql.sock"
            export MYSQL_PIDFILE="$MYSQL_HOME/mysql.pid"
            
            # Create MySQL directories if they don't exist
            mkdir -p "$MYSQL_DATADIR"
            
            # Initialize MySQL database if not already done
            if [ ! -d "$MYSQL_DATADIR/mysql" ]; then
              echo "📦 Initializing MySQL database..."
              mysqld --initialize-insecure --user=$USER --datadir="$MYSQL_DATADIR" --socket="$MYSQL_SOCKET"
              echo "✅ MySQL database initialized"
            fi
            
            # Note: Install Python dependencies manually with: pip install -r requirements.txt
            
            # Check if MySQL client is available
            if command -v mysql &> /dev/null; then
              echo "✅ MySQL client available: $(mysql --version | head -n1)"
            else
              echo "❌ MySQL client not found"
            fi
            
            # Check Python version
            echo "🐍 Python version: $(python --version)"
            
            echo ""
            echo "📋 Quick Commands:"
            echo "  Start MySQL: mysqld --datadir=$MYSQL_DATADIR --socket=$MYSQL_SOCKET --pid-file=$MYSQL_PIDFILE &"
            echo "  Connect to MySQL: mysql --socket=$MYSQL_SOCKET -u root"
            echo "  Create database: mysql --socket=$MYSQL_SOCKET -u root -e 'CREATE DATABASE IF NOT EXISTS vulnbot_db;'"
            echo "  Test VulnBot DB: python cli.py db test"
            echo ""
          '';

          # Environment variables
          PYTHONPATH = ".";
          PYTHONDONTWRITEBYTECODE = "1";
          PIP_DISABLE_PIP_VERSION_CHECK = "1";
        };
      });
}