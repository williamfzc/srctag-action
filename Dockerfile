FROM python:3.11-slim

WORKDIR /action_internal

RUN apt-get update && apt-get install -y git

COPY ./requirements.txt .

RUN pip install -r ./requirements.txt

COPY . .

# user's code here
WORKDIR /github/workspace

ENTRYPOINT ["python3", "/action_internal/main.py"]
