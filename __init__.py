import os
import string
import random
import logging
import subprocess

from flask import Flask
from flask import request
from flask import jsonify
from flask_cors import CORS
from flask_cors import cross_origin

# from flask_mail import Mail, Message

from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename


from flask_tacos.crossdomain import crossdomain

from flask_tacos.db import get_db
from flask_tacos.db import init_app

# mail_settings = {
#     "MAIL_SERVER": 'mail.coli.uni-saarland.de',
#     "MAIL_PORT": 465,
#     "MAIL_USE_TLS": False,
#     "MAIL_USE_SSL": True,
#     "MAIL_USERNAME": "moritzw",
#     "MAIL_PASSWORD": ""
#     "MAIL_DEBUG": True
# }
fee_path = "/home/tacos2019/flask_tacos/fees.txt" #"/Users/mo/Dropbox/Uni/TaCos/flask_tacos/fees.txt" # "/home/tacos2019/flask_tacos/fees.txt"

UPLOAD_FOLDER = '/home/tacos2019/talk_papers'
ALLOWED_EXTENSIONS = set(['txt', 'pdf'])


def create_app(test_config=None):
    
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    # app.config.update(mail_settings)
    # mail = Mail(app)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    app.config['CORS_HEADERS'] = 'Content-Type'

    CORS(app)
    # a simple page that says hello
    #@app.route('/hello')
    #def hello():
    #    return 'Hello, World!'

    @app.route('/register', methods=["POST", "OPTIONS"])
    #@crossdomain(origin="*")
    def register():
        response={}

        email = request.form['email']
        given_name = request.form['given_name']
        surname = request.form['surname']
        nutrition = request.form['nutrition']
        busticket = "ticket" in request.form

        # check if something is missing
        formTags = ["email", "given_name", "surname", "nutrition"]
        for tag in formTags:
             if request.form[tag] == "" or request.form[tag] is None:
                response['status']='ERROR'
                response['message']="Please fill in your " + tag[0].upper() + tag[1:]
                app.logger.info('Register error '+ tag)
                return jsonify(response)
        # check if user is already registered
        db = get_db()
        if db.execute(
            'SELECT id FROM user WHERE email = ?', (email,)
        ).fetchone() is not None:
            response['status']='ERROR'
            response['message'] = 'User {0} is already registered.'.format(email)
            return jsonify(response)
        else:
            check = True
            # generate new uid
            uid = ''.join(random.choice(string.ascii_letters) for _ in range(8))
            while check:
                if db.execute('SELECT id FROM user WHERE id = ?', (uid,)).fetchone() is not None:
                    uid = ''.join(random.choice(string.ascii_letters) for _ in range(8))
                else:
                    check = False
            
            # insert new user into db
            db.execute(
                'INSERT INTO user (id, email, given_name, surname, nutrition, busticket) VALUES (?, ?, ?, ?, ?, ?)',
                (uid, email, given_name, surname, nutrition, busticket)
            )
            db.commit()
            response['status']='OK'
            response['message']="Successfully registered"

            # build email text
            html_message = "Hello {0},<br>".format(given_name)
            html_message += "Thank you for registering for TaCoS29!<br>"
            html_message += "Your code is {0}.<br><br>".format(uid)
            html_message += "If you want to check your registration status enter your code under ''Check Registration Status'' on <a href='https://tacos2019.coli.uni-saarland.de/registration/'>https://tacos2019.coli.uni-saarland.de/registration/</a><br>"
            html_message += "To complete your registration send us X €. Please also consider presenting something: <a href='https://tacos2019.coli.uni-saarland.de/call/'>https://tacos2019.coli.uni-saarland.de/call/</a><br><br>"
            html_message += "IBAN: de123456789xxxx<br>"
            html_message += "BIC: XXXXXXXXXXX<br>"
            html_message += "Reference (Verwendungszweck): {0}<br>".format(uid)
            html_message += "Amount (Betrag): 10000000€<br><br>".format(uid)
            html_message += "Best,<br>Your TaCoS team"

            # send email via terminal (a bit hacky but with this we don't need to save the password
            # and flask-mail didn't want to work on the server)
            echo = subprocess.Popen(["echo", "",html_message, ""], stdout=subprocess.PIPE)
            output = subprocess.check_output(["mail", "-s", "TaCoS29 registration", "-a", "Content-type: text/html", email], stdin=echo.stdout)
            app.logger.debug('Email sent '+ str(output))

            response['status']='OK'
            response['message']="Successfully registered"
            app.logger.info(" ".join([email, uid, 'has succesfully registered']))

            return jsonify(response)
        return jsonify(response)

    @app.route('/talk', methods=["POST", "OPTIONS"])
    # @crossdomain(origin="*")
    def talk():
        response = {}

        uid = request.form['uid']
        title = request.form['title']
        subtitle = request.form['subtitle']
        presentation = request.form['presentation']
        description = request.form['description']
        app.logger.info(request.form)

        for f in request.files:
            app.logger.info(f)
            request.files[f].save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(uid + request.files[f].filename)))
        return "N/A"



    @app.route('/fee', methods=["GET"])
    @crossdomain(origin="*")
    def fee():

        uid = request.args.get('uid')
        if uid is not None and uid != "":
            
            #check in some textfile
            with open(fee_path, "r") as f:
                for feeid in f:
                    if feeid.strip() == uid.strip():
                        return "You are registered and your fee is paid. :)"
            db = get_db()
            if db.execute('SELECT id FROM user WHERE id = ?', (uid,)
                ).fetchone() is not None:
                return "You are registered, but we didn't receive your fee yet."
            else:
                return "You are not registered yet. Please register above."
        else:
            return "Please insert a code."
        return "N/A"

    @app.route('/test', methods=["GET"])
    @crossdomain(origin="*")
    def test():
        # app.logger.debug('this is a DEBUG message')
        # app.logger.info('this is an INFO message')
        # app.logger.warning('this is a WARNING message')
        # app.logger.error('this is an ERROR message')
        # app.logger.critical('this is a CRITICAL message')
        uid = ''.join(random.choice(string.ascii_letters) for _ in range(8))

        html_message = "Hello {0},<br>".format(given_name)
        html_message += "Thank you for registering for TaCoS29!<br>"
        html_message += "Your code is {0}.<br><br>".format(uid)
        html_message += "If you want to check your registration status enter your code under ''Check Registration Status'' on <a href='https://tacos2019.coli.uni-saarland.de/registration/'>https://tacos2019.coli.uni-saarland.de/registration/</a><br>"
        html_message += "To complete your registration send us X €. Please also consider presenting something: <a href='https://tacos2019.coli.uni-saarland.de/call/'>https://tacos2019.coli.uni-saarland.de/call/</a><br><br>"
        html_message += "IBAN: de123456789xxxx<br>"
        html_message += "BIC: XXXXXXXXXXX<br>"
        html_message += "Reference (Verwendungszweck): {0}<br>".format(uid)
        html_message += "Amount (Betrag): 10000000€<br><br>".format(uid)
        html_message += "Best,<br>Your TaCoS team"

        echo = subprocess.Popen(["echo", "",html_message, ""], stdout=subprocess.PIPE)
        output = subprocess.check_output(["mail", "-s", "subject", "-a", "Content-type: text/html", "moritzw@coli.uni-saarland.de"], stdin=echo.stdout)
        app.logger.info('email sent '+ str(output))

        # this doesn't work because of the pipe
        # subprocess.call(["echo", html_message, "|", "mail", "-s", "'subject'", "-a", "'Content-type: text/html'", "moritzw@coli.uni-saarland.de"])

        return "N/A"
    
    init_app(app)


    # enable logging
    if __name__ != '__main__':
        gunicorn_logger = logging.getLogger('gunicorn.error')
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)
    
    return app



