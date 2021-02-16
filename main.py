from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
from keras.models import load_model
from PIL import Image
import requests
import numpy as np
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'app'

mysql = MySQL(app)
model = load_model('model.h5')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return render_template('submit.html', account=account)
        else:
            return render_template('login.html', msg='')

    return render_template('login.html', msg='')


@app.route('/user/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/user/submit', methods=['GET'])
def imageGet():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        return render_template('submit.html', account=account)

    return redirect(url_for('login'))


@app.route('/user/submit', methods=['POST'])
def image():
    if 'loggedin' in session:
        url = request.form['imageUrl']
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        image = np.array(image)
        image = image.reshape((1, 784)).astype('float32')
        image /= 255
        y_labels = [[1., 0., 0., 0., 0., 0., 0., 0., 0., 0.],
                    [0., 1., 0., 0., 0., 0., 0., 0., 0., 0.],
                    [0., 0., 1., 0., 0., 0., 0., 0., 0., 0.],
                    [0., 0., 0., 1., 0., 0., 0., 0., 0., 0.],
                    [0., 0., 0., 0., 1., 0., 0., 0., 0., 0.],
                    [0., 0., 0., 0., 0., 1., 0., 0., 0., 0.],
                    [0., 0., 0., 0., 0., 0., 1., 0., 0., 0.],
                    [0., 0., 0., 0., 0., 0., 0., 1., 0., 0.],
                    [0., 0., 0., 0., 0., 0., 0., 0., 1., 0.],
                    [0., 0., 0., 0., 0., 0., 0., 0., 0., 1.]]

        result = []
        for i in range(0, 10):
            result.append(model.evaluate(image, np.array([y_labels[i]]), verbose=1))
            print(result[i])

        return render_template('result.html', number=result)
    else:
        return redirect(url_for('login'))


@app.errorhandler(Exception)
def all_exception_handler(error):
    return 'Error', 404
