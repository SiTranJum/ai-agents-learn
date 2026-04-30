"""
数据库管理器

负责 MySQL 数据库的连接、查询、更新等操作。
使用连接池管理连接，参数化查询防止 SQL 注入。

这个模块提供完整实现，你可以直接使用。

类比 Java：
    类似 Spring 的 JdbcTemplate
    @Component
    public class DatabaseManager {
        @Autowired
        private JdbcTemplate jdbcTemplate;
    }
"""

import mysql.connector
from mysql.connector import pooling, Error
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from dataclasses import dataclass
import sys
from functools import partial

print = partial(print, file=sys.stderr, flush=True)


@dataclass
class DatabaseConfig:
    """
    数据库配置

    类比 Java：
        @ConfigurationProperties(prefix = "database")
        public class DatabaseConfig {
            private String host;
            private int port;
            private String user;
            private String password;
            private String database;
        }
    """
    host: str
    port: int = 3306
    user: str = "root"
    password: str = ""
    database: str = ""
    pool_size: int = 5
    charset: str = "utf8mb4"


class DatabaseManager:
    """
    数据库管理器

    功能：
    1. 连接池管理
    2. 执行查询（SELECT）
    3. 执行更新（UPDATE/DELETE）
    4. 参数化查询防注入
    5. 事务管理

    类比 Java：
        @Component
        public class DatabaseManager {
            private final HikariDataSource dataSource;
            private final JdbcTemplate jdbcTemplate;
        }
    """

    def __init__(self, config: DatabaseConfig):
        """
        初始化数据库连接池

        参数：
            config: 数据库配置

        内部创建连接池：
            类比 Java 的 HikariCP 连接池
            HikariConfig config = new HikariConfig();
            config.setJdbcUrl("jdbc:mysql://...");
            HikariDataSource dataSource = new HikariDataSource(config);
        """
        self.config = config

        try:
            # 创建连接池
            # pooling.MySQLConnectionPool - MySQL 连接池
            # 参数：
            #   pool_name: 连接池名称
            #   pool_size: 连接池大小（最多同时保持多少个连接）
            #   host, port, user, password, database: 数据库连接信息
            #   charset: 字符集（utf8mb4 支持完整 Unicode，包括 emoji）
            self.pool = pooling.MySQLConnectionPool(
                pool_name="db_query_pool",
                pool_size=config.pool_size,
                pool_reset_session=True,  # 每次归还连接时重置会话状态
                host=config.host,
                port=config.port,
                user=config.user,
                password=config.password,
                database=config.database,
                charset=config.charset,
                autocommit=False  # 手动控制事务
            )
            print(f"[数据库] 连接池已创建，大小：{config.pool_size}")

        except Error as e:
            print(f"[数据库错误] 创建连接池失败: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """
        获取数据库连接（上下文管理器）

        使用方式：
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ...")
                # 连接会自动归还到连接池

        类比 Java：
            try (Connection conn = dataSource.getConnection()) {
                // 使用连接
            } // 自动关闭（归还到连接池）

        Yield:
            mysql.connector.connection.MySQLConnection - 数据库连接对象
        """
        conn = None
        try:
            # 从连接池获取连接
            conn = self.pool.get_connection()
            yield conn
        finally:
            # 归还连接到连接池
            if conn:
                conn.close()

    def execute_query(
        self,
        sql: str,
        params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        执行 SELECT 查询

        参数：
            sql: SQL 语句（支持参数化：SELECT * FROM users WHERE id = %s）
            params: 参数元组（例如：(123,)）

        返回：
            查询结果列表，每行是一个字典
            例如：[{"id": 1, "name": "张三"}, {"id": 2, "name": "李四"}]

        类比 Java：
            List<Map<String, Object>> results = jdbcTemplate.queryForList(
                "SELECT * FROM users WHERE id = ?",
                userId
            );

        注意：
            使用参数化查询防止 SQL 注入
            错误的方式：f"SELECT * FROM users WHERE id = {user_id}"  # 危险！
            正确的方式：execute_query("SELECT * FROM users WHERE id = %s", (user_id,))
        """
        with self.get_connection() as conn:
            # cursor(dictionary=True) - 返回字典格式的结果
            # 如果不加 dictionary=True，返回的是元组格式
            cursor = conn.cursor(dictionary=True)

            try:
                # 执行参数化查询
                # %s 是占位符，params 中的值会被安全地替换进去
                cursor.execute(sql, params or ())

                # fetchall() - 获取所有结果行
                # 类比 Java 的 ResultSet
                results = cursor.fetchall()

                print(f"[查询] 返回 {len(results)} 行")
                return results

            except Error as e:
                # 捕获 MySQL 错误
                print(f"[查询错误] {e}")
                return {
                    "error": True,
                    "error_code": e.errno,
                    "error_message": str(e),
                    "sql_state": getattr(e, 'sqlstate', None)
                }

            finally:
                cursor.close()

    def execute_update(
        self,
        sql: str,
        params: Optional[tuple] = None,
        require_confirmation: bool = True
    ) -> Dict[str, Any]:
        """
        执行 UPDATE/DELETE 语句

        参数：
            sql: SQL 语句
            params: 参数元组
            require_confirmation: 是否需要用户确认（默认 True）

        返回：
            {"success": True, "affected_rows": 5}
            或
            {"require_confirmation": True, "sql": "...", "params": (...)}

        类比 Java：
            int affectedRows = jdbcTemplate.update(
                "UPDATE users SET status = ? WHERE id = ?",
                status, userId
            );

        注意：
            UPDATE/DELETE 操作默认需要用户确认
            这是为了防止误操作导致数据丢失
        """
        if require_confirmation:
            # 返回需要确认的标记
            # 实际的确认逻辑由 Agent Harness 处理
            return {
                "require_confirmation": True,
                "sql": sql,
                "params": params,
                "message": "此操作会修改数据，需要用户确认"
            }

        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                # 执行更新
                cursor.execute(sql, params or ())

                # 提交事务
                # 类比 Java 的 connection.commit()
                conn.commit()

                affected_rows = cursor.rowcount
                print(f"[更新] 影响 {affected_rows} 行")

                return {
                    "success": True,
                    "affected_rows": affected_rows
                }

            except Error as e:
                # 回滚事务
                # 类比 Java 的 connection.rollback()
                conn.rollback()

                print(f"[更新错误] {e}")
                return {
                    "error": True,
                    "error_message": str(e)
                }

            finally:
                cursor.close()

    def test_connection(self) -> Dict[str, Any]:
        """
        测试数据库连接

        返回：
            {"connected": True, "database": "mydb", "version": "8.0.32"}
            或
            {"connected": False, "error": "错误信息"}

        类比 Java：
            boolean isValid = connection.isValid(5);
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # 查询当前数据库和版本
                cursor.execute("SELECT DATABASE(), VERSION()")
                result = cursor.fetchone()
                cursor.close()

                return {
                    "connected": True,
                    "database": result[0],
                    "version": result[1]
                }

        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        获取表结构信息

        参数：
            table_name: 表名

        返回：
            表的字段信息列表
            [
                {"Field": "id", "Type": "bigint", "Null": "NO", "Key": "PRI", ...},
                {"Field": "username", "Type": "varchar(50)", "Null": "NO", ...}
            ]

        类比 Java：
            DatabaseMetaData metaData = connection.getMetaData();
            ResultSet columns = metaData.getColumns(null, null, tableName, null);
        """
        sql = f"DESCRIBE {table_name}"
        return self.execute_query(sql)
