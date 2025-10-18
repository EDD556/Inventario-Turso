import reflex as rx
from .state import State
from . import utils


def file_upload_component() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            "1. Cargar Datos", class_name="text-lg font-semibold text-gray-700 mb-4"
        ),
        rx.upload.root(
            rx.el.div(
                rx.el.div(
                    rx.icon("cloud_upload", class_name="w-12 h-12 text-gray-400"),
                    rx.el.h3(
                        "Subir archivo Excel",
                        class_name="mt-4 text-sm font-semibold text-gray-900",
                    ),
                    rx.el.p(
                        State.file_status_message,
                        class_name="mt-1 text-xs text-gray-500",
                    ),
                    class_name="text-center",
                ),
                class_name="flex items-center justify-center w-full h-full",
            ),
            id="upload_excel",
            border="2px dashed var(--gray-a7)",
            padding="2em",
            border_radius="var(--radius-3)",
            bg="var(--gray-a2)",
            class_name="w-full cursor-pointer hover:bg-[var(--gray-a3)] transition-colors",
            on_drop=State.handle_upload,
            is_disabled=State.is_uploading,
        ),
        rx.cond(
            State.is_uploading,
            rx.el.progress(
                value=State.upload_progress,
                max=100,
                class_name="w-full mt-4 h-2 [&::-webkit-progress-bar]:rounded-lg [&::-webkit-progress-value]:rounded-lg [&::-webkit-progress-bar]:bg-gray-200 [&::-webkit-progress-value]:bg-violet-600",
            ),
        ),
        class_name="w-full p-6 bg-gray-50 rounded-xl",
    )


def search_interface() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.div(
                rx.el.button(
                    rx.icon("scan", class_name="mr-2 h-4 w-4"),
                    "Por SKU",
                    on_click=lambda: State.set_search_by("sku"),
                    class_name=rx.cond(
                        State.search_by == "sku",
                        "flex items-center px-4 py-2 rounded-l-lg bg-violet-600 text-white font-semibold z-10 transition-colors",
                        "flex items-center px-4 py-2 rounded-l-lg bg-white text-gray-700 border border-gray-300 hover:bg-gray-100 transition-colors",
                    ),
                ),
                rx.el.button(
                    rx.icon("tag", class_name="mr-2 h-4 w-4"),
                    "Por Familia",
                    on_click=lambda: State.set_search_by("family"),
                    class_name=rx.cond(
                        State.search_by == "family",
                        "flex items-center px-4 py-2 bg-violet-600 text-white font-semibold z-10 -ml-px transition-colors",
                        "flex items-center px-4 py-2 bg-white text-gray-700 border border-gray-300 hover:bg-gray-100 -ml-px transition-colors",
                    ),
                ),
                rx.el.button(
                    rx.icon("star", class_name="mr-2 h-4 w-4"),
                    "Por Familia Especial",
                    on_click=lambda: State.set_search_by("special_family"),
                    class_name=rx.cond(
                        State.search_by == "special_family",
                        "flex items-center px-4 py-2 rounded-r-lg bg-violet-600 text-white font-semibold z-10 -ml-px transition-colors",
                        "flex items-center px-4 py-2 rounded-r-lg bg-white text-gray-700 border border-gray-300 hover:bg-gray-100 -ml-px transition-colors",
                    ),
                ),
                class_name="flex",
            ),
            rx.el.div(
                rx.match(
                    State.search_by,
                    (
                        "sku",
                        rx.el.input(
                            placeholder="Buscar por SKU...",
                            on_change=State.set_search_query.debounce(300),
                            on_blur=State.handle_search,
                            on_key_down=lambda key: rx.cond(
                                key == "Enter", State.handle_search, rx.noop()
                            ),
                            class_name="w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all",
                            default_value=State.search_query,
                        ),
                    ),
                    (
                        "family",
                        rx.el.select(
                            rx.el.option("-- Todas las familias --", value=""),
                            rx.foreach(
                                State.families,
                                lambda family: rx.el.option(family, value=family),
                            ),
                            value=State.search_query,
                            on_change=State.set_search_query_and_search,
                            class_name="w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all",
                        ),
                    ),
                    (
                        "special_family",
                        rx.el.select(
                            rx.el.option(
                                "-- Todas las familias especiales --", value=""
                            ),
                            rx.foreach(
                                State.special_families,
                                lambda family: rx.el.option(
                                    family["name"], value=family["id"].to_string()
                                ),
                            ),
                            value=State.search_query,
                            on_change=State.set_search_query_and_search,
                            class_name="w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-violet-500 focus:border-transparent transition-all",
                        ),
                    ),
                ),
                rx.cond(
                    State.search_query != "",
                    rx.el.button(
                        rx.icon("x", class_name="h-4 w-4"),
                        on_click=lambda: State.set_search_query_and_search(""),
                        class_name="p-2 text-gray-400 hover:text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-full transition-colors",
                        variant="ghost",
                    ),
                ),
                class_name="flex items-center gap-2 w-full",
            ),
            class_name="flex flex-col md:flex-row gap-4 w-full items-center",
        ),
        class_name="p-6 bg-white rounded-xl shadow-[0_1px_3px_rgba(0,0,0,0.12)] w-full",
    )


