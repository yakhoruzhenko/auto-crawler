buid: ## build
	docker compose build crawler

up: ## up
	docker compose up crawler

clean: ## clean
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -f .coverage

down: ## down
	docker compose down

down-v: ## down and remove all existing volumes
	docker compose down -v

lint: ## lint
	docker compose run --rm review-app-dev sh -c " \
		flake8 . && \
		isort --check --diff . && \
		mypy ." && \
		yamllint .

sec: ## runs security tests
	docker compose run --rm review-app-dev bandit -r .

checks: lint sec ## run all static checks
	
# Absolutely awesome: https://marmelab.com/check/2016/02/29/auto-documented-makefile.html
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
