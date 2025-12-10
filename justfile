default:
    @just --list

# Run the server
runserver:
    PYTHONUNBUFFERED=true FORCE_COLOR=true DEBUG=true uv run python manage.py runserver --force-color 0.0.0.0:8000

make-migrations:
    uv run python manage.py makemigrations

migrate:
    uv run python manage.py migrate