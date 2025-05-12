version: '3.9'

services:
  pipeline:
    build: .
    container_name: doom_pipeline
    env_file:
      - .env
    command: python -m src.app
    depends_on:
      - mongo
    networks:
      - doom_net

  monitor:
    build: .
    container_name: doom_monitor
    env_file:
      - .env
    command: uvicorn src.monitor:app --host 0.0.0.0 --port 9000
    ports:
      - "9000:9000"
    depends_on:
      - mongo
    networks:
      - doom_net

  mongo:
    image: mongo:6.0
    container_name: doom_mongo
    restart: always
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: example
    ports:
      - "27017:27017"
    networks:
      - doom_net

networks:
  doom_net:
