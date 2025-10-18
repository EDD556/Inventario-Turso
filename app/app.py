import reflex as rx
from . import state, components


def query_view() -> rx.Component:
    return rx.el.div(
        rx.el.div(
            rx.el.h2(
                "Consultar Existencias",
                class_name="text-xl font-semibold text-gray-700 mb-4",
            ),
            components.search_interface(),
            class_name="w-full",
        ),
        rx.el.div(components.export_button(), class_name="flex justify-end mt-4"),
        components.results_display(),
        class_name="mt-8",
    )


def dashboard_view() -> rx.Component:
    return rx.el.div(components.dashboard_content(), class_name="mt-8")


def index() -> rx.Component:
    return rx.el.main(
        rx.el.div(
            rx.el.div(
                rx.el.div(
                    rx.icon("box-select", class_name="h-10 w-10 text-violet-600"),
                    rx.el.h1(
                        "Sistema de Consulta de Existencias",
                        class_name="text-3xl font-bold text-gray-800",
                    ),
                    class_name="flex items-center gap-4",
                ),
                rx.el.p(
                    "Panel de control para la gestión y consulta de inventario.",
                    class_name="text-gray-600 mt-2",
                ),
                rx.el.button(
                    rx.icon("settings", class_name="w-4 h-4 mr-2"),
                    "Configuración",
                    on_click=state.State.toggle_config_dialog,
                    class_name="absolute top-6 right-6 flex items-center px-4 py-2 bg-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-300 transition-colors",
                ),
                class_name="relative",
            ),
            components.config_dialog(),
            components.edit_product_dialog(),
            components.delete_product_dialog(),
            rx.el.div(
                rx.el.button(
                    rx.icon("search", class_name="w-4 h-4 mr-2"),
                    "Consulta",
                    on_click=lambda: state.State.set_active_tab("query"),
                    class_name=rx.cond(
                        state.State.active_tab == "query",
                        "flex items-center px-4 py-2 bg-violet-600 text-white font-semibold rounded-t-lg transition-colors",
                        "flex items-center px-4 py-2 bg-gray-200 text-gray-700 font-medium rounded-t-lg hover:bg-gray-300 transition-colors",
                    ),
                ),
                rx.el.button(
                    rx.icon("layout-dashboard", class_name="w-4 h-4 mr-2"),
                    "Dashboard",
                    on_click=lambda: state.State.set_active_tab("dashboard"),
                    class_name=rx.cond(
                        state.State.active_tab == "dashboard",
                        "flex items-center px-4 py-2 bg-violet-600 text-white font-semibold rounded-t-lg transition-colors",
                        "flex items-center px-4 py-2 bg-gray-200 text-gray-700 font-medium rounded-t-lg hover:bg-gray-300 transition-colors",
                    ),
                ),
                class_name="flex border-b-2 border-violet-600 mt-8",
            ),
            rx.el.div(
                rx.cond(
                    state.State.active_tab == "query", query_view(), dashboard_view()
                ),
                class_name="bg-white p-6 rounded-b-xl rounded-tr-xl shadow-[0_4px_10px_rgba(0,0,0,0.05)]",
            ),
            class_name="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8",
        ),
        class_name="font-['Inter'] bg-gray-50 min-h-screen",
        on_mount=state.State.on_load,
    )


app = rx.App(
    theme=rx.theme(appearance="light", accent_color="violet", radius="medium"),
    head_components=[
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(rel="preconnect", href="https://fonts.gstatic.com", cross_origin=""),
        rx.el.link(
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",
            rel="stylesheet",
        ),
    ],
)
app.add_page(index)