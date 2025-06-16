from __future__ import annotations

"""AutoBalanceDaemon – headless/background loop for corpus rebalancing.

It reuses existing CorpusBalancer logic but avoids Qt dependencies so it can
run on servers without the GUI. The loop is controlled by the `auto_balance`
block inside any valid ProjectConfig YAML.

Usage (once-off preview):

    python -m shared_tools.services.auto_balance_daemon \
           --config path/to/project.yaml --once --preview-only

Regular background run:

    python -m shared_tools.services.auto_balance_daemon --config proj.yaml

The daemon creates a PID lock-file (`logs/auto_balance.pid`) to prevent
multiple concurrent instances using the same config.
"""

from pathlib import Path
import argparse
import json
import logging
import os
import sys
import time
import signal
from typing import List, Dict, Any, Optional
import threading
try:
    from flask import Flask, jsonify, request
except ImportError:  # pragma: no cover – Flask optional
    Flask = None  # type: ignore

from shared_tools.project_config import ProjectConfig  # type: ignore
from shared_tools.processors.corpus_balancer import CorpusBalancer  # type: ignore
from shared_tools.ui_wrappers.wrapper_factory import create_collector_wrapper  # type: ignore
from cli.execute_from_config import enabled_modules  # type: ignore  # reuse helper

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper: basic stdout logger when run as standalone module
# ---------------------------------------------------------------------------
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