def config_dialog() -> rx.Component:
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.trigger(rx.el.button("Open", class_name="hidden")),
        rx.radix.primitives.dialog.content(
            rx.radix.primitives.dialog.title(
                "Configuración del Sistema", class_name="text-xl font-bold"
            ),
            rx.el.div(
                rx.el.button(
                    "Cargar Archivo",
                    on_click=lambda: State.set_config_tab("upload"),
                    class_name=rx.cond(
                        State.config_tab == "upload",
                        "px-3 py-1.5 text-sm font-semibold text-white bg-violet-600 rounded-md",
                        "px-3 py-1.5 text-sm font-semibold text-gray-600 hover:bg-gray-100 rounded-md",
                    ),
                ),
                rx.el.button(
                    "Familias Especiales",
                    on_click=lambda: State.set_config_tab("special_families"),
                    class_name=rx.cond(
                        State.config_tab == "special_families",
                        "px-3 py-1.5 text-sm font-semibold text-white bg-violet-600 rounded-md",
                        "px-3 py-1.5 text-sm font-semibold text-gray-600 hover:bg-gray-100 rounded-md",
                    ),
                ),
                rx.el.button(
                    "SKUs Descatalogados",
                    on_click=lambda: State.set_config_tab("discontinued"),
                    class_name=rx.cond(
                        State.config_tab == "discontinued",
                        "px-3 py-1.5 text-sm font-semibold text-white bg-violet-600 rounded-md",
                        "px-3 py-1.5 text-sm font-semibold text-gray-600 hover:bg-gray-100 rounded-md",
                    ),
                ),
                class_name="flex items-center gap-2 border-b pb-3 mb-4",
            ),
            rx.match(
                State.config_tab,
                ("upload", file_upload_component()),
                ("special_families", special_families_management()),
                ("discontinued", discontinued_sku_management()),
            ),
            rx.el.div(
                rx.radix.primitives.dialog.close(
                    rx.el.button(
                        "Cerrar",
                        color_scheme="gray",
                        variant="soft",
                        class_name="cursor-pointer",
                    )
                ),
                class_name="flex justify-end gap-3 mt-4",
            ),
            class_name="max-w-4xl",
        ),
        open=State.show_config_dialog,
        on_open_change=State.set_show_config_dialog,
    )


