# ZKart - Full Stack E-commerce Platform

A comprehensive e-commerce web application built with Django framework following the Model-View-Template (MVT) architecture. ZKart provides a complete online shopping experience with advanced features for both customers and administrators.

## 🚀 Features

### Customer Features
- **User Authentication & Management**
  - User registration with email verification
  - Secure login/logout system
  - Password reset with OTP verification
  - Social authentication (Google & Facebook)
  - Profile management with address book
  - Referral system with wallet rewards

- **Product Browsing & Search**
  - Advanced filtering (category, brand, price range, colors, sizes)
  - Product search functionality
  - Sort products (A-Z, price, popularity, latest)
  - Product details with multiple images
  - Product ratings and reviews
  - Wishlist functionality

- **Shopping Experience**
  - Add to cart with quantity management
  - Real-time cart updates
  - Coupon system with discount codes
  - Dynamic delivery charge calculation based on location
  - Multiple payment options (Razorpay, COD, Wallet)

- **Order Management**
  - Order tracking and management
  - Order history with detailed tracking
  - Order cancellation and return requests
  - Invoice generation (PDF)
  - 7-day return policy
  - Refund processing to wallet

### Admin Features
- **Dashboard Analytics**
  - Sales charts and revenue tracking
  - Order status analytics
  - Top-selling products and categories
  - Customer insights with customizable date filtering

- **Product Management**
  - Add/edit products with image cropping
  - Multi-variant products (size, color, quantity)
  - Category and size management
  - Inventory tracking

- **Order Processing**
  - Order status management
  - Return request handling
  - Refund processing
  - Sales reporting (PDF/Excel export)

## 🛠️ Technology Stack

- **Backend**: Django 5.0.6, Python
- **Database**: PostgreSQL (AWS RDS)
- **Frontend**: HTML, CSS, JavaScript
- **Payment Integration**: Razorpay
- **Cloud Services**: AWS S3 (file storage)
- **Authentication**: Django Allauth
- **PDF Generation**: xhtml2pdf, ReportLab
- **Charts**: Chart.js

## 📦 Key Dependencies

```
Django==5.0.6
django-allauth==0.63.3
razorpay==1.4.2
psycopg2==2.9.9
boto3==1.35.2
pillow==10.4.0
xhtml2pdf==0.2.16
geopy==2.4.1
pyotp==2.9.0
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/nasif-muhamed/ZKart.git
   cd ZKart
   ```

2. **Create virtual environment**
   ```bash
   python -m venv zkart_env
   source zkart_env/bin/activate  # On Windows: zkart_env\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file with the following variables:
   ```env
   SECRET_KEY=your_secret_key
   DEBUG=True
   DB_NAME=your_db_name
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=your_db_host
   MAIL=your_email@gmail.com
   PASSWORD=your_app_password
   AWS_ACCESS_KEY_ID=your_aws_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret
   RAZORPAY_API_KEY=your_razorpay_key
   RAZORPAY_API_SECRET=your_razorpay_secret
   ```

5. **Database Setup**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Run the application**
   ```bash
   python manage.py runserver
   ```

Visit `http://127.0.0.1:8000/` to access the application.

## 🏗️ Project Structure

```
ZKart/
├── users/              # User management & authentication
├── products/           # Product catalog & management
├── orders/             # Order processing & management
├── templates/          # HTML templates
├── static/             # CSS, JS, images
├── media/              # User uploaded files
└── zkart/             # Project configuration
```

## 💳 Payment Integration

ZKart integrates with Razorpay for secure payment processing, supporting:
- Credit/Debit cards
- UPI payments
- Net banking
- Digital wallets
- Cash on Delivery (COD) for orders under ₹1000

## 🌍 Location-Based Delivery

- Dynamic delivery charge calculation using geolocation
- Free delivery within 100km radius
- Graduated pricing based on distance
- Address validation with coordinates

## 🔒 Security Features

- CSRF protection
- User authentication & authorization
- Email verification for new accounts
- OTP-based password reset
- Secure payment processing
- Session management

## 📊 Key Highlights

- **Responsive Design**: Mobile-friendly interface across all devices
- **Social Authentication**: Google & Facebook login integration
- **Wallet System**: Referral rewards and refund processing
- **Advanced Analytics**: Comprehensive admin dashboard with charts
- **AWS Integration**: S3 for media storage, RDS for database
- **PDF Generation**: Automated invoice and report generation

## 🚀 Deployment

Configured for production deployment with:
- PostgreSQL database on AWS RDS
- Static file serving with WhiteNoise
- Media file storage on AWS S3
- Production-ready settings

## 👨‍💻 Developer

**Muhamed Nasif** - Full Stack Developer
- GitHub: [@nasif-muhamed](https://github.com/nasif-muhamed)

## 🤝 Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

**ZKart - Your one-stop e-commerce solution built with Django!** 🛒✨
