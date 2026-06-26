from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


@app.route('/contratistas')
def contratistas():
    return render_template('contratistas.html')


@app.route('/legislacion')
def legislacion():
    return render_template('legislacion.html')


if __name__ == '__main__':
    app.run(debug=True, port=5000)