def product_card(product: utils.Product) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h3(product["sku"], class_name="font-bold text-lg text-violet-700"),
            rx.el.div(
                rx.el.button(
                    rx.icon("pencil", class_name="h-4 w-4"),
                    on_click=lambda: State.open_edit_dialog(product),
                    class_name="p-1 text-gray-500 hover:text-violet-600 rounded-md transition-colors",
                ),
                rx.el.button(
                    rx.icon("trash-2", class_name="h-4 w-4"),
                    on_click=lambda: State.open_delete_dialog(product["sku"]),
                    class_name="p-1 text-gray-500 hover:text-red-600 rounded-md transition-colors",
                ),
                class_name="flex items-center gap-1",
            ),
            class_name="flex justify-between items-center",
        ),
        rx.el.p(product["description"], class_name="mt-2 text-sm text-gray-600"),
        rx.el.span(
            product["family"],
            class_name="mt-2 px-2 py-1 bg-gray-200 text-gray-700 text-xs font-semibold rounded-full w-fit",
        ),
        rx.el.div(
            rx.el.p("Existencia:", class_name="text-sm font-medium text-gray-800"),
            rx.el.p(
                product["current_stock"],
                class_name=rx.cond(
                    product["current_stock"] > 0,
                    "text-xl font-bold text-green-600",
                    "text-xl font-bold text-red-600",
                ),
            ),
            class_name="mt-4 flex justify-between items-center bg-gray-50 p-3 rounded-lg",
        ),
        class_name="bg-white p-4 rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow",
    )


def results_display() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h3("Resultados", class_name="text-lg font-semibold text-gray-800"),
            rx.cond(
                State.search_results.length() > 0,
                rx.el.p(
                    State.search_results.length().to_string()
                    + " productos encontrados",
                    class_name="text-sm text-gray-500",
                ),
            ),
            class_name="flex justify-between items-baseline mb-4",
        ),
        rx.cond(
            State.is_searching,
            rx.el.div(
                rx.spinner(size="3", class_name="text-violet-600"),
                class_name="flex justify-center p-16 w-full",
            ),
            rx.cond(
                State.search_results.length() > 0,
                rx.el.div(
                    rx.foreach(State.search_results, product_card),
                    class_name="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 transition-all duration-300",
                ),
                rx.el.div(
                    rx.icon("search_x", class_name="w-16 h-16 text-gray-300"),
                    rx.el.p(
                        rx.cond(
                            State.search_query.length() > 0,
                            "No se encontraron productos para tu búsqueda.",
                            "Realiza una búsqueda para ver los resultados.",
                        ),
                        class_name="mt-4 text-gray-500 text-center",
                    ),
                    class_name="flex flex-col items-center justify-center p-16 bg-gray-50 rounded-lg w-full border border-dashed",
                ),
            ),
        ),
        class_name="w-full mt-4",
    )


def export_button() -> rx.Component:
    return rx.el.button(
        rx.icon("download", class_name="mr-2 h-4 w-4"),
        "Exportar a CSV",
        on_click=State.export_to_csv,
        class_name="flex items-center px-4 py-2 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors shadow-sm disabled:opacity-50",
        is_disabled=~(State.search_results.length() > 0),
    )


def special_families_management() -> rx.Component:
    return rx.cond(
        State.selected_family_id.is_not_none(),
        manage_skus_for_family_view(),
        manage_special_families_view(),
    )


def manage_special_families_view() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            "2. Gestionar Familias Especiales",
            class_name="text-lg font-semibold text-gray-700 mb-4",
        ),
        rx.el.form(
            rx.el.div(
                rx.el.input(
                    placeholder="Nombre de la nueva familia especial",
                    name="new_special_family_name",
                    class_name="flex-grow px-3 py-2 border rounded-l-md focus:outline-none focus:ring-violet-500",
                ),
                rx.el.button(
                    "Crear Familia",
                    type="submit",
                    class_name="px-4 py-2 bg-violet-600 text-white font-semibold rounded-r-md hover:bg-violet-700",
                ),
                class_name="flex",
            ),
            on_submit=State.create_special_family,
            reset_on_submit=True,
            class_name="mb-4",
        ),
        rx.el.div(
            rx.foreach(
                State.special_families,
                lambda family: rx.el.div(
                    rx.el.p(family["name"], class_name="font-medium text-gray-800"),
                    rx.el.div(
                        rx.el.button(
                            "Gestionar SKUs",
                            on_click=lambda: State.load_skus_for_family(family["id"]),
                            class_name="text-sm text-violet-600 hover:underline",
                        ),
                        rx.el.button(
                            rx.icon("trash-2", class_name="h-4 w-4"),
                            on_click=lambda: State.delete_special_family(family["id"]),
                            class_name="text-red-500 hover:text-red-700 p-1 rounded-md",
                        ),
                        class_name="flex items-center gap-4",
                    ),
                    class_name="flex justify-between items-center p-3 bg-gray-50 rounded-lg mb-2",
                ),
            ),
            class_name="space-y-2",
        ),
        class_name="p-4 border rounded-lg bg-white",
    )


