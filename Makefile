# Package Management
install_poetry:
	@poetry --version || pip install poetry

deps:
	@echo "Installing dependencies"
	poetry lock
	poetry install

freeze:
	@echo "Freezing dependencies"
	poetry export -f requirements.txt --output requirements.txt --without-hashes

# Infrastructure

deploy_infra:
	@echo "Applying changes to Infrastructure"
	cd infrastructure && yes | terraform apply

# Docker

build_image:
	@echo "Building Docker image"
	docker build --platform linux/amd64 --build-arg PROJECT_ID=${PROJECT_ID} --build-arg PROJECT_NO=${PROJECT_NO} -t energy-project-tracking:latest .

push_image:
	@echo "Pushing Docker image to registry"
	docker tag energy-project-tracking:latest ${PROJECT_REGION}-docker.pkg.dev/${PROJECT_ID}/${DOCKER_REPO}/energy-project-tracking:latest
	docker push ${PROJECT_REGION}-docker.pkg.dev/${PROJECT_ID}/${DOCKER_REPO}/energy-project-tracking:latest

# Linting and Formatting

format:
	@echo "Formatting code"
	poetry run ruff format energy_projects_tracking

check:
	ruff check energy_projects_tracking
	mypy energy_projects_tracking --ignore-missing-imports --disallow-untyped-defs

set_env:
	./scripts/set_env_var.sh
	@echo "Environment variables set"
	