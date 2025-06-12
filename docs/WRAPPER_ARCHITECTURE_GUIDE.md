# Wrapper Architecture Guide

## Overview
This guide describes the **robust, explicit, and Qt-compliant architecture** for all UI processor wrappers in this project. It ensures:
- Maximum compatibility with PySide6/Qt
- No multiple inheritance or mixin magic
- All required methods, properties, and signals are preserved and exposed
- Easy portability and maintainability

## Hard Rules
1. **Inherit ONLY from `QWidget`** (or the appropriate Qt base class for your UI component).
2. **No `BaseWrapper`, no `ProcessorMixin`, no multiple inheritance.**
3. **No `super()` calls**—use explicit base class initializers if needed.
4. **Use composition for any processor/mixin logic.**
5. **Store and use `ProjectConfig` directly.**
6. **Explicitly delegate every method, property, and signal needed by the UI or external code.**
7. **All UI setup must be in a `setup_ui()` method, called from the constructor.**
8. **No hardcoded paths—use `ProjectConfig` for all environment/config needs.**
9. **No magic: no `__getattr__`, no automatic delegation, no inheritance tricks.**

## Safe Migration Process
**How to migrate an old wrapper to the new pattern:**

1. **List all methods, properties, and signals you need on the wrapper** (look at the old class and its bases).
2. **For each, add an explicit delegation or connection in the new wrapper.**
3. **Copy all UI setup code and call it in the constructor.**
4. **Test thoroughly.**

## Example Template
See `wrapper_template.py` for a ready-to-use template. Example:
```python
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal
# from shared_tools.processors.YOUR_PROCESSOR import YourProcessor

class YourProcessorWrapper(QWidget):
    example_signal = Signal(str)
    def __init__(self, project_config, parent=None, **kwargs):
        QWidget.__init__(self, parent)
        if project_config is None:
            raise RuntimeError("YourProcessorWrapper requires a non-None ProjectConfig")
        self.project_config = project_config
        # self._processor = YourProcessor(project_config=project_config)
        self._is_running = False
        self.worker_thread = None
        self.setup_ui()
    @property
    def config(self):
        return self._processor.config
    def start(self, *args, **kwargs):
        self._is_running = True
        if hasattr(self._processor, 'start'):
            return self._processor.start(*args, **kwargs)
        return None
    def setup_ui(self):
        layout = QVBoxLayout(self)
        # Add your UI components here
```

## Action Plan for All Wrappers
1. **Apply the template to every wrapper.**
2. **Remove all multiple inheritance and mixins.**
3. **Delegate all required signals, properties, and methods explicitly.**
4. **Test each wrapper in isolation and in the full app.**

## Developer Checklist
- [ ] Inherit only from QWidget
- [ ] No BaseWrapper or ProcessorMixin
- [ ] No super() calls
- [ ] All signals, properties, and methods needed by UI/external code are present and delegated
- [ ] All config is via ProjectConfig
- [ ] UI setup is explicit
- [ ] No hardcoded paths
- [ ] No magic delegation

## Troubleshooting
- **Missing signals/methods:** Add explicit delegation.
- **Config errors:** Ensure you pass a real ProjectConfig, not a dict or None.
- **Qt errors:** Check inheritance and initializer order—always QWidget only.
- **Path issues:** Use ProjectConfig for all paths.
- **Legacy code:** Remove all references to BaseWrapper, ProcessorMixin, and super().

## How to Verify Correctness
- Run all unit and integration tests.
- Manually test the UI for each wrapper.
- Check that all signals, methods, and properties are available and work as expected.

## Summary
**This pattern is robust, explicit, and future-proof.**
- No more inheritance headaches.
- All business logic is delegated, not inherited.
- UI and processor logic are cleanly separated.
- Easy to maintain and extend.

**Apply this to every wrapper for a stable, portable, and maintainable codebase!**

**Yes, I can confirm that the rewritten `QualityControlWrapper` preserves all the methods, properties, and signals you need on the wrapper, as per your requirements and the comprehensive list you provided.**

---

### **What is Preserved and Explicitly Delegated:**

#### **Signals**
- `quality_score_calculated`
- `status_updated`
- `progress_updated`
- `batch_completed`
- `error_occurred`

#### **Properties**
- `config`
- `logger`
- `task_history_service`
- `activity_log_service`
- `_task_id` (with getter/setter)
- `task_queue_manager` (with getter/setter)
- `target` (with getter/setter)
- `_progress` (with getter/setter)
- `_test_mode` (with getter/setter)
- `is_running` (with getter/setter, now local to the wrapper)
- `worker_thread` (local attribute)
- `quality_threshold` (local attribute)

#### **Methods**
- `start`
- `stop`
- `get_status`
- `set_test_mode`
- `refresh_config`
- `get_processing_stats`
- `process_batch`
- (Any other processor methods can be delegated in the same way if needed)

#### **UI Setup**
- `setup_ui` is present and called in the constructor.

---

### **No Magic, No Mixins**
- There is **no `ProcessorMixin`**, **no `BaseWrapper`**, and **no automatic delegation**.
- All delegation is explicit and local to the wrapper.

---

### **How to Add More**
If you need to expose or delegate any additional methods, properties, or signals, you can do so by following the same explicit pattern used in the current wrapper.

---

### **Summary Table**

| Type      | Name(s) Preserved/Delegated                |
|-----------|--------------------------------------------|
| Signals   | quality_score_calculated, status_updated, progress_updated, batch_completed, error_occurred |
| Properties| config, logger, task_history_service, activity_log_service, _task_id, task_queue_manager, target, _progress, _test_mode, is_running, worker_thread, quality_threshold |
| Methods   | start, stop, get_status, set_test_mode, refresh_config, get_processing_stats, process_batch |
| UI        | setup_ui                                   |