def manage_skus_for_family_view() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.button(
                rx.icon("arrow-left", class_name="mr-2 h-4 w-4"),
                "Volver a Familias",
                on_click=State.clear_selected_family,
                class_name="flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4",
            ),
            rx.el.h3(
                "Gestionar SKUs de Familia",
                class_name="text-lg font-semibold text-gray-700 mb-4",
            ),
            class_name="flex items-center gap-4",
        ),
        rx.el.form(
            rx.el.div(
                rx.el.input(
                    placeholder="Añadir SKU a la familia...",
                    name="add_sku_to_family_sku",
                    class_name="flex-grow px-3 py-2 border rounded-l-md focus:outline-none focus:ring-violet-500",
                    on_mount=lambda: State.set_add_sku_to_family_id(
                        State.selected_family_id
                    ),
                ),
                rx.el.button(
                    "Añadir SKU",
                    type="submit",
                    class_name="px-4 py-2 bg-violet-600 text-white font-semibold rounded-r-md hover:bg-violet-700",
                ),
                class_name="flex",
            ),
            on_submit=State.add_sku_to_special_family,
            reset_on_submit=True,
            class_name="mb-4",
        ),
        rx.el.div(
            rx.foreach(
                State.special_family_skus,
                lambda sku: rx.el.div(
                    rx.el.p(sku["sku"], class_name="font-mono text-sm text-gray-800"),
                    rx.el.button(
                        rx.icon("x", class_name="h-4 w-4"),
                        on_click=lambda: State.remove_sku_from_family(sku["id"]),
                        class_name="text-gray-400 hover:text-red-600 p-1 rounded-full",
                    ),
                    class_name="flex justify-between items-center p-2 bg-gray-100 rounded-md",
                ),
            ),
            class_name="space-y-2 max-h-60 overflow-y-auto",
        ),
    )


def discontinued_sku_management() -> rx.Component:
    return rx.el.div(
        rx.el.h3(
            "3. Gestionar SKUs Descatalogados",
            class_name="text-lg font-semibold text-gray-700 mb-4",
        ),
        rx.el.form(
            rx.el.div(
                rx.el.input(
                    placeholder="SKU a descatalogar",
                    name="new_discontinued_sku",
                    class_name="flex-grow px-3 py-2 border rounded-l-md focus:outline-none focus:ring-violet-500",
                ),
                rx.el.button(
                    "Añadir",
                    type="submit",
                    class_name="px-4 py-2 bg-red-600 text-white font-semibold rounded-r-md hover:bg-red-700",
                ),
                class_name="flex mb-2",
            ),
            rx.el.input(
                placeholder="Razón (opcional)",
                name="new_discontinued_reason",
                class_name="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-violet-500",
            ),
            on_submit=State.add_discontinued_sku,
            reset_on_submit=True,
            class_name="mb-4",
        ),
        rx.el.div(
            rx.foreach(
                State.discontinued_skus,
                lambda sku: rx.el.div(
                    rx.el.div(
                        rx.el.p(
                            sku["sku"],
                            class_name="font-mono text-sm font-semibold text-gray-800",
                        ),
                        rx.el.p(sku["reason"], class_name="text-xs text-gray-500"),
                    ),
                    rx.el.button(
                        rx.icon("circle_x", class_name="h-5 w-5"),
                        on_click=lambda: State.remove_discontinued_sku(sku["id"]),
                        class_name="text-gray-400 hover:text-red-600 p-1 rounded-full",
                    ),
                    class_name="flex justify-between items-center p-3 bg-gray-50 rounded-lg mb-2",
                ),
            ),
            class_name="space-y-2 max-h-60 overflow-y-auto",
        ),
        class_name="p-4 border rounded-lg bg-white",
    )


