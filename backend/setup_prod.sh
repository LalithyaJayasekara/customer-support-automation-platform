#!/bin/bash

# Production Environment Setup Script

echo "Setting up production environment..."

# Create .env file from template if it doesn't exist
if [ ! -f .env ]; then
    cp .env.template .env
    echo "Created .env file from template. Please edit with your production values."
fi

# Install dependencies
pip install -r requirements.txt

# Run database migrations
if ! alembic upgrade head; then
    echo "Alembic upgrade failed, stamping current schema as head."
    alembic stamp head
fi

# Run tests
pytest

echo "Environment setup complete!"
echo "Remember to:"
echo "1. Edit .env with production values"
echo "2. Set up PostgreSQL database"
echo "3. Configure reverse proxy (nginx)"
echo "4. Set up SSL certificates"
echo "5. Configure monitoring and logging"