---

**If you have a specific method, property, or signal you want to double-check, just name it and I'll confirm its presence and delegation. But as per your requirements and the migration plan, everything you listed is preserved and explicit.**

Let me know if you want to review or add anything else!

WRAPPERS AUDIT

Ran tool
Ran tool
Read file: CorpusBuilderApp/shared_tools/ui_wrappers/processors/domain_classifier_wrapper.py
Read file: CorpusBuilderApp/shared_tools/ui_wrappers/processors/language_confidence_detector_wrapper.py
Read file: CorpusBuilderApp/shared_tools/ui_wrappers/processors/financial_symbol_processor_wrapper.py
Read file: CorpusBuilderApp/shared_tools/ui_wrappers/processors/machine_translation_detector_wrapper.py
Read file: CorpusBuilderApp/shared_tools/ui_wrappers/processors/formula_extractor_wrapper.py
Here is the **audit summary** for the main UI processor wrappers in your system, with a focus on whether they need migration to the new architecture and why:

---

## **Wrappers That Need Migration**

### 1. **DomainClassifierWrapper**
- **Current Inheritance:** `QWidget`, but also uses `ProcessorMixin` and delegates via `_bw`.
- **Why Migrate:** Uses `ProcessorMixin` (forbidden), delegates via mixin magic, not explicit, not robust.
- **Action:** **Migrate** to single-inheritance `QWidget`, explicit delegation, config via `ProjectConfig`.

---

### 2. **LanguageConfidenceDetectorWrapper**
- **Current Inheritance:** `BaseWrapper, QWidget`
- **Why Migrate:** Uses `BaseWrapper` (forbidden), multiple inheritance, magic delegation.
- **Action:** **Migrate** to single-inheritance `QWidget`, explicit delegation, config via `ProjectConfig`.

---

### 3. **FinancialSymbolProcessorWrapper**
- **Current Inheritance:** `BaseWrapper, QWidget`
- **Why Migrate:** Uses `BaseWrapper` (forbidden), multiple inheritance, magic delegation.
- **Action:** **Migrate** to single-inheritance `QWidget`, explicit delegation, config via `ProjectConfig`.

---

### 4. **MachineTranslationDetectorWrapper**
- **Current Inheritance:** `BaseWrapper, QWidget`
- **Why Migrate:** Uses `BaseWrapper` (forbidden), multiple inheritance, magic delegation.
- **Action:** **Migrate** to single-inheritance `QWidget`, explicit delegation, config via `ProjectConfig`.

---

### 5. **FormulaExtractorWrapper**
- **Current Inheritance:** `BaseWrapper, QWidget`
- **Why Migrate:** Uses `BaseWrapper` (forbidden), multiple inheritance, magic delegation.
- **Action:** **Migrate** to single-inheritance `QWidget`, explicit delegation, config via `ProjectConfig`.

---

## **General Pattern in Other Wrappers**
- **If a wrapper inherits from `BaseWrapper`, `ProcessorMixin`, or uses multiple inheritance:**  
  **It must be migrated.**
- **If a wrapper uses only `QWidget` and delegates everything explicitly:**  
  **No migration needed.**

---

## **Hard Rules for Migration**
- **Inherit only from `QWidget`**
- **No `BaseWrapper`, no `ProcessorMixin`, no multiple inheritance**
- **No `super()` calls**
- **Explicitly delegate all signals, properties, and methods**
- **Config must be via `ProjectConfig`**
- **No magic delegation or `__getattr__`**
- **All UI setup in `setup_ui()`**

---

## **Wrappers That May Not Need Migration**
- If you have wrappers that already:
  - Inherit only from `QWidget`
  - Do not use `BaseWrapper` or `ProcessorMixin`
  - Delegate all signals, properties, and methods explicitly
  - Use `ProjectConfig` for config
  - Have all UI setup in `setup_ui()`
- **Then they do not need migration.**
- **Example:** The newly rewritten `QualityControlWrapper` is already compliant.

---

## **Summary Table**

| Wrapper Name                        | Needs Migration? | Reason                                                                 |
|--------------------------------------|------------------|------------------------------------------------------------------------|
| QualityControlWrapper                | NO               | Already migrated, explicit, single-inheritance, config via ProjectConfig|
| DomainClassifierWrapper              | YES              | Uses ProcessorMixin, not explicit, not robust                          |
| LanguageConfidenceDetectorWrapper    | YES              | Uses BaseWrapper, multiple inheritance, not explicit                   |
| FinancialSymbolProcessorWrapper      | YES              | Uses BaseWrapper, multiple inheritance, not explicit                   |
| MachineTranslationDetectorWrapper    | YES              | Uses BaseWrapper, multiple inheritance, not explicit                   |
| FormulaExtractorWrapper              | YES              | Uses BaseWrapper, multiple inheritance, not explicit                   |
| (Others with BaseWrapper/ProcessorMixin) | YES          | Same reasons as above                                                  |
| (Wrappers with only QWidget, explicit delegation) | NO | Already compliant                                                      |

---

## **What to Do Next**
- **Migrate all wrappers that use `BaseWrapper`, `ProcessorMixin`, or multiple inheritance.**
- **For each, follow the template and rules in `WRAPPER_ARCHITECTURE_GUIDE.md`.**
- **Preserve all methods, properties, and signals needed by the UI or external code.**

---

If you want a **full, file-by-file migration checklist** or want to audit additional wrappers (e.g., `deduplicator_wrapper.py`, `chart_image_extractor_wrapper.py`, etc.), let me know and I’ll continue the audit for those files as well!