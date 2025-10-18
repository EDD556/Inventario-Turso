import reflex as rx
from typing import Literal
from . import utils
import asyncio
import random
import string
import logging
import csv
from datetime import datetime
from .models import (
    StockByFamily,
    DashboardStats,
    Product,
    SpecialFamily,
    DiscontinuedSKU,
    EditableProduct,
)


class State(rx.State):
    search_query: str = ""
    search_by: Literal["sku", "family", "special_family"] = "sku"
    search_results: list[Product] = []
    is_searching: bool = False
    upload_progress: int = 0
    is_uploading: bool = False
    file_status_message: str = (
        "Arrastra un archivo Excel aquí o haz clic para seleccionar."
    )
    families: list[str] = []
    active_tab: Literal["query", "dashboard"] = "query"
    stats: DashboardStats = {
        "total_products": 0,
        "total_stock": 0,
        "family_count": 0,
        "low_stock_count": 0,
    }
    stock_by_family: list[StockByFamily] = []
    low_stock_products: list[Product] = []
    is_loading_dashboard: bool = False
    show_config_dialog: bool = False
    config_tab: Literal["upload", "special_families", "discontinued"] = "upload"
    special_families: list[SpecialFamily] = []
    special_family_skus: list[dict] = []
    discontinued_skus: list[DiscontinuedSKU] = []
    new_special_family_name: str = ""
    add_sku_to_family_id: int = 0
    add_sku_to_family_sku: str = ""
    new_discontinued_sku: str = ""
    new_discontinued_reason: str = ""
    selected_family_id: int | None = None
    show_edit_dialog: bool = False
    editing_product: EditableProduct | None = None
    show_delete_dialog: bool = False
    product_to_delete_sku: str | None = None

    @rx.event
    def on_load(self):
        utils.setup_database()
        yield State.fetch_families
        yield State.load_dashboard_data
        yield State.load_special_families
        yield State.load_discontinued_skus

    @rx.event
    def toggle_config_dialog(self):
        self.show_config_dialog = not self.show_config_dialog

    @rx.event
    def set_config_tab(self, tab: str):
        self.config_tab = tab

    @rx.event(background=True)
    async def fetch_families(self):
        async with self:
            self.is_searching = True
        try:
            client = utils.get_db_client()
            if not client:
                return
            result = await asyncio.to_thread(
                client.execute, "SELECT DISTINCT family FROM inventory ORDER BY family"
            )
            families = [row[0] for row in result.rows]
            async with self:
                self.families = families
        except Exception as e:
            logging.exception(f"Error fetching families: {e}")
        finally:
            async with self:
                self.is_searching = False
            if client:
                client.close()

    @rx.event
    async def load_special_families(self):
        self.special_families = await asyncio.to_thread(utils.get_special_families)

    @rx.event(background=True)
    async def create_special_family(self, form_data: dict):
        family_name = form_data.get("new_special_family_name", "").strip()
        if not family_name:
            return
        try:
            await asyncio.to_thread(utils.create_special_family, family_name)
            async with self:
                self.new_special_family_name = ""
            await self.load_special_families()
        except Exception as e:
            logging.exception(f"Error creating special family: {e}")

    @rx.event(background=True)
    async def delete_special_family(self, family_id: int):
        try:
            await asyncio.to_thread(utils.delete_special_family, family_id)
            async with self:
                await self.load_special_families()
        except Exception as e:
            logging.exception(f"Error deleting special family: {e}")

    @rx.event
    async def load_skus_for_family(self, family_id: int):
        self.selected_family_id = family_id
        self.special_family_skus = await asyncio.to_thread(
            utils.get_skus_for_family, family_id
        )

    @rx.event
    def clear_selected_family(self):
        self.selected_family_id = None
        self.special_family_skus = []

    @rx.event(background=True)
    async def add_sku_to_special_family(self, form_data: dict):
        sku_to_add = form_data.get("add_sku_to_family_sku", "").strip()
        if not sku_to_add or self.add_sku_to_family_id == 0:
            return
        try:
            await asyncio.to_thread(
                utils.add_sku_to_family, self.add_sku_to_family_id, sku_to_add
            )
            async with self:
                self.add_sku_to_family_sku = ""
            await self.load_skus_for_family(self.add_sku_to_family_id)
        except Exception as e:
            logging.exception(f"Error adding sku to family: {e}")

    @rx.event(background=True)
    async def remove_sku_from_family(self, special_family_sku_id: int):
        try:
            await asyncio.to_thread(utils.remove_sku_from_family, special_family_sku_id)
            if self.selected_family_id:
                async with self:
                    await self.load_skus_for_family(self.selected_family_id)
        except Exception as e:
            logging.exception(f"Error removing sku from family: {e}")

    @rx.event
    async def load_discontinued_skus(self):
        self.discontinued_skus = await asyncio.to_thread(utils.get_discontinued_skus)

    @rx.event(background=True)
    async def add_discontinued_sku(self, form_data: dict):
        sku = form_data.get("new_discontinued_sku", "").strip()
        reason = form_data.get("new_discontinued_reason", "").strip()
        if not sku:
            return
        try:
            await asyncio.to_thread(utils.add_discontinued_sku, sku, reason)
            async with self:
                self.new_discontinued_sku = ""
                self.new_discontinued_reason = ""
            await self.load_discontinued_skus()
        except Exception as e:
            logging.exception(f"Error adding discontinued sku: {e}")

    @rx.event(background=True)
    async def remove_discontinued_sku(self, sku_id: int):
        try:
            await asyncio.to_thread(utils.remove_discontinued_sku, sku_id)
            async with self:
                await self.load_discontinued_skus()
        except Exception as e:
            logging.exception(f"Error removing discontinued sku: {e}")

    @rx.event
    def set_active_tab(self, tab: Literal["query", "dashboard"]):
        self.active_tab = tab
        if tab == "dashboard":
            return State.load_dashboard_data

    @rx.event(background=True)
    async def load_dashboard_data(self):
        async with self:
            self.is_loading_dashboard = True
        try:
            stats, stock_family, low_stock = await asyncio.to_thread(
                utils.get_dashboard_data
            )
            async with self:
                self.stats = stats
                self.stock_by_family = stock_family
                self.low_stock_products = low_stock
        except Exception as e:
            logging.exception(f"Error loading dashboard data: {e}")
        finally:
            async with self:
                self.is_loading_dashboard = False

    @rx.event
    def export_to_csv(self) -> rx.download:
        """Export the current search results to a CSV file."""
        if not self.search_results:
            return rx.toast.warning("No hay resultados para exportar.")
        output_filename = f"existencias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        import io

        string_io = io.StringIO()
        writer = csv.writer(string_io)
        writer.writerow(["SKU", "Descripción", "Familia", "Existencia Actual"])
        for product in self.search_results:
            writer.writerow(
                [
                    product["sku"],
                    product["description"],
                    product["family"],
                    product["current_stock"],
                ]
            )
        csv_content = string_io.getvalue().encode("utf-8")
        string_io.close()
        return rx.download(data=csv_content, filename=output_filename)

    @rx.event
    def set_search_query_and_search(self, query: str):
        self.search_query = query
        return State.handle_search

    @rx.event(background=True)
    async def handle_search(self):
        async with self:
            self.is_searching = True
            if not self.search_query.strip():
                self.search_results = []
                self.is_searching = False
                return
        try:
            results = await asyncio.to_thread(
                utils.search_db, self.search_query, self.search_by
            )
            async with self:
                self.search_results = results
        except Exception as e:
            logging.exception(f"Error during search: {e}")
            async with self:
                self.search_results = []
        finally:
            async with self:
                self.is_searching = False

    @rx.event
    def set_search_by(self, value: Literal["sku", "family", "special_family"]):
        self.search_query = ""
        self.search_results = []
        self.search_by = value
        if value != "sku":
            return State.handle_search

    @rx.event
    async def handle_upload(self, files: list[rx.UploadFile]):
        if not files:
            return
        uploader = files[0]
        self.is_uploading = True
        self.upload_progress = 0
        self.file_status_message = f"Subiendo: {uploader.name}"
        yield
        upload_dir = rx.get_upload_dir()
        upload_dir.mkdir(parents=True, exist_ok=True)
        unique_name = (
            "".join(random.choices(string.ascii_letters + string.digits, k=10))
            + "_"
            + uploader.name
        )
        file_path = upload_dir / unique_name
        total_size = uploader.size
        uploaded_size = 0
        try:
            with open(file_path, "wb") as file_obj:
                while data := (await uploader.read(1024 * 1024)):
                    file_obj.write(data)
                    uploaded_size += len(data)
                    progress = int(uploaded_size / total_size * 50)
                    self.upload_progress = progress
                    yield
            self.file_status_message = "Procesando archivo..."
            yield
            products = await asyncio.to_thread(utils.parse_excel_file, file_path)
            if products is None:
                self.is_uploading = False
                self.file_status_message = "Error: formato de archivo inválido."
                return
            self.file_status_message = f"Importando {len(products)} registros..."
            yield
            inserted, updated = await asyncio.to_thread(
                utils.import_products_to_db, products
            )
            for i in range(51, 101, 5):
                await asyncio.sleep(0.05)
                self.upload_progress = i
                yield
            self.is_uploading = False
            self.file_status_message = (
                "Arrastra un archivo Excel aquí o haz clic para seleccionar."
            )
            await self.fetch_families()
            await self.load_dashboard_data()
        except Exception as e:
            logging.exception(f"Error handling upload: {e}")
            self.is_uploading = False
            self.file_status_message = "Error durante la carga."

    @rx.event
    def open_edit_dialog(self, product: Product):
        self.show_edit_dialog = True
        self.editing_product = product

    @rx.event
    def close_edit_dialog(self):
        self.show_edit_dialog = False
        self.editing_product = None

    @rx.event(background=True)
    async def update_product(self, form_data: dict):
        if not self.editing_product:
            return
        try:
            sku = self.editing_product["sku"]
            description = form_data.get(
                "description", self.editing_product["description"]
            )
            family = form_data.get("family", self.editing_product["family"])
            stock_str = form_data.get(
                "current_stock", self.editing_product["current_stock"]
            )
            current_stock = int(stock_str) if stock_str.isdigit() else 0
            await asyncio.to_thread(
                utils.update_product_in_db, sku, description, family, current_stock
            )
            async with self:
                self.show_edit_dialog = False
                self.editing_product = None
            await self.handle_search()
        except Exception as e:
            logging.exception(f"Error updating product: {e}")

    @rx.event
    def open_delete_dialog(self, sku: str):
        self.show_delete_dialog = True
        self.product_to_delete_sku = sku

    @rx.event
    def close_delete_dialog(self):
        self.show_delete_dialog = False
        self.product_to_delete_sku = None

    @rx.event(background=True)
    async def delete_product(self):
        if not self.product_to_delete_sku:
            return
        try:
            await asyncio.to_thread(
                utils.delete_product_from_db, self.product_to_delete_sku
            )
            async with self:
                self.show_delete_dialog = False
                self.product_to_delete_sku = None
            await self.handle_search()
        except Exception as e:
            logging.exception(f"Error deleting product: {e}")