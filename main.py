import os
import json
import base64
import gzip
import hashlib
import configparser
from flask import Flask, request, Response, render_template
import google.auth
import google.cloud.logging
from xialib.tools import get_object
from pyinsight import Insight, Cleaner


app = Flask(__name__)

project_id = google.auth.default()[1]

config = configparser.ConfigParser()
config.read('service.ini')

internal_publisher = get_object(**config['internal_messager'])
internal_messager = get_object(pub_client=internal_publisher, **config['internal_publisher'])
Insight.set_internal_channel(messager=internal_messager,
                             channel=config['insight']['control_channel'],
                             topic_cockpit=config['insight']['topic_cockpit'],
                             topic_cleaner=config['insight']['topic_cleaner'],
                             topic_merger=config['insight']['topic_merger'],
                             topic_packager=config['insight']['topic_packager'],
                             topic_loader=config['insight']['topic_loader'],
                             topic_backlog=config['insight']['topic_backlog']
)

depositor_db = get_object(**config['depositor.db'])
archiver_storer = get_object(**config['archiver.storer'])

client = google.cloud.logging.Client()
client.get_default_handler()
client.setup_logging()

@app.route('/', methods=['GET', 'POST'])
def insight_cleaner():
    if request.method == 'GET':
        return render_template("index.html"), 200
    envelope = request.get_json()
    if not envelope:
        return "no Pub/Sub message received", 204
    if not isinstance(envelope, dict) or 'message' not in envelope:
        return "invalid Pub/Sub message format", 204
    data_header = envelope['message']['attributes']

    global depositor_db
    global archiver_storer
    depositor = get_object(db=depositor_db, **config['depositor'])
    archiver = get_object(storer=archiver_storer, **config['archiver'])
    cleaner = Cleaner(archiver=archiver, depositor=depositor)

    if cleaner.clean_data(data_header['topic_id'], data_header['table_id'], data_header['start_seq']):
        return "clean message received", 200
    else:  # pragma: no cover
        return "clean message to be resent", 400  # pragma: no cover

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))  # pragma: no cover