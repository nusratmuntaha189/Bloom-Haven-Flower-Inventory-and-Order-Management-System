import random
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
import mysql.connector

app = Flask(__name__)
app.secret_key = "bloom_haven_secret_key"  # needed for flash messages + sessions

LOW_STOCK_THRESHOLD = 10  # flowers with quantity below this are flagged on the dashboard
SEED_PAPER_FEE = 20.00    # flat fee (৳) added when a customer chooses seed-paper gift wrap


# ---------- DATABASE CONNECTION ----------
def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",       # default XAMPP username
        password="",       # default XAMPP password is empty
        database="bloom_haven"
    )
    return connection


# ---------- LOGIN REQUIRED DECORATOR ----------
def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get('admin_id'):
            flash("Please log in to continue.")
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return wrapped


# =========================================================
#                       AUTH
# =========================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']

        if not email or not password:
            flash("Email and password are required.")
            return redirect(url_for('login'))

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM admins WHERE email = %s", (email,))
        admin = cursor.fetchone()
        cursor.close()
        conn.close()

        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_id'] = admin['id']
            session['admin_name'] = admin['name']
            flash(f"Welcome back, {admin['name']}!")
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password.")
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for('login'))


# ---------- HOME PAGE ----------
@app.route('/')
@login_required
def home():
    return render_template('index.html')


# =========================================================
#                      DASHBOARD
# =========================================================
@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Total orders and total revenue (join orders -> flowers)
    cursor.execute("""
        SELECT COUNT(*) AS total_orders,
               COALESCE(SUM(orders.quantity * flowers.price), 0) AS total_revenue
        FROM orders
        JOIN flowers ON orders.flower_id = flowers.id
    """)
    totals = cursor.fetchone()

    # Total customers and flowers in inventory
    cursor.execute("SELECT COUNT(*) AS total_customers FROM customers")
    total_customers = cursor.fetchone()['total_customers']

    cursor.execute("SELECT COUNT(*) AS total_flowers FROM flowers")
    total_flowers = cursor.fetchone()['total_flowers']

    # Top-selling flower by total quantity ordered
    cursor.execute("""
        SELECT flowers.name, SUM(orders.quantity) AS total_sold
        FROM orders
        JOIN flowers ON orders.flower_id = flowers.id
        GROUP BY flowers.id, flowers.name
        ORDER BY total_sold DESC
        LIMIT 1
    """)
    top_flower = cursor.fetchone()

    # Low stock flowers
    cursor.execute(
        "SELECT * FROM flowers WHERE quantity < %s ORDER BY quantity ASC",
        (LOW_STOCK_THRESHOLD,)
    )
    low_stock = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'dashboard.html',
        totals=totals,
        total_customers=total_customers,
        total_flowers=total_flowers,
        top_flower=top_flower,
        low_stock=low_stock,
        threshold=LOW_STOCK_THRESHOLD
    )


