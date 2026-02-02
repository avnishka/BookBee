# BookBee 🐝
A Peer-to-Peer Book Sharing & Selling Platform

## 📖 Project Description
BookBee is a web-based platform designed to connect book lovers. It allows users to lend, rent, or sell their pre-loved books to others in their community. With features like location-based search, real-time chat, and a trust score system, BookBee makes sharing knowledge easy and secure.

## ✨ Key Features
* **User Authentication:** Secure Sign Up, Login, and Profile Management with email activation.
* **Lend or Sell:** Users can list books for rent (with a per-2-weeks price) or for sale.
* **Smart Search:** Find books by Title, Genre, or Location (City).
* **Location Detection:** Automatically detects user city for easier listing.
* **Shopping Cart:** Add multiple books to a cart and proceed to checkout.
* **Real-time Chat:** Integrated messaging system to discuss book details before transacting.
* **Trust Score:** "User Credit" system to build trust between buyers and sellers.
* **Responsive Design:** Works on desktop and mobile devices.

## 🛠️ Technology Stack
* **Backend:** Django (Python)
* **Frontend:** HTML5, CSS3, JavaScript
* **Database:** SQLite (Default Django DB)
* **Styling:** Custom CSS (Poppins font, modern card layout)

## 📂 Project Structure
* `bookbeeproject/` - Main project configuration (settings, urls, wsgi).
* `bookbeeapp/` - Core application handling books, users, cart, and payments.
* `chat/` - Chat application handling messaging and notifications.
* `templates/` - HTML templates for all pages (Home, Profile, Chat, etc.).
* `static/` - Static assets (CSS, Book Images, Avatars, Logo).
* `media/` - User-uploaded content (Book covers).

## 🚀 Installation & Setup

1.  **Clone the Repository**
    git clone <repository-url>
    cd bookbee

2.  **Create a Virtual Environment**
    python -m venv venv
    
    # Activate it:
    # Windows:
    venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate

3.  **Install Dependencies**
    pip install django
    pip install pillow
    # (Install any other requirements if you have a requirements.txt)

4.  **Database Migration**
    python manage.py makemigrations
    python manage.py migrate

5.  **Create a Superuser (Admin)**
    python manage.py createsuperuser

6.  **Run the Server**
    python manage.py runserver

7.  **Access the App**
    Open your browser and go to: http://127.0.0.1:8000/

## 👤 Author
**Avnishka Bhardwaj**
**Aditi Gupta**
**Abhya Sharma**
**Anushka Joshi**
B.Tech Computer Science Student

## 📜 License
This project is for educational purposes.