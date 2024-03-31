import traceback
import uuid

import humanfriendly
from flask import Flask, request, render_template, abort, send_from_directory
from functools import wraps, update_wrapper
from datetime import datetime
from flask import make_response
import os

from panoptes.database import init_db, db_session
from panoptes.models import Workflows
from panoptes.routes import *
from panoptes.schema_forms import SnakemakeUpdateForm
from panoptes.server_utilities.db_queries import maintain_jobs
from panoptes.other_utilities.log_utils import ansi_to_html

app = Flask(__name__, template_folder="static/src/")
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.register_blueprint(routes)
app.jinja_env.globals.update(get_jobs=get_jobs)
app.jinja_env.globals.update(get_job=get_job)

init_db()


# you can add @nocache in any endpoint to disable caching
def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response

    return update_wrapper(no_cache, view)

@app.route('/')
def index():
    wf = [w.get_workflow() for w in get_db_workflows()]
    info = {
        'workflows': len(wf),
        'completed': sum([1 if w['status'] == 'Done' else 0 for w in wf]),
        'jobs_done': sum([w['jobs_done'] if w['jobs_done'] else 0 for w in wf]),
        'jobs_total': sum([w['jobs_total'] if w['jobs_total'] else 0 for w in wf]),
    }
    return render_template("index.html", info=info)


@app.route('/workflows/')
@nocache
def workflows_page():
    workflows = [w.get_workflow() for w in get_db_workflows()]
    return render_template('workflows.html', workflows=workflows)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contribute')
def contribute():
    return render_template('contribute.html')


@app.route('/searchResults')
@nocache
def search_results():
    userinput = request.args.get('q')
    workflows = [w.get_workflow() for w in get_db_workflows()]
    filteredworkflows = [w for w in workflows if userinput in w['name']]
    alljobs = []
    for wf in workflows:
        jobs = [j.get_job_json() for j in get_db_jobs(wf['id'])]
        filteredjobs = [j for j in jobs if userinput in j['name']]
        alljobs.extend(filteredjobs)

    return render_template('searchResults.html', workflows=filteredworkflows, alljobs=alljobs)


@app.route('/workflow/<id>', methods=['GET'])
@nocache
def get_status(id):
    try:
        workflow = get_db_workflows_by_id(id).get_workflow()

        if workflow:
            return render_template('workflow.html', workflow=workflow)
        else:
            return render_template('404.html')

    except:
        traceback.print_exc()
        return render_template('404.html')


@app.route('/workflow/<wf_id>/job/<job_id>', methods=['GET'])
def get_job_status(wf_id, job_id):
    # get all the job data
    job = get_job(wf_id, job_id)

    # get the log folder
    try:
        # passed from the argument parser --log, uses cwd as default
        log_folder = app.config['LOG_FOLDER']
        # only for pycharm testing:
        # log_folder = '/Users/nquinones/Desktop/snakemake_assembly/logs'
    except:
        # no log folder in the app.config
        log_folder = None

    # new key to store the text of the log files
    job['log_text'] = []

    if log_folder:
        # if the log folder exists
        try:
            # for each log in the list
            for log in job['log']:
                # build the full path
                if log_folder == os.getcwd():
                    # if log dir is the default (cwd)
                    log_path = os.path.join(log_folder, log)
                else:
                    # if log dir is specified, use base name to avoid log/log duplication
                    base_name = os.path.basename(log)
                    log_path = os.path.join(log_folder, base_name)

                # open the log file, read the text, convert to html
                with open(log_path, 'r') as f:
                    log_text = f.read()
                    log_text = ansi_to_html(log_text)
                    # add an entry to the job dictionary
                    job['log_text'].append({'name': log, 'text':log_text})
        except Exception as e:
            # if the log file cannot be read, add an entry to the job dictionary
            job['log_text'].append({'name': '',
                                    'text': f'...could not find/read logs. Tried in: {log_folder} \n Error: {e}'})
    else:
        # if no log folder in the app.config
        # this shouldn't happen if it's being run from panotpes.py
        job['log_text'].append({'name': '',
                                'text': '...no log folder provided'})

    return render_template('job.html',
                           job=job)


@app.route('/create_workflow', methods=['GET'])
def create_workflow():
    try:
        w = Workflows(str(uuid.uuid4()), "Running")
        db_session.add(w)
        db_session.commit()

        return w.get_workflow()
    except:
        traceback.print_exc()
        return render_template('404.html')


@app.route('/update_workflow_status', methods=['POST'])
def update_status():
    update_form = SnakemakeUpdateForm()
    errors = update_form.validate(request.form)

    if errors:
        abort(404, str(errors))
    else:
        r = update_form.load(request.form)
    # now all required fields exist and are the right type
    maintain_jobs(msg=r["msg"], wf_id=r["id"])
    return "ok"


@app.route('/vendor/<path:path>')
def send_vendor(path):
    return send_from_directory('static/vendor', path)


@app.route('/node_modules/<path:path>')
def send_node_modules_charts(path):
    return send_from_directory('static/node_modules', path)


@app.route('/<path:path>')
def send_js(path):
    return send_from_directory('static/src', path)


@app.template_filter('formatdatetime')
def format_datetime(value, format="%d %b %Y %I:%M %p"):
    """Format a date time to (Default): d Mon YYYY HH:MM P"""
    if value is None:
        return ""
    return value.strftime(format)\



@app.template_filter('formatdelta')
def format_delta(value):
    """Format a date time to (Default): d Mon YYYY HH:MM P"""
    if value is None:
        return ""

    return humanfriendly.format_timespan(value)


@app.errorhandler(Exception)
def handle_bad_request(e):
    return render_template('404.html')


if __name__ == '__main__':
    app.run()
