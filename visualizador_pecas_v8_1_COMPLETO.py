"""Entrypoint compatível da versão 8.1 modularizada."""

from inventory_viewer.core import (
    StructuredLogger,
    JSONFormatter,
    ReadableFormatter,
    ConfigManager,
    ThreadState,
    DirectoryCache,
    ParallelImageLoader,
    BuscadorService,
    ThreadManager,
)
from inventory_viewer.ui import VisualizadorPecas, run_app


if __name__ == "__main__":
    run_app()