# =========================================================
#                      FLOWERS CRUD
# =========================================================
@app.route('/flowers')
@login_required
def flowers():
    search = request.args.get('q', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if search:
        cursor.execute(
            "SELECT * FROM flowers WHERE name LIKE %s OR category LIKE %s ORDER BY name",
            (f"%{search}%", f"%{search}%")
        )
    else:
        cursor.execute("SELECT * FROM flowers ORDER BY name")
    all_flowers = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('flowers.html', flowers=all_flowers, search=search)


@app.route('/flowers/add', methods=['GET', 'POST'])
@login_required
def add_flower():
    if request.method == 'POST':
        name = request.form['name'].strip()
        price = request.form['price']
        quantity = request.form['quantity']
        category = request.form['category'].strip()

        # ---- basic data validation ----
        if not name or not price or not quantity:
            flash("Name, price and quantity are required.")
            return redirect(url_for('add_flower'))
        try:
            price = float(price)
            quantity = int(quantity)
            if price < 0 or quantity < 0:
                raise ValueError
        except ValueError:
            flash("Price and quantity must be valid positive numbers.")
            return redirect(url_for('add_flower'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO flowers (name, price, quantity, category) VALUES (%s, %s, %s, %s)",
            (name, price, quantity, category)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Flower added successfully!")
        return redirect(url_for('flowers'))

    return render_template('add_flower.html')


@app.route('/flowers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_flower(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name'].strip()
        price = request.form['price']
        quantity = request.form['quantity']
        category = request.form['category'].strip()

        try:
            price = float(price)
            quantity = int(quantity)
            if price < 0 or quantity < 0:
                raise ValueError
        except ValueError:
            flash("Price and quantity must be valid positive numbers.")
            return redirect(url_for('edit_flower', id=id))

        cursor.execute(
            "UPDATE flowers SET name=%s, price=%s, quantity=%s, category=%s WHERE id=%s",
            (name, price, quantity, category, id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Flower updated successfully!")
        return redirect(url_for('flowers'))

    cursor.execute("SELECT * FROM flowers WHERE id = %s", (id,))
    flower = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_flower.html', flower=flower)


@app.route('/flowers/delete/<int:id>')
@login_required
def delete_flower(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM flowers WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Flower deleted.")
    return redirect(url_for('flowers'))


# =========================================================
#                     CUSTOMERS CRUD
# =========================================================
@app.route('/customers')
@login_required
def customers():
    search = request.args.get('q', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    if search:
        cursor.execute(
            "SELECT * FROM customers WHERE name LIKE %s OR phone LIKE %s ORDER BY name",
            (f"%{search}%", f"%{search}%")
        )
    else:
        cursor.execute("SELECT * FROM customers ORDER BY name")
    all_customers = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('customers.html', customers=all_customers, search=search)


@app.route('/customers/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if request.method == 'POST':
        name = request.form['name'].strip()
        phone = request.form['phone'].strip()
        address = request.form['address'].strip()

        if not name or not phone:
            flash("Name and phone are required.")
            return redirect(url_for('add_customer'))

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO customers (name, phone, address) VALUES (%s, %s, %s)",
            (name, phone, address)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Customer added successfully!")
        return redirect(url_for('customers'))

    return render_template('add_customer.html')


@app.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name'].strip()
        phone = request.form['phone'].strip()
        address = request.form['address'].strip()

        if not name or not phone:
            flash("Name and phone are required.")
            return redirect(url_for('edit_customer', id=id))

        cursor.execute(
            "UPDATE customers SET name=%s, phone=%s, address=%s WHERE id=%s",
            (name, phone, address, id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        flash("Customer updated successfully!")
        return redirect(url_for('customers'))

    cursor.execute("SELECT * FROM customers WHERE id = %s", (id,))
    customer = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit_customer.html', customer=customer)


@app.route('/customers/delete/<int:id>')
@login_required
def delete_customer(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE id = %s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash("Customer deleted.")
    return redirect(url_for('customers'))


# =========================================================
#                       ORDERS CRUD
# =========================================================
@app.route('/orders')
@login_required
def orders():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # JOIN so we display customer name and flower name instead of just IDs
    cursor.execute("""
        SELECT orders.id, customers.name AS customer_name, flowers.name AS flower_name,
               orders.quantity, orders.order_date, orders.status
        FROM orders
        JOIN customers ON orders.customer_id = customers.id
        JOIN flowers ON orders.flower_id = flowers.id
        ORDER BY orders.id DESC
    """)
    all_orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('orders.html', orders=all_orders)


@app.route('/orders/add', methods=['GET', 'POST'])
@login_required
def add_order():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        customer_id = request.form['customer_id']
        flower_id = request.form['flower_id']
        quantity = request.form['quantity']
        order_date = request.form['order_date']

        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            flash("Quantity must be a positive number.")
            cursor.close()
            conn.close()
            return redirect(url_for('add_order'))

        try:
            # ---- stock validation + deduction as a single transaction ----
            cursor.execute(
                "SELECT quantity, name FROM flowers WHERE id = %s FOR UPDATE",
                (flower_id,)
            )
            flower = cursor.fetchone()

            if not flower:
                flash("Selected flower does not exist.")
                conn.rollback()
                return redirect(url_for('add_order'))

            if flower['quantity'] < quantity:
                flash(f"Not enough stock for {flower['name']}. Only {flower['quantity']} left.")
                conn.rollback()
                return redirect(url_for('add_order'))

            cursor.execute(
                "INSERT INTO orders (customer_id, flower_id, quantity, order_date) VALUES (%s, %s, %s, %s)",
                (customer_id, flower_id, quantity, order_date)
            )
            cursor.execute(
                "UPDATE flowers SET quantity = quantity - %s WHERE id = %s",
                (quantity, flower_id)
            )
            conn.commit()
            flash("Order placed successfully! Stock updated.")
            return redirect(url_for('orders'))
        finally:
            cursor.close()
            conn.close()

    cursor.execute("SELECT * FROM customers")
    customer_list = cursor.fetchall()
    cursor.execute("SELECT * FROM flowers")
    flower_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('add_order.html', customers=customer_list, flowers=flower_list)


@app.route('/orders/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_order(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        new_customer_id = request.form['customer_id']
        new_flower_id = request.form['flower_id']
        new_quantity = request.form['quantity']
        order_date = request.form['order_date']

        try:
            new_quantity = int(new_quantity)
            if new_quantity <= 0:
                raise ValueError
        except ValueError:
            flash("Quantity must be a positive number.")
            cursor.close()
            conn.close()
            return redirect(url_for('edit_order', id=id))

        try:
            # ---- fetch the original order so we know how much stock to restore ----
            cursor.execute("SELECT * FROM orders WHERE id = %s FOR UPDATE", (id,))
            old_order = cursor.fetchone()
            if not old_order:
                flash("Order not found.")
                conn.rollback()
                return redirect(url_for('orders'))

            if old_order['status'] == 'Cancelled':
                flash("A cancelled order can't be edited. Place a new order instead.")
                conn.rollback()
                return redirect(url_for('orders'))

            # Restore stock to the original flower first
            cursor.execute(
                "UPDATE flowers SET quantity = quantity + %s WHERE id = %s",
                (old_order['quantity'], old_order['flower_id'])
            )

            # Now validate against the (possibly new) flower's available stock
            cursor.execute(
                "SELECT quantity, name FROM flowers WHERE id = %s FOR UPDATE",
                (new_flower_id,)
            )
            flower = cursor.fetchone()

            if not flower:
                flash("Selected flower does not exist.")
                conn.rollback()
                return redirect(url_for('edit_order', id=id))

            if flower['quantity'] < new_quantity:
                flash(f"Not enough stock for {flower['name']}. Only {flower['quantity']} left.")
                conn.rollback()
                return redirect(url_for('edit_order', id=id))

            cursor.execute(
                "UPDATE flowers SET quantity = quantity - %s WHERE id = %s",
                (new_quantity, new_flower_id)
            )
            cursor.execute(
                "UPDATE orders SET customer_id=%s, flower_id=%s, quantity=%s, order_date=%s WHERE id=%s",
                (new_customer_id, new_flower_id, new_quantity, order_date, id)
            )
            conn.commit()
            flash("Order updated successfully! Stock adjusted.")
            return redirect(url_for('orders'))
        finally:
            cursor.close()
            conn.close()

    cursor.execute("SELECT * FROM orders WHERE id = %s", (id,))
    order = cursor.fetchone()
    if not order:
        flash("Order not found.")
        cursor.close()
        conn.close()
        return redirect(url_for('orders'))
    if order['status'] == 'Cancelled':
        flash("A cancelled order can't be edited. Place a new order instead.")
        cursor.close()
        conn.close()
        return redirect(url_for('orders'))
    cursor.execute("SELECT * FROM customers")
    customer_list = cursor.fetchall()
    cursor.execute("SELECT * FROM flowers")
    flower_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('edit_order.html', order=order, customers=customer_list, flowers=flower_list)


@app.route('/orders/delete/<int:id>')
@login_required
def delete_order(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Restore stock back to the flower before deleting the order
    cursor.execute("SELECT * FROM orders WHERE id = %s", (id,))
    order = cursor.fetchone()

    if order:
        if order['status'] != 'Cancelled':
            cursor.execute(
                "UPDATE flowers SET quantity = quantity + %s WHERE id = %s",
                (order['quantity'], order['flower_id'])
            )
        cursor.execute("DELETE FROM orders WHERE id = %s", (id,))
        conn.commit()
        flash("Order deleted. Stock restored.")
    else:
        flash("Order not found.")

    cursor.close()
    conn.close()
    return redirect(url_for('orders'))


@app.route('/orders/cancel/<int:id>')
@login_required
def cancel_order(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM orders WHERE id = %s FOR UPDATE", (id,))
    order = cursor.fetchone()

    if not order:
        flash("Order not found.")
    elif order['status'] == 'Cancelled':
        flash("This order is already cancelled.")
    elif order['status'] == 'Delivered':
        flash("A delivered order can't be cancelled.")
    else:
        # Cancelling releases the stock back to inventory
        cursor.execute(
            "UPDATE flowers SET quantity = quantity + %s WHERE id = %s",
            (order['quantity'], order['flower_id'])
        )
        cursor.execute("UPDATE orders SET status = 'Cancelled' WHERE id = %s", (id,))
        conn.commit()
        flash("Order cancelled. Stock restored.")

    cursor.close()
    conn.close()
    return redirect(url_for('orders'))


@app.route('/orders/deliver/<int:id>')
@login_required
def mark_delivered(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM orders WHERE id = %s", (id,))
    order = cursor.fetchone()

    if not order:
        flash("Order not found.")
    elif order['status'] == 'Cancelled':
        flash("A cancelled order can't be marked delivered.")
    else:
        cursor.execute("UPDATE orders SET status = 'Delivered' WHERE id = %s", (id,))
        conn.commit()
        flash("Order marked as delivered.")

    cursor.close()
    conn.close()
    return redirect(url_for('orders'))


# =========================================================
#                  CUSTOM BOUQUET BUILDER
# =========================================================
@app.route('/bouquets')
@login_required
def bouquets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT bouquets.id, customers.name AS customer_name, bouquets.wrapping_type,
               bouquets.has_seed_paper, bouquets.total_price, bouquets.created_date,
               COUNT(bouquet_items.id) AS flower_types
        FROM bouquets
        JOIN customers ON bouquets.customer_id = customers.id
        LEFT JOIN bouquet_items ON bouquet_items.bouquet_id = bouquets.id
        GROUP BY bouquets.id, customers.name, bouquets.wrapping_type,
                 bouquets.has_seed_paper, bouquets.total_price, bouquets.created_date
        ORDER BY bouquets.id DESC
    """)
    all_bouquets = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('bouquets.html', bouquets=all_bouquets)


@app.route('/bouquets/create', methods=['GET', 'POST'])
@login_required
def create_bouquet():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        wrapping_type = request.form.get('wrapping_type', 'Standard Wrap').strip() or 'Standard Wrap'
        has_seed_paper = 1 if request.form.get('seed_paper') == 'on' else 0

        if not customer_id:
            flash("Please select a customer.")
            cursor.close()
            conn.close()
            return redirect(url_for('create_bouquet'))

        # Gather the chosen flowers: form fields are named qty_<flower_id>
        cursor.execute("SELECT * FROM flowers")
        all_flowers = cursor.fetchall()
        chosen = []
        for f in all_flowers:
            raw_qty = request.form.get(f"qty_{f['id']}", "0").strip()
            try:
                qty = int(raw_qty) if raw_qty else 0
            except ValueError:
                qty = 0
            if qty > 0:
                chosen.append((f['id'], f['name'], f['price'], qty))

        if not chosen:
            flash("Pick at least one flower and quantity for your bouquet.")
            cursor.close()
            conn.close()
            return redirect(url_for('create_bouquet'))

        try:
            # ---- validate + deduct stock for every chosen flower, atomically ----
            total_price = 0
            for flower_id, name, price, qty in chosen:
                cursor.execute(
                    "SELECT quantity FROM flowers WHERE id = %s FOR UPDATE",
                    (flower_id,)
                )
                stock = cursor.fetchone()
                if not stock or stock['quantity'] < qty:
                    available = stock['quantity'] if stock else 0
                    flash(f"Not enough stock for {name}. Only {available} left.")
                    conn.rollback()
                    return redirect(url_for('create_bouquet'))
                total_price += float(price) * qty

            quote_id = None
            if has_seed_paper:
                total_price += SEED_PAPER_FEE
                cursor.execute("SELECT id FROM quotes")
                quote_ids = [row['id'] for row in cursor.fetchall()]
                if quote_ids:
                    quote_id = random.choice(quote_ids)

            cursor.execute(
                """INSERT INTO bouquets (customer_id, wrapping_type, has_seed_paper, quote_id, total_price)
                   VALUES (%s, %s, %s, %s, %s)""",
                (customer_id, wrapping_type, has_seed_paper, quote_id, total_price)
            )
            bouquet_id = cursor.lastrowid

            for flower_id, name, price, qty in chosen:
                cursor.execute(
                    "INSERT INTO bouquet_items (bouquet_id, flower_id, quantity) VALUES (%s, %s, %s)",
                    (bouquet_id, flower_id, qty)
                )
                cursor.execute(
                    "UPDATE flowers SET quantity = quantity - %s WHERE id = %s",
                    (qty, flower_id)
                )

            conn.commit()
            flash("Custom bouquet created! 💐")
            return redirect(url_for('view_bouquet', id=bouquet_id))
        finally:
            cursor.close()
            conn.close()

    cursor.execute("SELECT * FROM customers ORDER BY name")
    customer_list = cursor.fetchall()
    cursor.execute("SELECT * FROM flowers WHERE quantity > 0 ORDER BY name")
    flower_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('create_bouquet.html', customers=customer_list, flowers=flower_list,
                            seed_paper_fee=SEED_PAPER_FEE)


@app.route('/bouquets/view/<int:id>')
@login_required
def view_bouquet(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT bouquets.*, customers.name AS customer_name, customers.phone AS customer_phone,
               quotes.text AS quote_text
        FROM bouquets
        JOIN customers ON bouquets.customer_id = customers.id
        LEFT JOIN quotes ON bouquets.quote_id = quotes.id
        WHERE bouquets.id = %s
    """, (id,))
    bouquet = cursor.fetchone()

    if not bouquet:
        flash("Bouquet not found.")
        cursor.close()
        conn.close()
        return redirect(url_for('bouquets'))

    cursor.execute("""
        SELECT flowers.name, flowers.price, bouquet_items.quantity
        FROM bouquet_items
        JOIN flowers ON bouquet_items.flower_id = flowers.id
        WHERE bouquet_items.bouquet_id = %s
    """, (id,))
    items = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('view_bouquet.html', bouquet=bouquet, items=items)


@app.route('/bouquets/delete/<int:id>')
@login_required
def delete_bouquet(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Restore stock for every flower in the bouquet before deleting it
    cursor.execute("SELECT flower_id, quantity FROM bouquet_items WHERE bouquet_id = %s", (id,))
    items = cursor.fetchall()

    if items:
        for item in items:
            cursor.execute(
                "UPDATE flowers SET quantity = quantity + %s WHERE id = %s",
                (item['quantity'], item['flower_id'])
            )
        cursor.execute("DELETE FROM bouquets WHERE id = %s", (id,))
        conn.commit()
        flash("Bouquet deleted. Stock restored.")
    else:
        flash("Bouquet not found.")

    cursor.close()
    conn.close()
    return redirect(url_for('bouquets'))


if __name__ == '__main__':
    app.run(debug=True)
