.PHONY: run test lint clean docker-build

run:
	python main.py

test:
	python -m unittest discover -s tests

lint:
	flake8 src main.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build:
	docker build -t smart-chess:latest .
