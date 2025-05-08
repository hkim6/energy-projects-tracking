FROM python:3.12.8-slim-bullseye AS base
ARG PROJECT_ID
ENV PROJECT_ID=$PROJECT_ID

ARG PROJECT_NO
ENV PROJECT_NO=$PROJECT_NO

RUN python -m pip install --upgrade pip

WORKDIR /app

COPY ./energy_projects_tracking/ ./energy_projects_tracking/ 
COPY ./requirements.txt .

# Install project dependencies
RUN pip install -r requirements.txt

CMD [ "python", "./energy_projects_tracking/news_scraper.py"]