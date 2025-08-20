# VulnBot MySQL Socket Configuration Example

This example shows how to configure VulnBot to use the MySQL server from the nix-shell environment.

## Using nix-shell MySQL

If you're using the nix-shell environment with MySQL, update your `db_config.yaml`:

```yaml
mysql:
  host: localhost
  port: 3306
  user: root  # Use root since nix-shell MySQL initializes without password
  password: ""  # Empty password for development
  database: vulnbot_db
  socket: .mysql/mysql.sock  # Path relative to project root
  charset: utf8mb4
  connect_timeout: 30
  pool_size: 10
  max_overflow: 20
```

## Starting MySQL in nix-shell

1. Enter the nix-shell:
   ```bash
   nix-shell
   ```

2. Start MySQL server:
   ```bash
   mysqld --datadir=$MYSQL_DATADIR --socket=$MYSQL_HOME/mysql.sock --pid-file=$MYSQL_HOME/mysql.pid &
   ```

3. Create the VulnBot database:
   ```bash
   mysql --socket=$MYSQL_HOME/mysql.sock -e "CREATE DATABASE vulnbot_db;"
   ```

4. Test VulnBot database connection:
   ```bash
   python cli.py db test
   ```

## Benefits of Socket Connection

- **Performance**: Unix sockets are faster than TCP for local connections
- **Security**: No network exposure for database connections
- **Simplicity**: No need to configure firewall rules or network access

## Troubleshooting

- Ensure MySQL server is running before testing VulnBot connection
- Check that the socket path in config matches the actual MySQL socket location
- Verify database permissions if connection fails
