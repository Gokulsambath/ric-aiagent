#!/bin/bash
# Standalone script to seed the database inside the docker container
echo "Seeding widget configurations..."
docker exec ricagent-api python -m app.db.seed_widget_config
echo "Done."
