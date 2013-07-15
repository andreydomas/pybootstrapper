from flask import Blueprint, render_template

import models

mod = Blueprint('events', __name__, url_prefix='/events')

@mod.route('/', methods=['GET'])
def list():
    events = models.PyBootstrapperEvent.query \
                                       .order_by(models.PyBootstrapperEvent.created.desc()) \
                                       .all()

    return render_template('events/list.html', events=events)
