from flask import Blueprint

import models

mod = Blueprint('nodes', __name__, url_prefix='/nodes')

@mod.route('/', methods=['GET'])
def list():
    pass
