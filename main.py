import requests, json
from flask import Flask, abort, render_template, request, redirect
from putato.putato import Storage

app = Flask(__name__)
app.config.from_pyfile("config.py")
storage = Storage(app.config['DB_FILE'])

from functools import wraps
# "Magic" to create tables from empty functions
# eg:
#    @get_table
#    def table_name():
#      pass
def get_table(func):
  @wraps(func)
  def table():
    name = "table_" + func.__name__
    t = getattr(request, "table_" + name, None)
    if t is None:
      t = storage.table(func.__name__)
      setattr(request, name, t)
    return t
  return table

@get_table
def redirects():
  pass

@get_table
def counts():
  pass

# Really this should be a separate server that
# responds to all `goto` domain requests instead
# of having this built into the `go` server.
@app.before_request
def maybe_rewrite_for_goto_domain():
  host = request.host
  force_goto = request.args.get('force_goto')
  if host.startswith('goto.') or host.startswith("goto:") or host == "goto" or force_goto:
    # Redirect to go, assuming it resolves to where this request landed.
    return request.url_root.replace("goto", "go", 1) + "to" + request.full_path

@app.route('/')
def index():
  return redirect('/list')

@app.route('/new')
def create_link():
  return render_template('new.html')

@app.route('/edit', methods=['GET', 'POST'])
def create_or_edit_link():
  name = request.values.get('name', None)
  dest = request.values.get('dest', "")
  # both edit & new post to this spot.
  # They need to be differentiated.
  mode = request.values.get('mode', "create")

  if not name:
    return redirect('create_link')

  current = redirects().get(name)
  if current is None:
    current = ""

  if request.method == 'GET':
    return render_template('edit.html', name=name, dest=current, mode="edit")

  if mode == "create" and current:
    # Attempted a create that already existed.
    return render_template('edit.html', name=name, dest=current, error="exists", mode="edit")

  with storage.transaction():
    redirects().put(name, dest)

  return render_template('edit.html', name=name, dest=dest, success=True, mode="edit")

@app.route('/delete', methods=['POST'])
def delete():
  name = request.values.get('name', None)

  if not name:
    return redirect('/list')
 
  current = redirects().get(name)
  if current is None:
    current = ""

  with storage.transaction():
    redirects().remove(name)

  return render_template('delete.html', name=name, dest=current)

@app.route('/list')
def list_links():
  links = [{"id": i[0], "target": i[1]} for i in redirects().list()]
  return render_template("listing.html", listing=links)

@app.route('/to/<path:wildcard>')
def redirector(wildcard):
  redir = redirects().get(wildcard)
  if redir:
    with storage.transaction():
      val = counts().get(wildcard) or 0
      counts().put(wildcard, val + 1)
    return redirect(redir)
  abort(404)

def create_app():
  return app
