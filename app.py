from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
# from flask_basicauth import BasicAuth

app = Flask(__name__)
# app.config['BASIC_AUTH_USERNAME'] = 'username'
# app.config['BASIC_AUTH_PASSWORD'] = 'password'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost/library_store'


# basic_auth = BasicAuth(app)
db = SQLAlchemy(app)
login_manager = LoginManager(app)

class Categories(db.Model):
    id_category = db.Column(db.String(4), primary_key=True, default=db.text("CONCAT('NC', LPAD(nextval('categories_id_category_seq')::text, 2, '0'))"))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    related_books = db.relationship('Books', backref='owner_category', lazy='dynamic')

class Authors(db.Model):
    id_author = db.Column(db.String(4), primary_key=True, default=db.text("CONCAT('NA', LPAD(nextval('authors_id_author_seq')::text, 2, '0'))"))
    name = db.Column(db.String(255), nullable=False)
    nationality = db.Column(db.String(255), nullable=False)
    year_birth = db.Column(db.Integer, nullable=False)
    related_books = db.relationship('Books', backref='owner_author', lazy='dynamic')

class Books(db.Model):
    id_book = db.Column(db.String(5), primary_key=True, default=db.text("CONCAT('NB', LPAD(nextval('books_id_book_seq')::text, 3, '0'))"))
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(4), db.ForeignKey('authors.id_author'), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    total_pages = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(4), db.ForeignKey('categories.id_category'), nullable=False)
    related_transaction_books = db.relationship('TransactionBooks', backref='owner_book', lazy='dynamic')

class Users(db.Model):
    id_user = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(255), nullable=False, server_default='member')
                        #   check="user_type IN ('admin', 'member')")
    transactions_as_admin = db.relationship('Transactions', backref='owner_admin', foreign_keys='Transactions.id_admin', lazy='dynamic')
    transactions_as_member = db.relationship('Transactions', backref='owner_member', foreign_keys='Transactions.id_member', lazy='dynamic')
    def is_authenticated(self):
        return True
    def is_active(self):
        return True
    def is_anonymous(self):
        return False
    def get_id(self):
        return str(self.id_user)
    
class Transactions(db.Model):
    id_transaction = db.Column(db.String(5), primary_key=True, default=db.text("CONCAT('NT', LPAD(nextval('transactions_id_transaction_seq')::text, 3, '0'))"))
    id_admin = db.Column(db.Integer, db.ForeignKey('users.id_user'), nullable=False)
    id_member = db.Column(db.Integer, db.ForeignKey('users.id_user'), nullable=False)
    borrowing_date = db.Column(db.TIMESTAMP, nullable=False)
    related_transaction_books = db.relationship('TransactionBooks', backref='owner_transaction', lazy='dynamic')

