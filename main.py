import os
from flask import Flask, request, Response, render_template
import google.auth
import google.cloud.logging
from xialib.service import service_factory
from pyinsight import Insight, Cleaner

# Global Setting
app = Flask(__name__)
project_id = google.auth.default()[1]

global_connectors = service_factory({})
insight_config = {}
Insight.set_internal_channel(messager=global_connectors.get(insight_config['publisher']),
                             channel=insight_config['insight']['control_channel'],
                             topic_cockpit=insight_config['insight']['control_topics']['cockpit'],
                             topic_cleaner=insight_config['insight']['control_topics']['cleaner'],
                             topic_merger=insight_config['insight']['control_topics']['merger'],
                             topic_packager=insight_config['insight']['control_topics']['packager'],
                             topic_loader=insight_config['insight']['control_topics']['loader'],
                             topic_backlog=insight_config['insight']['control_topics']['backlog']
)

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

    cleaner = service_factory({}, global_connectors)
    if cleaner.clean_data(data_header['topic_id'], data_header['table_id'], data_header['start_seq']):
        return "clean message received", 200
    else:  # pragma: no cover
        return "clean message to be resent", 400  # pragma: no cover

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))  # pragma: no cover