def stat_card(icon: str, title: str, value: rx.Var, color_class: str) -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.icon(icon, class_name="h-8 w-8 " + color_class),
            class_name="p-3 bg-gray-100 rounded-lg",
        ),
        rx.el.div(
            rx.el.p(title, class_name="text-sm font-medium text-gray-500"),
            rx.el.p(value, class_name="text-2xl font-bold text-gray-800"),
            class_name="mt-2",
        ),
        class_name="flex items-center gap-4 bg-white p-4 rounded-xl border border-gray-200 shadow-sm",
    )


def dashboard_content() -> rx.Component:
    return rx.cond(
        State.is_loading_dashboard,
        rx.el.div(
            rx.spinner(size="3", class_name="text-violet-600"),
            class_name="flex justify-center p-16 w-full",
        ),
        rx.el.div(
            rx.el.div(
                rx.el.h2(
                    "Resumen de Inventario",
                    class_name="text-2xl font-bold text-gray-800",
                ),
                rx.el.button(
                    rx.icon("refresh-cw", class_name="w-4 h-4"),
                    on_click=State.load_dashboard_data,
                    class_name="p-2 text-gray-500 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors",
                ),
                class_name="flex justify-between items-center mb-6",
            ),
            rx.el.div(
                stat_card(
                    "package",
                    "Total Productos",
                    State.stats["total_products"].to_string(),
                    "text-blue-600",
                ),
                stat_card(
                    "boxes",
                    "Total Existencias",
                    State.stats["total_stock"].to_string(),
                    "text-green-600",
                ),
                stat_card(
                    "tags",
                    "Total Familias",
                    State.stats["family_count"].to_string(),
                    "text-yellow-600",
                ),
                stat_card(
                    "shield-alert",
                    "Bajo Stock (<20)",
                    State.stats["low_stock_count"].to_string(),
                    "text-red-600",
                ),
                class_name="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6",
            ),
            rx.el.div(
                rx.el.div(
                    rx.el.h3(
                        "Existencias por Familia",
                        class_name="text-xl font-semibold text-gray-800",
                    ),
                    rx.recharts.bar_chart(
                        rx.recharts.cartesian_grid(
                            stroke_dasharray="3 3", vertical=False
                        ),
                        rx.recharts.x_axis(data_key="name", hide=True),
                        rx.recharts.y_axis(width=80, tick_line=False, axis_line=False),
                        rx.recharts.tooltip(
                            cursor=False,
                            content_style={
                                "background": "#fff",
                                "border": "1px solid #ccc",
                            },
                        ),
                        rx.recharts.bar(
                            data_key="stock",
                            fill="var(--accent-9)",
                            radius=[4, 4, 0, 0],
                        ),
                        data=State.stock_by_family,
                        height=300,
                        margin={"left": 20},
                    ),
                    class_name="bg-white p-6 rounded-xl border border-gray-200 shadow-sm w-full lg:w-2/3",
                ),
                rx.el.div(
                    rx.el.h3(
                        "Productos con Bajo Stock",
                        class_name="text-xl font-semibold text-gray-800 mb-4",
                    ),
                    rx.cond(
                        State.low_stock_products.length() > 0,
                        rx.el.div(
                            rx.foreach(
                                State.low_stock_products,
                                lambda p: rx.el.div(
                                    rx.el.div(
                                        rx.el.p(
                                            p["sku"],
                                            class_name="font-semibold text-gray-700 text-sm",
                                        ),
                                        rx.el.p(
                                            p["description"],
                                            class_name="text-xs text-gray-500 whitespace-normal",
                                        ),
                                        class_name="flex-1",
                                    ),
                                    rx.el.span(
                                        p["current_stock"],
                                        class_name="ml-4 font-bold text-red-600 text-lg",
                                    ),
                                    class_name="flex items-center justify-between gap-4 py-3 border-b",
                                ),
                            ),
                            class_name="overflow-y-auto max-h-[250px] pr-2 space-y-1",
                        ),
                        rx.el.div(
                            rx.icon(
                                "square_check", class_name="w-12 h-12 text-green-500"
                            ),
                            rx.el.p(
                                "No hay productos con bajo stock.",
                                class_name="mt-2 text-gray-500",
                            ),
                            class_name="flex flex-col items-center justify-center h-full text-center",
                        ),
                    ),
                    class_name="bg-white p-6 rounded-xl border border-gray-200 shadow-sm lg:col-span-1",
                ),
                class_name="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6",
            ),
        ),
    )


