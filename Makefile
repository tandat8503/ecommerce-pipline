# Ecommerce Pipeline — Quick Commands

.PHONY: setup run test lint format push

setup:
	pip install -r requirements.txt

run:
	python pipeline/run_pipeline.py

test:
	pytest tests/ -v

lint:
	ruff check pipeline/ tests/

format:
	ruff format pipeline/ tests/

push:
	git add .
	git commit -m "$(msg)"
	git push origin main
