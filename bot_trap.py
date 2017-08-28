import string
import random
import sys
from flask import Flask
from gevent import monkey
monkey.patch_all()

app = Flask(__name__)


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


@app.route('/')
@app.route('/<trap>')
def bot(discard=None, trap=None):
    response = "<html>\n"
    response += "<head>\n"
    response += "<body>\n"
    for i in range(1, 50):
        response += '<a href="http://localhost:5000/' + id_generator(50) + '">trap</a><br>\n'
    response += "</body>\n"
    response += "</head>\n"
    response += "</html>\n"
    return response



def main():
    app.run(host='0.0.0.0', debug=True)

if __name__ == "__main__":
    sys.exit(main())