def edit_product_dialog() -> rx.Component:
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.content(
            rx.radix.primitives.dialog.title(
                "Editar Producto", class_name="text-xl font-bold"
            ),
            rx.cond(
                State.editing_product.is_not_none(),
                rx.el.form(
                    rx.el.div(
                        rx.el.label(
                            "SKU", class_name="text-sm font-medium text-gray-700"
                        ),
                        rx.el.input(
                            default_value=State.editing_product["sku"],
                            class_name="w-full px-3 py-2 mt-1 border rounded-md bg-gray-100",
                            disabled=True,
                        ),
                        class_name="mb-4",
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Descripción",
                            class_name="text-sm font-medium text-gray-700",
                        ),
                        rx.el.input(
                            name="description",
                            default_value=State.editing_product["description"],
                            class_name="w-full px-3 py-2 mt-1 border rounded-md focus:outline-none focus:ring-violet-500",
                        ),
                        class_name="mb-4",
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Familia", class_name="text-sm font-medium text-gray-700"
                        ),
                        rx.el.input(
                            name="family",
                            default_value=State.editing_product["family"],
                            class_name="w-full px-3 py-2 mt-1 border rounded-md focus:outline-none focus:ring-violet-500",
                        ),
                        class_name="mb-4",
                    ),
                    rx.el.div(
                        rx.el.label(
                            "Existencia Actual",
                            class_name="text-sm font-medium text-gray-700",
                        ),
                        rx.el.input(
                            name="current_stock",
                            type="number",
                            default_value=State.editing_product[
                                "current_stock"
                            ].to_string(),
                            class_name="w-full px-3 py-2 mt-1 border rounded-md focus:outline-none focus:ring-violet-500",
                        ),
                        class_name="mb-4",
                    ),
                    rx.el.div(
                        rx.el.button(
                            "Cancelar",
                            on_click=State.close_edit_dialog,
                            color_scheme="gray",
                            variant="soft",
                            class_name="cursor-pointer",
                        ),
                        rx.el.button(
                            "Guardar Cambios",
                            type="submit",
                            class_name="px-4 py-2 bg-violet-600 text-white font-semibold rounded-md hover:bg-violet-700",
                        ),
                        class_name="flex justify-end gap-3 mt-6",
                    ),
                    on_submit=State.update_product,
                    reset_on_submit=False,
                ),
            ),
            class_name="max-w-lg",
        ),
        open=State.show_edit_dialog,
        on_open_change=State.set_show_edit_dialog,
    )


def delete_product_dialog() -> rx.Component:
    return rx.radix.primitives.dialog.root(
        rx.radix.primitives.dialog.content(
            rx.radix.primitives.dialog.title(
                "Confirmar Eliminación", class_name="text-xl font-bold text-red-600"
            ),
            rx.radix.primitives.dialog.description(
                "¿Estás seguro de que quieres eliminar el producto con SKU: "
                + State.product_to_delete_sku
                + "? Esta acción no se puede deshacer.",
                class_name="text-gray-600 mt-2 mb-6",
            ),
            rx.el.div(
                rx.el.button(
                    "Cancelar",
                    on_click=State.close_delete_dialog,
                    color_scheme="gray",
                    variant="soft",
                    class_name="cursor-pointer",
                ),
                rx.el.button(
                    "Eliminar Producto",
                    on_click=State.delete_product,
                    class_name="px-4 py-2 bg-red-600 text-white font-semibold rounded-md hover:bg-red-700",
                ),
                class_name="flex justify-end gap-3 mt-4",
            ),
            class_name="max-w-md",
        ),
        open=State.show_delete_dialog,
        on_open_change=State.set_show_delete_dialog,
    )