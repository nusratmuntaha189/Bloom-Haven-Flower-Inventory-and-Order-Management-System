
DROP TABLE IF EXISTS bouquet_items;
DROP TABLE IF EXISTS bouquets;
DROP TABLE IF EXISTS quotes;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS flowers;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS admins;

CREATE TABLE admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE customers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    address VARCHAR(255)
);

CREATE TABLE flowers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    category VARCHAR(50)
);

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    flower_id INT NOT NULL,
    quantity INT NOT NULL,
    order_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    status ENUM('Pending', 'Delivered', 'Cancelled') NOT NULL DEFAULT 'Pending',
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (flower_id) REFERENCES flowers(id) ON DELETE CASCADE
);

-- Original short quotes/poem lines used as a surprise on seed-paper gift wrapping
CREATE TABLE quotes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    text VARCHAR(255) NOT NULL
);

-- A custom bouquet: a customer picks any mix of flowers, optionally with seed-paper wrap
CREATE TABLE bouquets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    wrapping_type VARCHAR(50) NOT NULL DEFAULT 'Standard Wrap',
    has_seed_paper BOOLEAN NOT NULL DEFAULT FALSE,
    quote_id INT DEFAULT NULL,
    total_price DECIMAL(10,2) NOT NULL DEFAULT 0,
    created_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
    FOREIGN KEY (quote_id) REFERENCES quotes(id) ON DELETE SET NULL
);

-- Which flowers (and how many of each) make up a bouquet
CREATE TABLE bouquet_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    bouquet_id INT NOT NULL,
    flower_id INT NOT NULL,
    quantity INT NOT NULL,
    FOREIGN KEY (bouquet_id) REFERENCES bouquets(id) ON DELETE CASCADE,
    FOREIGN KEY (flower_id) REFERENCES flowers(id) ON DELETE CASCADE
);

INSERT INTO quotes (text) VALUES
('Grow wild, grow gentle, grow your own way.'),
('Every seed here is a small promise to the future.'),
('Plant this, and let something new begin with you.'),
('Some gifts bloom once. This one keeps blooming.'),
('You are allowed to take up space and still be soft.'),
('Roots first, then wings.'),
('This paper remembers you long after the flowers fade.'),
('Bury this, water it, and watch patience turn into color.'),
('A small start is still a start worth planting.'),
('May whatever you grow from this remind you of today.');

-- Default admin login: email = admin@bloomhaven.com | password = admin123
-- (password_hash below is a werkzeug generate_password_hash() output for 'admin123')
INSERT INTO admins (name, email, password_hash) VALUES
('Admin', 'admin@bloomhaven.com', 'scrypt:32768:8:1$XMUxZWmJHF9mlfdZ$c59b77a8ea5f6f2873e846482e172538ce05902a5e1e1bf621e835c644e77f3a58a934c773eb0393f3905c6485fa050fedb144ef76bed42633099f633e90b6b1');

INSERT INTO customers (name, phone, address) VALUES
('Rahim Uddin', '01711111111', 'Dhanmondi, Dhaka'),
('Karim Ahmed', '01822222222', 'Mirpur, Dhaka');

INSERT INTO flowers (name, price, quantity, category) VALUES
('Rose', 25.00, 100, 'Fresh Flower'),
('Lily', 40.00, 50, 'Fresh Flower'),
('Orchid', 60.00, 30, 'Premium Flower');

INSERT INTO orders (customer_id, flower_id, quantity, order_date) VALUES
(1, 1, 5, '2026-06-15'),
(2, 3, 2, '2026-06-16');
