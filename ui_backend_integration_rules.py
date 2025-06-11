from dataclasses import dataclass
from importlib import import_module
from typing import List

@dataclass(frozen=True)
class UIMapping:
    """Represent a mapping between a UI event and a backend method."""
    ui_event: str
    backend_target: str

# Ordered list of rules mapping UI events to backend callables
UI_BACKEND_RULES: List[UIMapping] = [
    # Collector card buttons to collectors tab methods
    UIMapping("CollectorCard.start_requested", "CollectorsTab.start_collection"),
    UIMapping("CollectorCard.stop_requested", "CollectorsTab.stop_collection"),
    UIMapping(
        "CollectorCard.configure_requested",
        "CollectorsTab.configure_collector",
    ),
    UIMapping("CollectorCard.logs_requested", "CollectorsTab.show_logs"),

    # Collectors tab start/stop buttons to wrapper methods
    UIMapping("CollectorsTab.start_collection", "BaseWrapper.start"),
    UIMapping("CollectorsTab.stop_collection", "BaseWrapper.stop"),

    # Processor start buttons to wrapper batch methods
    UIMapping(
        "ProcessorsTab.pdf_start_btn", "PDFExtractorWrapper.start_batch_processing",
    ),
    UIMapping(
        "ProcessorsTab.text_start_btn",
        "TextExtractorWrapper.start_batch_processing",
    ),
    UIMapping(
        "ProcessorsTab.batch_start_btn",
        "CorpusBalancerWrapper.start_balancing",
    ),

    # Dashboard quick actions
    UIMapping(
        "DashboardTab.start_corpus_optimization",
        "CorpusBalancerWrapper.start_balancing",
    ),
    UIMapping(
        "DashboardTab.start_all_collectors",
        "CollectorsTab.start_collection",
    ),
    UIMapping("DashboardTab.export_report", "generate_corpus_report.main"),
    UIMapping(
        "DashboardTab.update_dependencies",
        "DependencyUpdateService.start_update",
    ),
    UIMapping(
        "DashboardTab.rebalance_now_btn",
        "CryptoCorpusMainWindow.on_rebalance_requested",
    ),
    UIMapping(
        "DashboardTab.view_all_btn",
        "CryptoCorpusMainWindow.show_full_activity_tab",
    ),
]

# Map top-level class names to import paths used for validation
MODULE_MAP = {
    "CollectorCard": "app.ui.widgets.collector_card",
    "CollectorsTab": "app.ui.tabs.collectors_tab",
    "ProcessorsTab": "app.ui.tabs.processors_tab",
    "DashboardTab": "app.ui.tabs.dashboard_tab",
    "CryptoCorpusMainWindow": "app.main_window",
    "PDFExtractorWrapper": "shared_tools.ui_wrappers.processors.pdf_extractor_wrapper",
    "TextExtractorWrapper": "shared_tools.ui_wrappers.processors.text_extractor_wrapper",
    "CorpusBalancerWrapper": "shared_tools.ui_wrappers.processors.corpus_balancer_wrapper",
    "BaseWrapper": "shared_tools.ui_wrappers.base_wrapper",
    "DependencyUpdateService": "shared_tools.services.dependency_update_service",
    "generate_corpus_report": "shared_tools.utils.generate_corpus_report",
}


def _resolve(class_name: str):
    """Import class by name using MODULE_MAP."""
    mod_name = MODULE_MAP.get(class_name)
    if not mod_name:
        raise ImportError(f"No module mapping for {class_name}")
    module = import_module(mod_name)
    obj = getattr(module, class_name.split(".")[-1], None)
    if obj is None:
        raise AttributeError(f"{class_name} not found in {mod_name}")
    return obj


def validate_ui_backend_rules() -> None:
    """Ensure each UI event points to a valid callable backend attribute."""
    errors = []
    for rule in UI_BACKEND_RULES:
        ui_cls_name, ui_attr = rule.ui_event.split(".")
        backend_cls_name, backend_attr = rule.backend_target.split(".")

        try:
            ui_cls = _resolve(ui_cls_name)
        except Exception as exc:  # pragma: no cover - defensive
            errors.append(f"{ui_cls_name} missing: {exc}")
            continue
        if not hasattr(ui_cls, ui_attr):
            errors.append(f"{ui_cls_name} missing attribute {ui_attr}")
            continue

        try:
            backend_cls = _resolve(backend_cls_name)
        except Exception as exc:  # pragma: no cover - defensive
            errors.append(f"{backend_cls_name} missing: {exc}")
            continue

        if not hasattr(backend_cls, backend_attr):
            errors.append(
                f"{backend_cls_name} missing attribute {backend_attr}")
            continue

        attr = getattr(backend_cls, backend_attr)
        if not callable(attr) and not hasattr(attr, "emit"):
            errors.append(
                f"{backend_cls_name}.{backend_attr} is not callable or signal")

    if errors:
        raise AssertionError(
            "UI backend integration validation failed:\n" + "\n".join(errors)
        )


if __name__ == "__main__":
    validate_ui_backend_rules()
    print("\u2705 UI–backend rules validated.")
