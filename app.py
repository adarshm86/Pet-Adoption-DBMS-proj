from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from datetime import date, timedelta
import os
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Session lifetime
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=10)

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

# Home page - show all pets
@app.route('/')
def home():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM pets")
    pets = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('index.html', pets=pets)


# Add pet to cart
@app.route('/add_to_cart/<int:pet_id>', methods=['POST', 'GET'])
def add_to_cart(pet_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM pets WHERE id = %s", (pet_id,))
    pet = cursor.fetchone()

    cursor.close()
    conn.close()

    if 'cart' not in session:
        session['cart'] = []

    session['cart'].append(pet)

    print(f"Cart after adding pet: {session['cart']}")

    session.modified = True

    return redirect(url_for('home'))


# View cart
@app.route('/cart')
def view_cart():
    cart = session.get('cart', [])

    total_pets = len(cart)

    return render_template(
        'cart.html',
        cart=cart,
        total_pets=total_pets
    )


# Clear cart
@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('view_cart'))


# Remove pet from cart
@app.route('/remove_from_cart/<int:pet_index>', methods=['POST'])
def remove_from_cart(pet_index):
    cart = session.get('cart', [])

    if 0 <= pet_index < len(cart):
        cart.pop(pet_index)

    session['cart'] = cart

    return redirect(url_for('view_cart'))


# Checkout page
@app.route('/checkout', methods=['POST', 'GET'])
def checkout():
    if request.method == 'POST':
        return render_template('checkout.html')

    return redirect(url_for('view_cart'))


# Confirm adoption
@app.route('/confirm_adoption', methods=['POST'])
def confirm_adoption():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']

    cart = session.get('cart', [])

    if not cart:
        return redirect(url_for('home'))

    conn = get_connection()
    cursor = conn.cursor()

    # Insert adopter
    cursor.execute("""
        INSERT INTO Adopter (Name, Email, Phone, Address)
        VALUES (%s, %s, %s, %s)
    """, (name, email, phone, address))

    adopter_id = cursor.lastrowid

    today = date.today()

    # Insert adoption records
    for pet in cart:
        cursor.execute("""
            INSERT INTO Adoption (Pet_id, Adopter_id, Adoption_date, Status)
            VALUES (%s, %s, %s, %s)
        """, (pet['id'], adopter_id, today, "Pending"))

    conn.commit()

    cursor.close()
    conn.close()

    session.pop('cart', None)

    return render_template("thank_you.html", adopter_name=name)


if __name__ == '__main__':
    app.run(debug=True)
