# Bloom Haven — Flower Inventory & Order Management System

A full-stack DBMS project built with **Python (Flask)**, **MySQL**, and **HTML/CSS/JavaScript**.
Bloom Haven lets an admin manage flowers, customers, orders, and build custom bouquets
(with an optional seed-paper gift wrap that includes a random quote).

## Features
- Admin login/authentication (session-based)
- Full CRUD for Flowers, Customers, and Orders
- Custom Bouquet builder (pick multiple flowers + optional seed-paper wrap with a quote)
- Low-stock flag on the dashboard
- Order status tracking (Pending / Delivered / Cancelled)

## Tech Stack
- **Backend:** Python, Flask
- **Database:** MySQL
- **Frontend:** HTML, CSS, Jinja2 templates

## Database Schema
See [`schema.sql`](./schema.sql) for the full schema. Main tables:
`admins`, `customers`, `flowers`, `orders`, `quotes`, `bouquets`, `bouquet_items`.

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/bloom-haven.git
   cd bloom-haven
   ```

2. **Create a virtual environment (optional but recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**
   - Start MySQL (via XAMPP or MySQL Workbench)
   - Import the schema:
     ```bash
     mysql -u root -p < schema.sql
     ```

5. **Run the app**
   ```bash
   python app.py
   ```
   Open `http://127.0.0.1:5000` in your browser.

6. **Default admin login**
   - Email: `admin@bloomhaven.com`
   - Password: `admin123`

## Project Structure
```
bloom_haven_project_updated/
├── app.py
├── schema.sql
├── requirements.txt
├── static/
│   └── style.css
└── templates/
    ├── base.html
    ├── login.html
    ├── dashboard.html
    ├── flowers.html / add_flower.html / edit_flower.html
    ├── customers.html / add_customer.html / edit_customer.html
    ├── orders.html / add_order.html / edit_order.html
    └── bouquets.html / create_bouquet.html / view_bouquet.html
```
