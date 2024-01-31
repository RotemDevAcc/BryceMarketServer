# BryceMarket Django Server

Welcome to the BryceMarket Django server repository. This server is the backend of the BryceMarket secure supermarket app, providing essential functionality for managing products, categories, users, receipts, and more. Below, you'll find information on how to set up and use the server.


## Setting Up a Virtual Environment

Before installing the required packages, it's recommended to set up a virtual environment. This keeps your project's dependencies separate from your global Python installation. To set up a virtual environment, run:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```
## Prerequisites
Ensure Python 3.x is installed on your system. You can [download Python here](https://www.python.org/downloads/).

After cloning the repository, navigate to the project directory and install the required dependencies using:
```bash
pip install -r requirements.txt
```
## Getting Started

1. Clone the repository to your local machine:

   ```bash
   git clone https://github.com/RotemDevAcc/BryceMarketServer.git
   ```

2. Navigate to the project directory:
   ```bash
   cd Back
   ```


3. Run database migrations:
   ```bash
   python manage.py migrate
   ```

4. access settings.py and set your web url there for password reset:
   ```bash
   SECRET_KEY = 'YOUR_DJANGO_SECRET_KEY'
   ```
   Use this website to generate a key: https://djecrety.ir/

5. access settings.py and set your web url there for password reset:
   ```bash
   PASSWORD_RESET_URL = 'your url'
   ```

   
   
6. access settings.py and set your paypal details there too:
   ```bash
   PAYPAL_CLIENT_ID = "YOUR_PAYPAL_CLIENTID"
   PAYPAL_CLIENT_SECRET = "YOUR_PAYPAL_CLIENTSECRET"
   ```

7. Set up your email for password resets in settings.py
   # Tutuorial https://www.youtube.com/watch?v=lezhrFdVSVY for setting enviorment variables
   ```bash
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   EMAIL_HOST = 'smtp.gmail.com'  # Update with your email provider's SMTP server
   EMAIL_PORT = 587  # Update with the appropriate port for your email provider
   EMAIL_USE_TLS = True
   EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER") # Update with your email username or use an enviorment variable like i did
   EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD") # Update with your email password or use an enviorment variable like i did
   ```


8. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Designed To Work With https://github.com/RotemDevAcc/BryceMarketReact As A FrontEnd