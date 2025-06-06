import argparse
import logging
from typing import List

from shared_tools.project_config import ProjectConfig
from shared_tools.ui_wrappers.wrapper_factory import (
    create_collector_wrapper,
    create_processor_wrapper,
)
from shared_tools.ui_wrappers.processors.corpus_balancer_wrapper import CorpusBalancerWrapper


logger = logging.getLogger(__name__)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute pipeline components configured in a ProjectConfig YAML"
    )
    parser.add_argument("--config", required=True, help="Path to ProjectConfig YAML")
    parser.add_argument("--run-all", action="store_true", help="Run collectors, processors and balancer")
    parser.add_argument("--collect", action="store_true", help="Run enabled collectors")
    parser.add_argument("--extract", action="store_true", help="Run enabled processors")
    parser.add_argument("--balance", action="store_true", help="Run corpus balancer")
    return parser.parse_args(argv)


def load_config(path: str) -> ProjectConfig:
    return ProjectConfig.from_yaml(path)


def enabled_modules(config: ProjectConfig, section: str) -> List[str]:
    modules = config.get(section, {}) or {}
    return [name for name, cfg in modules.items() if isinstance(cfg, dict) and cfg.get("enabled", False)]


def run_collectors(config: ProjectConfig, names: List[str]):
    if not names:
        raise RuntimeError("No enabled collectors found in configuration")
    for name in names:
        logger.info("Running collector: %s", name)
        wrapper = create_collector_wrapper(name, config)
        wrapper.start()
        if getattr(wrapper, "worker", None):
            wrapper.worker.wait()
        logger.info("Collector %s finished", name)


def run_processors(config: ProjectConfig, names: List[str]):
    if not names:
        raise RuntimeError("No enabled processors found in configuration")
    for name in names:
        wrapper_name = "text" if name in {"nonpdf", "text"} else name
        logger.info("Running processor: %s", wrapper_name)
        wrapper = create_processor_wrapper(wrapper_name, config)
        wrapper.start()
        if getattr(wrapper, "worker", None):
            wrapper.worker.wait()
        logger.info("Processor %s finished", wrapper_name)


def run_balancer(config: ProjectConfig):
    enabled = config.get("processors.corpus_balancer.enabled", False) or config.get(
        "corpus_balancer.enabled", False
    )
    if not enabled:
        raise RuntimeError("Corpus balancer not enabled in configuration")
    logger.info("Running corpus balancer")
    balancer = CorpusBalancerWrapper(config)
    balancer.start_balancing()
    if getattr(balancer, "worker", None):
        balancer.worker.wait()
    logger.info("Corpus balancer completed")


def main(argv: List[str] | None = None):
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    config = load_config(args.config)

    run_collect = args.run_all or args.collect
    run_extract = args.run_all or args.extract
    run_balance = args.run_all or args.balance

    if not any([run_collect, run_extract, run_balance]):
        raise RuntimeError("No phases selected to run")

    if run_collect:
        collectors = enabled_modules(config, "collectors")
        run_collectors(config, collectors)

    if run_extract:
        processors = enabled_modules(config, "extractors") or enabled_modules(config, "processors")
        # remove corpus_balancer if present
        processors = [p for p in processors if p != "corpus_balancer"]
        run_processors(config, processors)

    if run_balance:
        run_balancer(config)


if __name__ == "__main__":
    main()

# Example usage:
# python cli/execute_from_config.py --config examples/project_config.yaml --run-all
