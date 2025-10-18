import reflex as rx
import libsql_client
import os
import pandas as pd
from typing import Any, cast
import logging
from .models import DashboardStats, StockByFamily, Product


def get_db_client() -> libsql_client.Client:
    url = "https://primaria-edd556.aws-ap-northeast-1.turso.io"
    auth_token = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3NjA4MTgxNzAsImlkIjoiYTUyMzY2NmMtZjhlNC00YWJlLWE1NjQtMmVjYTY5ODBlMWMxIiwicmlkIjoiN2IyZDk3MGYtZGJkMC00YzU0LWFjYWQtMjQ2MDgwMGViYmExIn0.cJs_y0rJRQ2nnpieSf2ssaA12xjwk_sfKlpvOjJ2Zkqn_n8AAf8D1n3_HxGVPy0EhhjhZN-66dmOP3BNGCIwAw"
    try:
        return libsql_client.create_client_sync(url=url, auth_token=auth_token)
    except Exception as e:
        logging.exception(f"Failed to create database client: {e}")
        return None


def setup_database():
    client = get_db_client()
    if not client:
        return
    try:
        client.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL UNIQUE,
                description TEXT NOT NULL,
                family TEXT NOT NULL,
                current_stock INTEGER NOT NULL DEFAULT 0
            )
        """)
        client.execute("CREATE INDEX IF NOT EXISTS idx_sku ON inventory(sku)")
        client.execute("CREATE INDEX IF NOT EXISTS idx_family ON inventory(family)")
        client.execute("""
            CREATE TABLE IF NOT EXISTS special_families (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        client.execute("""
            CREATE TABLE IF NOT EXISTS special_family_skus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                special_family_id INTEGER NOT NULL,
                sku TEXT NOT NULL,
                FOREIGN KEY (special_family_id) REFERENCES special_families(id) ON DELETE CASCADE
            )
        """)
        client.execute("""
            CREATE TABLE IF NOT EXISTS discontinued_skus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sku TEXT NOT NULL UNIQUE,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    except Exception as e:
        logging.exception(f"Database setup failed: {e}")
    finally:
        if client:
            client.close()


def get_dashboard_data() -> tuple[DashboardStats, list[StockByFamily], list[Product]]:
    client = get_db_client()
    if not client:
        return (
            cast(
                DashboardStats,
                {
                    "total_products": 0,
                    "total_stock": 0,
                    "family_count": 0,
                    "low_stock_count": 0,
                },
            ),
            [],
            [],
        )
    try:
        (
            total_products_res,
            total_stock_res,
            family_count_res,
            low_stock_count_res,
            stock_by_family_res,
            low_stock_products_res,
        ) = client.batch(
            [
                "SELECT COUNT(id) FROM inventory",
                "SELECT SUM(current_stock) FROM inventory",
                "SELECT COUNT(DISTINCT family) FROM inventory",
                "SELECT COUNT(id) FROM inventory WHERE current_stock < 20",
                "SELECT family, SUM(current_stock) as stock FROM inventory GROUP BY family ORDER BY stock DESC",
                "SELECT sku, description, family, current_stock FROM inventory WHERE current_stock < 20 ORDER BY current_stock ASC LIMIT 50",
            ]
        )
        stats: DashboardStats = {
            "total_products": total_products_res.rows[0][0]
            if total_products_res.rows and total_products_res.rows[0][0] is not None
            else 0,
            "total_stock": total_stock_res.rows[0][0]
            if total_stock_res.rows and total_stock_res.rows[0][0] is not None
            else 0,
            "family_count": family_count_res.rows[0][0]
            if family_count_res.rows and family_count_res.rows[0][0] is not None
            else 0,
            "low_stock_count": low_stock_count_res.rows[0][0]
            if low_stock_count_res.rows and low_stock_count_res.rows[0][0] is not None
            else 0,
        }
        stock_by_family = [
            StockByFamily(name=row[0], stock=row[1]) for row in stock_by_family_res.rows
        ]
        low_stock_products = [
            Product(sku=row[0], description=row[1], family=row[2], current_stock=row[3])
            for row in low_stock_products_res.rows
        ]
        return (stats, stock_by_family, low_stock_products)
    except Exception as e:
        logging.exception(f"Error getting dashboard data: {e}")
        return (
            cast(
                DashboardStats,
                {
                    "total_products": 0,
                    "total_stock": 0,
                    "family_count": 0,
                    "low_stock_count": 0,
                },
            ),
            [],
            [],
        )
    finally:
        if client:
            client.close()


def parse_excel_file(file_path: str) -> list[Product] | None:
    try:
        df = pd.read_excel(file_path)
        df.columns = [col.strip().lower() for col in df.columns]
        column_map = {
            "sku": "sku",
            "descripcion": "description",
            "descripción": "description",
            "familia": "family",
            "existencias": "current_stock",
            "existencia_actual": "current_stock",
            "existencia": "current_stock",
        }
        df.rename(columns=column_map, inplace=True)
        required_columns = {"sku", "description", "family", "current_stock"}
        if not required_columns.issubset(df.columns):
            logging.error(f"Missing required columns. Found: {df.columns.tolist()}")
            return None
        df["sku"] = df["sku"].astype(str)
        df["description"] = df["description"].astype(str)
        df["family"] = df["family"].astype(str)
        df["current_stock"] = (
            pd.to_numeric(df["current_stock"], errors="coerce").fillna(0).astype(int)
        )
        return df[["sku", "description", "family", "current_stock"]].to_dict("records")
    except Exception as e:
        logging.exception(f"Error parsing Excel file: {e}")
        return None


def import_products_to_db(products: list[Product]) -> tuple[int, int]:
    client = get_db_client()
    if not client:
        return (0, 0)
    inserted_count = 0
    updated_count = 0
    try:
        for product in products:
            res = client.execute(
                "SELECT id FROM inventory WHERE sku = ?", [product["sku"]]
            )
            if len(res.rows) > 0:
                client.execute(
                    "UPDATE inventory SET description = ?, family = ?, current_stock = ? WHERE sku = ?",
                    [
                        product["description"],
                        product["family"],
                        product["current_stock"],
                        product["sku"],
                    ],
                )
                updated_count += 1
            else:
                client.execute(
                    "INSERT INTO inventory (sku, description, family, current_stock) VALUES (?, ?, ?, ?)",
                    [
                        product["sku"],
                        product["description"],
                        product["family"],
                        product["current_stock"],
                    ],
                )
                inserted_count += 1
        return (inserted_count, updated_count)
    except Exception as e:
        logging.exception(f"Database import failed: {e}")
        return (0, 0)
    finally:
        if client:
            client.close()


def search_db(query: str, by: str) -> list[Product]:
    client = get_db_client()
    if not client:
        return []
    try:
        if by == "sku":
            sql_query = "SELECT sku, description, family, current_stock FROM inventory WHERE sku LIKE ? AND sku NOT IN (SELECT sku FROM discontinued_skus) LIMIT 50"
            params = [f"%{query}%"]
        elif by == "family":
            sql_query = "SELECT sku, description, family, current_stock FROM inventory WHERE family = ? AND sku NOT IN (SELECT sku FROM discontinued_skus) LIMIT 200"
            params = [query]
        elif by == "special_family":
            if not query:
                return []
            sql_query = """
                SELECT i.sku, i.description, i.family, i.current_stock
                FROM inventory i
                JOIN special_family_skus sfs ON i.sku = sfs.sku
                WHERE sfs.special_family_id = ? AND i.sku NOT IN (SELECT sku FROM discontinued_skus)
                LIMIT 500
            """
            params = [int(query)]
        else:
            return []
        result = client.execute(sql_query, params)
        return [
            Product(sku=row[0], description=row[1], family=row[2], current_stock=row[3])
            for row in result.rows
        ]
    except Exception as e:
        logging.exception(f"Database search failed: {e}")
        return []
    finally:
        if client:
            client.close()


def get_special_families():
    client = get_db_client()
    if not client:
        return []
    try:
        res = client.execute("SELECT id, name FROM special_families ORDER BY name")
        return [{"id": row[0], "name": row[1]} for row in res.rows]
    finally:
        client.close()


def create_special_family(name: str):
    client = get_db_client()
    if not client:
        return
    try:
        client.execute("INSERT INTO special_families (name) VALUES (?)", [name])
    finally:
        client.close()


def delete_special_family(family_id: int):
    client = get_db_client()
    if not client:
        return
    try:
        client.execute("DELETE FROM special_families WHERE id = ?", [family_id])
    finally:
        client.close()


def get_skus_for_family(family_id: int):
    client = get_db_client()
    if not client:
        return []
    try:
        res = client.execute(
            "SELECT id, sku FROM special_family_skus WHERE special_family_id = ? ORDER BY sku",
            [family_id],
        )
        return [{"id": row[0], "sku": row[1]} for row in res.rows]
    finally:
        client.close()


def add_sku_to_family(family_id: int, sku: str):
    client = get_db_client()
    if not client:
        return
    try:
        client.execute(
            "INSERT INTO special_family_skus (special_family_id, sku) VALUES (?, ?)",
            [family_id, sku],
        )
    finally:
        client.close()


def remove_sku_from_family(special_family_sku_id: int):
    client = get_db_client()
    if not client:
        return
    try:
        client.execute(
            "DELETE FROM special_family_skus WHERE id = ?", [special_family_sku_id]
        )
    finally:
        client.close()


def get_discontinued_skus():
    client = get_db_client()
    if not client:
        return []
    try:
        res = client.execute(
            "SELECT id, sku, reason FROM discontinued_skus ORDER BY sku"
        )
        return [{"id": row[0], "sku": row[1], "reason": row[2]} for row in res.rows]
    finally:
        client.close()


def add_discontinued_sku(sku: str, reason: str | None):
    client = get_db_client()
    if not client:
        return
    try:
        client.execute(
            "INSERT INTO discontinued_skus (sku, reason) VALUES (?, ?)", [sku, reason]
        )
    finally:
        client.close()


def remove_discontinued_sku(sku_id: int):
    client = get_db_client()
    if not client:
        return
    try:
        client.execute("DELETE FROM discontinued_skus WHERE id = ?", [sku_id])
    finally:
        if client:
            client.close()


def update_product_in_db(sku: str, description: str, family: str, current_stock: int):
    client = get_db_client()
    if not client:
        return
    try:
        client.execute(
            "UPDATE inventory SET description = ?, family = ?, current_stock = ? WHERE sku = ?",
            [description, family, current_stock, sku],
        )
    finally:
        if client:
            client.close()


def delete_product_from_db(sku: str):
    client = get_db_client()
    if not client:
        return
    try:
        client.execute("DELETE FROM inventory WHERE sku = ?", [sku])
    finally:
        if client:
            client.close()