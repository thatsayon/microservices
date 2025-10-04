
# Microservices Project

This repository contains multiple Django microservices: **authentication** and **payment**. Each microservice is self-contained with its own Django project setup.

---

## Folder Structure

```
microservices/
│
├── authentication/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py      # Django settings for authentication service
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── manage.py
│   └── .gitignore
│
├── payment/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py      # Django settings for payment service
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── manage.py
│   ├── requirements.txt
│   └── .gitignore
│
└── README.md
```

> **Note:** Each microservice has its own `core/settings.py` file, which contains the Django configuration for that microservice.

---

## Common Coding Conventions

To keep the code clean and consistent, the following conventions are followed across all microservices:

### 1. PEP 8 Compliance
- Use 4 spaces for indentation
- Limit lines to 79 characters
- Use descriptive variable and function names

### 2. Apps and Modules
- Each Django app is kept self-contained with models, views, serializers, and urls
- Microservice-specific configurations are in `core/settings.py`

### 3. Imports
Standard library imports first, followed by third-party, then local imports.

\`\`\`python
import os
from datetime import datetime

from django.conf import settings

from myapp.models import User
\`\`\`

### 4. Docstrings
Functions, classes, and modules include clear docstrings.

\`\`\`python
class User(models.Model):
    """Represents a user in the authentication service.

    Fields:
    - email: user's email
    - full_name: user's full name
    - date_joined: registration date
    """
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100)
\`\`\`

### 5. Settings Separation
- Keep secret keys and sensitive configs in environment variables
- Use `.env` files for local development (do not commit to Git)

### 6. REST API
- Use Django REST Framework (DRF) for API endpoints
- Use serializers for request validation and response formatting
- Organize API views using `views.py` and route via `urls.py`

---

## Example Port Plan

When running multiple microservices together, each service should have its own dedicated port to avoid conflicts.

| Microservice     | Container Port | Host Port |
|-------------------|----------------|-----------|
| Authentication    | 8000           | 8001      |
| Payment           | 8000           | 8002      |
| Email (future)   | 8000           | 8003      |
| Notification (future) | 8000      | 8004      |
| Socket.IO Service (future) | 9000 | 9000      |
| Celery Worker    | —              | —         |
| Celery Beat      | —              | —         |
| PostgreSQL       | 5432           | 5432      |
| Redis             | 6379           | 6379      |

This ensures no port conflicts and keeps services isolated.

---

## Setup Instructions

### 1. Clone the repository

\`\`\`bash
git clone https://github.com/thatsayon/microservices.git
cd microservices
\`\`\`

### 2. Navigate to a microservice folder and install dependencies

\`\`\`bash
cd authentication  # or payment
pip install -r requirements.txt
\`\`\`

### 3. Apply migrations

\`\`\`bash
python manage.py migrate
\`\`\`

### 4. Run the development server

\`\`\`bash
python manage.py runserver
\`\`\`

---

## Running Multiple Microservices Together

When running multiple microservices locally, each service needs to run on a different port.

### Terminal 1 - Authentication Service
\`\`\`bash
cd authentication
python manage.py runserver 8001
\`\`\`

### Terminal 2 - Payment Service
\`\`\`bash
cd payment
python manage.py runserver 8002
\`\`\`

The services will be available at:
- Authentication: \`http://localhost:8001\`
- Payment: \`http://localhost:8002\`

---

## Contribution Guidelines

- Follow the coding conventions above
- Use feature branches for new functionality
- Write docstrings and maintain \`README.md\` updates
- Test your changes before creating a pull request

---

## License

This project is licensed under the MIT License.

