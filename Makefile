.PHONY: install run test lint clean

install:
	pip install -r requirements.txt

run:
	python -m pipeline.run_pipeline

test:
	pytest tests/ -v

lint:
	ruff check pipeline/ tests/

clean:
	rm -rf data/staging/* data/warehouse/* data/mart/* logs/* .pytest_cache/ __pycache__/ pipeline/**/__pycache__/

check-warehouse:
	python scripts/check_warehouse_output.py
