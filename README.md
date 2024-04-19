
# RocketFin - Lending App

RocketFin is a Django-based lending application that utilizes Celery for task scheduling, including Celery beat for periodic tasks and Celery worker for executing background tasks. It also uses Redis as the message broker for Celery.

## Setup Instructions

To set up the project on your local machine, follow these steps:

### Prerequisites

Make sure you have the following installed on your system:

- Python (>=3.6)
- Redis Server

### Installation

1. Clone the repository:
   ```bash
   git clone -b master https://github.com/Fayym7/RocketFins.git
   ```

2. Navigate to the project directory:
   ```bash
   cd RocketFins
   ```

3. Create and activate a virtual environment:
   ```bash
   python -m venv env
   source env/bin/activate   # For Linux/Mac
   # OR
   .\env\Scripts\activate    # For Windows
   ```

4. Install project dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Open a seperate Terminal and start the Redis server:
   ```bash
   redis-server
   ```

6. Run migrations to set up the database:
   ```bash
   python manage.py migrate
   ```

7. Start Celery beat for periodic tasks(New Terminal):
   ```bash
   celery -A RocketFins beat -l info
   ```

8. Start Celery worker for background task processing(New Terminal):
   ```bash
   celery -A RocketFins worker -l info
   ```

9. Finally, start the Django development server:
   ```bash
   python manage.py runserver
   ```

10. Access the application at [http://localhost:8000](http://localhost:8000) in your web browser.

## Project Structure

- **RocketFin**: Django project directory.
- **Finops**: Django app for financial operations.
- **Media**: Directory for storing user-uploaded files.
- **Static**: Directory for storing static files (CSS, JavaScript, etc.).
- **Templates**: HTML templates for rendering views.


Feel free to contribute by forking the repository and submitting pull requests!

