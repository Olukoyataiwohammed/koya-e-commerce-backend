# 🛒 Koya Ecommerce Backend

A RESTful e-commerce backend built with Django and Django REST Framework. This API powers the Koya Ecommerce frontend by providing secure authentication, product management, shopping cart functionality, wishlist management, order processing, Paystack payment integration, and a customer support messaging system.

## 🚀 Features

- User registration and authentication
- JWT authentication
- Product and category management
- Shopping cart management
- Wishlist functionality
- Order processing
- Paystack payment integration
- Customer support messaging
- Admin reply system
- File uploads
- RESTful API architecture

## 🛠️ Tech Stack

- Python
- Django
- Django REST Framework
- PostgreSQL (Production)
- SQLite (Development)
- Gunicorn
- PythonAnywhere
- JWT Authentication

## 📡 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/products/` | Retrieve product list |
| `/api/cart/` | Manage shopping cart |
| `/api/orders/` | Create and manage orders |
| `/api/accounts/register/` | Register a new user |
| `/api/accounts/login/` | Authenticate users |
| `/api/wishlist/` | Manage wishlist |
| `/api/support/` | Customer support messaging |

## ⚙️ Installation

```bash
https://github.com/Olukoyataiwohammed/koya-ecommerce-backend.git

cd koya-ecommerce-backend

python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt

python manage.py migrate

python manage.py runserver
```

## 🌐 Live Application

**Frontend Demo**

https://koya-ecommerce-frontend.vercel.app/

**Frontend Repository**

https://github.com/Olukoyataiwohammed/koya-ecommerce-frontend



## 👨‍💻 Author

**Taiwo Olukoya**

GitHub: https://github.com/Olukoyataiwohammed