class AutoBalanceDaemon:
    """Headless loop that analyses corpus balance and triggers collectors."""

    def __init__(self, cfg: ProjectConfig, preview_only: bool = False):
        self.cfg = cfg
        self.preview = preview_only
        self.thresholds = {
            "dominance_ratio": float(cfg.get("auto_balance.dominance_ratio", 5.0)),
            "min_entropy": float(cfg.get("auto_balance.min_entropy", 2.0)),
            "check_interval": int(cfg.get("auto_balance.check_interval", 900)),
        }
        self.start_balancing = bool(cfg.get("auto_balance.start_balancing", False))
        self.logs_dir = cfg.get_logs_dir()
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.pid_file = self.logs_dir / "auto_balance.pid"
        self._write_pid_file()

        # REST server state
        self._rest_thread: Optional[threading.Thread] = None
        self._last_result: Dict[str, Any] = {}

        rest_enabled = bool(cfg.get("auto_balance.rest_enabled", False))
        if rest_enabled and Flask is None:
            logger.warning("auto_balance.rest_enabled is true but Flask not installed – REST API disabled")
        if rest_enabled and Flask is not None:
            self._port = int(cfg.get("auto_balance.rest_port", 8799))
            self._auth_token = str(cfg.get("auto_balance.auth_token", ""))
            self._start_rest_server()

    # ------------------------------------------------------------------
    def _write_pid_file(self):
        if self.pid_file.exists():
            try:
                existing_pid = int(self.pid_file.read_text().strip())
                # If process still alive, refuse to start second instance
                if existing_pid and existing_pid != os.getpid() and self._pid_alive(existing_pid):
                    raise RuntimeError(f"AutoBalanceDaemon already running with PID {existing_pid}")
            except Exception:
                # stale / unreadable file – overwrite
                pass
        self.pid_file.write_text(str(os.getpid()))

    # ------------------------------------------------------------------
    @staticmethod
    def _pid_alive(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    def _cleanup(self):
        try:
            if self.pid_file.exists():
                self.pid_file.unlink()
        except Exception:
            pass

    # ------------------------------------------------------------------
    def run_once(self) -> Dict[str, Any]:
        """Run one analyse→collect→(optional)balance cycle."""
        logger.info("Starting auto-balance cycle (preview=%s)", self.preview)

        balancer = CorpusBalancer(self.cfg)
        analysis = balancer.analyzer.analyze_corpus_balance(force_refresh=True)
        domain_info = analysis.get("domain_analysis", {}) if isinstance(analysis, dict) else {}
        missing = domain_info.get("missing_domains", []) or []
        dominance_ratio = float(domain_info.get("dominance_ratio", 1.0))
        entropy = float(domain_info.get("entropy", 10.0))

        logger.info("Corpus dominance_ratio=%.2f entropy=%.2f missing_domains=%s", dominance_ratio, entropy, missing)

        actions: Dict[str, Any] = {"collect_triggered": False, "balance_triggered": False}

        imbalance = (missing or dominance_ratio > self.thresholds["dominance_ratio"] or entropy < self.thresholds["min_entropy"])

        if imbalance:
            # ------------------------------------------------------------------
            # Trigger collectors for missing domains
            # ------------------------------------------------------------------
            if missing:
                logger.info("Triggering collectors for domains: %s", ", ".join(missing))
                actions["collect_triggered"] = self._run_collectors_for_domains(missing)
            else:
                logger.info("Imbalance detected (dominance_ratio or entropy), but no explicit missing domains")

            # ------------------------------------------------------------------
            # Optionally run the balancer (non-dry run) after collection stage
            # ------------------------------------------------------------------
            if self.start_balancing:
                if self.preview:
                    logger.info("[preview] Would run balancer in execute mode")
                else:
                    result = balancer.rebalance(strategy="quality_weighted", dry_run=False)
                    actions["balance_triggered"] = True
                    logger.info("Balancer executed – plan_id=%s", result.get("plan_id"))
        else:
            logger.info("Corpus within balance thresholds – nothing to do.")

        # Dump summary JSON
        def _convert(obj):  # local helper mimics cli.execute_from_config
            if isinstance(obj, dict):
                # Ensure keys are strings
                return {str(k): _convert(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_convert(v) for v in obj]
            import numpy as _np  # local import to avoid global dependency issues
            import datetime as _dt
            if isinstance(obj, (_np.integer,)):
                return int(obj)
            if isinstance(obj, (_np.floating,)):
                return float(obj)
            if isinstance(obj, (_dt.date, _dt.datetime)):
                return obj.isoformat()
            return obj

        summary_path = self.logs_dir / "auto_balance_last_result.json"
        with open(summary_path, "w", encoding="utf-8") as fh:
            json.dump(_convert({"analysis": analysis, "actions": actions}), fh, indent=2)

        # keep in memory for REST /status
        self._last_result = _convert({"analysis": analysis, "actions": actions})

        return {"analysis": analysis, "actions": actions}

    # ------------------------------------------------------------------
    def _run_collectors_for_domains(self, domains: List[str]) -> bool:
        """Run all enabled collectors, biasing them toward the supplied domains."""
        names = enabled_modules(self.cfg, "collectors")
        if not names:
            logger.warning("No enabled collectors found – skipping collection stage")
            return False

        any_started = False
        for name in names:
            try:
                wrapper = create_collector_wrapper(name, self.cfg)
                # If wrapper supports search-term injection, append domains
                if domains and hasattr(wrapper, "set_search_terms"):
                    existing = getattr(wrapper, "search_terms", []) or []
                    for dom in domains:
                        if dom not in existing:
                            existing.append(dom)
                    try:
                        wrapper.set_search_terms(existing)
                    except Exception:
                        pass
                if self.preview:
                    logger.info("[preview] Would run collector %s", name)
                    continue
                wrapper.start()
                if getattr(wrapper, "worker", None):
                    wrapper.worker.wait()
                any_started = True
                logger.info("Collector %s finished", name)
            except Exception as exc:
                logger.warning("Collector %s failed: %s", name, exc)
        return any_started

    # ------------------------------------------------------------------
    def run_loop(self, once: bool = False):
        try:
            while True:
                self.run_once()
                if once:
                    break
                time.sleep(self.thresholds["check_interval"])
        finally:
            self._cleanup()

    # ------------------------------------------------------------------
    # REST server helpers
    # ------------------------------------------------------------------
    def _start_rest_server(self):
        """Launch a background Flask app for control/status."""
        app = Flask("auto_balance_daemon")  # type: ignore

        @app.before_request
        def _check_token():  # pragma: no cover
            if not self._auth_token:
                return  # open
            token = request.headers.get("X-AUTH-TOKEN") or request.args.get("token")
            if token != self._auth_token:
                return ("Forbidden", 403)

        @app.route("/status", methods=["GET"])
        def _status():  # pragma: no cover
            return jsonify({
                "pid": os.getpid(),
                "thresholds": self.thresholds,
                "start_balancing": self.start_balancing,
                "preview": self.preview,
                "last_result": self._last_result,
            })

        @app.route("/control", methods=["POST", "PATCH"])
        def _control():  # pragma: no cover
            data = request.get_json(force=True, silent=True) or {}
            if "start_balancing" in data:
                self.start_balancing = bool(data["start_balancing"])
            return jsonify({"start_balancing": self.start_balancing})

        def _run():  # pragma: no cover
            app.run(host="0.0.0.0", port=self._port, threaded=True, use_reloader=False)

        self._rest_thread = threading.Thread(target=_run, daemon=True)
        self._rest_thread.start()


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def _parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Headless auto-balance daemon")
    p.add_argument("--config", required=True, help="Path to ProjectConfig YAML")
    p.add_argument("--once", action="store_true", help="Run a single cycle and exit")
    p.add_argument("--preview-only", action="store_true", help="Dry-run collectors and balancer")
    p.add_argument("--rest", action="store_true", help="Expose REST control endpoint (requires Flask). Overrides auto_balance.rest_enabled flag.")
    return p.parse_args(argv)


def main(argv: List[str] | None = None):
    args = _parse_args(argv)

    cfg = ProjectConfig(args.config)
    # Override rest_enabled if --rest provided
    if args.rest:
        cfg.set("auto_balance.rest_enabled", True)
    daemon = AutoBalanceDaemon(cfg, preview_only=args.preview_only)
    daemon.run_loop(once=args.once)


if __name__ == "__main__":
    main() 