class TransactionBooks(db.Model):
    id_transaction_book = db.Column(db.Integer, primary_key=True)
    id_transaction = db.Column(db.String(5), db.ForeignKey('transactions.id_transaction'), primary_key=True)
    id_book = db.Column(db.String(5), db.ForeignKey('books.id_book'), primary_key=True)
    return_date = db.Column(db.TIMESTAMP, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

@app.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return {'message': 'You are already logged in'}
    
    username = request.headers.get('username')
    password = request.headers.get('password')

    user = Users.query.filter_by(username=username).first()
    if user and user.password == password:
        login_user(user)
        return {'message': 'Login successful'}
    else:
        return {'message': 'Invalid username or password'}, 401

@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    return {'message': 'Logout successful'}

@app.route("/settings", methods=["GET"])
@login_required
def settings():
    user = Users.query.filter_by(username=current_user.username).first()
    return {'message': f'Welcome, {user.username}!'}

@app.route("/profile", methods=["GET"])
@login_required
def profile():
    name = current_user.username
    return {'message': f'Welcome, {name}!'}

@app.route('/books', methods=['GET'])
@login_required
def view_books():
    data = Books.query.order_by(Books.id_book.desc()).all()
    books_list = []
    for el in data:
        books_list.append({
            'id_book': el.id_book,
            'title': el.title,
            'author': el.author,
            'year': el.year,
            'total_pages': el.total_pages,
            'category': el.category,
            'owner': {
                'author': el.owner_author.name,
                'category': el.owner_category.name
            }
            
        })
    return {'books': books_list}

@app.route('/books', methods=['POST'])
@login_required
def add_books():
    if current_user.user_type == 'admin':
        data = Books(
            title=request.form['title'],
            author=request.form['author'],
            year=request.form['year'],
            total_pages=request.form['total_pages'],
            category=request.form['category']
        )
        db.session.add(data)
        db.session.commit()
        return jsonify({'message': 'Book added'})
    else:
        return jsonify({'message': 'Access denied'})

@app.route('/books', methods=['PUT'])
@login_required
def update_books():
    if current_user.user_type == 'admin':
        data = Books.query.get(request.form['id_book'])
        data.title = request.form['title']
        data.author = request.form['author']
        data.year = request.form['year']
        data.total_pages = request.form['total_pages']
        data.category = request.form['category']
        db.session.commit()
        return jsonify({'message': 'Book updated'})
    else:
        return jsonify({'message': 'Access denied'})

@app.route('/books', methods=['DELETE'])
@login_required
def delete_books():
    if current_user.user_type == 'admin':
        data = Books.query.get(request.form['id_book'])
        db.session.delete(data)
        db.session.commit()
        return jsonify({'message': 'Book deleted'})
    else:
        return jsonify({'message': 'Access denied'})

@app.route('/users', methods=['GET'])
@login_required
def view_users():
    if current_user.user_type == 'admin':
        data = Users.query.order_by(Users.id_user.desc()).all()
        users_list = []
        for el in data:
            users_list.append({
                'id_user': el.id_user,
                'username': el.username,
                'password': el.password,
                'user_type': el.user_type
            })
        return {'users': users_list}
    else:
        return jsonify({'message': 'Access denied'})

@app.route('/users', methods=['POST'])
@login_required
def add_users():
    if current_user.user_type == 'admin':
        data = Users(
            username = request.form['username'],
            password = request.form['password'],
            user_type = request.form['user_type']
        )
        db.session.add(data)
        db.session.commit()
        return jsonify({'message': 'User added'})
    else:
        return jsonify({'message': 'Access denied'})

@app.route('/users_member', methods=['POST'])
@login_required
def add_users_member():
    if current_user.user_type == 'member':
        data = Users(
            username=request.form['username'],
            password=request.form['password'],
            user_type='member'
        )
        db.session.add(data)
        db.session.commit()
        return jsonify({'message': 'User added'})
    else:
        return jsonify({'message': 'Access denied'})

@app.route('/users', methods=['PUT'])
@login_required
def update_users():
    if current_user.user_type == 'admin':
        data = Users.query.get(request.form['id_user'])
        data.username = request.form['username']
        data.password = request.form['password']
        data.user_type = request.form['user_type']
        db.session.commit()
        return jsonify({'message': 'User updated'})
    else:
        return jsonify({'message': 'Access denied'})

@app.route('/users', methods=['DELETE'])
@login_required
def delete_users():
    if current_user.user_type == 'admin':
        data = Users.query.get(request.form['id_user'])
        db.session.delete(data)
        db.session.commit()
        return jsonify({'message': 'User deleted'})
    else:
        return jsonify({'message': 'Access denied'})

@app.route('/transactions', methods=['GET'])
@login_required
def view_transactions():
    if current_user.user_type == 'admin':
        data = Transactions.query.order_by(Transactions.id_transaction.desc()).all()
        transactions_list = []
        for el in data:
            transactions_list.append({
                'id_transaction': el.id_transaction,
                'id_admin': el.id_admin,
                'id_member': el.id_member,
                'borrowing_date': el.borrowing_date,
                'owner': {
                    'id_admin': el.owner_admin.username,
                    'id_member': el.owner_member.username
                }
            })
        return {'transactions': transactions_list}
    else:
        return jsonify({'message': 'Access denied'})

@app.route('/transactions', methods=['POST'])
@login_required
def add_transactions():
    if current_user.user_type == 'admin':
        data = Transactions(
            id_admin = request.form['id_admin'],
            id_member = request.form['id_member'],
            borrowing_date = request.form['borrowing_date']
        )
        db.session.add(data)
        db.session.commit()
        return jsonify({'message': 'Transaction added'})
    else:
        return jsonify({'message': 'Access denied'})

@app.route('/transactions', methods=['PUT'])
@login_required
def update_transactions():
    if current_user.user_type == 'admin':
        data = Transactions.query.get(request.form['id_transaction'])
        data.id_admin = request.form['id_admin']
        data.id_member = request.form['id_member']
        data.borrowing_date = request.form['borrowing_date']
        db.session.commit()
        return jsonify({'message': 'Transaction updated'})
    else:
        return jsonify({'message': 'Access denied'})

@app.route('/transactions', methods=['DELETE'])
@login_required
def delete_transactions():
    if current_user.user_type == 'admin':
        data = Transactions.query.get(request.form['id_transaction'])
        db.session.delete(data)
        db.session.commit()
        return jsonify({'message': 'Transaction deleted'})
    else:
        return jsonify({'message': 'Access denied'})

@app.route('/transaction_books', methods=['GET'])
@login_required
def view_transaction_books():
    if current_user.user_type == 'admin':
        data = TransactionBooks.query.order_by(TransactionBooks.id_transaction_book.desc()).all()
        transaction_books_list = []
        for el in data:
            transaction_books_list.append({
                'id_transaction_book': el.id_transaction_book,
                'id_transaction': el.id_transaction,
                'id_book': el.id_book,
                'return_date': el.return_date,
                'owner': {
                    'id_book': el.owner_book.title,
                    'id_transaction': el.owner_transaction.borrowing_date
                }
            })
        return {'transaction_books': transaction_books_list}
    else:
        return jsonify({'message': 'Access denied'})

@app.route('/transaction_books', methods=['POST'])
@login_required
def add_transaction_books():
    if current_user.user_type == 'admin':
        data = TransactionBooks(
            id_transaction = request.form['id_transaction'],
            id_book = request.form['id_book'],
            return_date = request.form['return_date']
        )
        db.session.add(data)
        db.session.commit()
        return jsonify({'message': 'Transaction Books added'})
    else:
        return jsonify({'message': 'Access denied'})

@app.route('/transaction_books', methods=['PUT'])
@login_required
def update_transaction_books():
    if current_user.user_type == 'admin':
        id_transaction_book = request.form['id_transaction_book']
        id_transaction = request.form['id_transaction']
        id_book = request.form['id_book']

        data = TransactionBooks.query.get((id_transaction_book, id_transaction, id_book))
        if data:
            data.return_date = request.form['return_date']
            db.session.commit()
            return jsonify({'message': 'Transaction Books updated'})
        else:
            return jsonify({'message': 'Transaction Books not found'})
    else:
        return jsonify({'message': 'Access denied'})

@app.route('/transaction_books', methods=['DELETE'])
@login_required
def delete_transaction_books():
    if current_user.user_type == 'admin':
        id_transaction_book = request.form.get('id_transaction_book')
        id_transaction = request.form.get('id_transaction')
        id_book = request.form.get('id_book')

        if id_transaction_book and id_transaction and id_book:
            data = TransactionBooks.query.get((id_transaction_book, id_transaction, id_book))
            if data:
                db.session.delete(data)
                db.session.commit()
                return jsonify({'message': 'Transaction Books deleted'})
            else:
                return jsonify({'message': 'Transaction Books not found'})
        else:
            return jsonify({'message': 'Missing required form data'})
    else:
        return jsonify({'message': 'Access denied'})

if __name__ == '__main__':
    app.run(debug=True)