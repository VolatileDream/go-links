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

def render(template, **kwargs):
  return render_template(template,
                         base_host=app.config['HOST_BASE'],
                         quick_host=app.config['HOST_QUICK'],
                         **kwargs)

# Really this should be a separate server that
# responds to all `goto` domain requests instead
# of having this built into the `go` server.
@app.before_request
def maybe_rewrite_for_goto_domain():
  url_delims = [':', '.']
  base = app.config['HOST_BASE']
  quick = app.config['HOST_QUICK']

  host = request.host
  force_goto = request.args.get('force_goto')
  if force_goto or host == quick or \
      (host.startswith(quick) and len(host) > len(quick) and host[len(quick)] in url_delims):
    # Redirect to go, assuming it resolves to where this request landed.
    # Note: this assumes the service is reachable __without__ specifying a port.
    url = "{scheme}://{hostname}/to{path}".format(
        scheme=request.scheme,
        hostname=base,
        # Path starts with '/' hence the above weirdness.
        path=request.full_path)
    return redirect(url)


@app.route('/')
def index():
  return redirect('/list')

@app.route('/new')
def create_link():
  return render('new.html')

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
    return render('edit.html', name=name, dest=current, mode="edit")

  if mode == "create" and current:
    # Attempted a create that already existed.
    return render('edit.html', name=name, dest=current, error="exists", mode="edit")

  with storage.transaction():
    redirects().put(name, dest)

  return render('edit.html', name=name, dest=dest, success=True, mode="edit")

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

  return render('delete.html', name=name, dest=current)

@app.route('/list')
def list_links():
  links = [{"id": i[0], "target": i[1]} for i in redirects().list()]
  return render("listing.html", listing=links)

@app.route('/to/')
@app.route('/to/<path:wildcard>')
def redirector(wildcard=""):
  # for convenience, because the empty string can't be registered.
  if not wildcard:
    base = app.config['HOST_BASE']
    quick = app.config['HOST_QUICK']
    return redirect(request.url_root.replace(quick, base, 1))

  redir = redirects().get(wildcard)
  if redir:
    with storage.transaction():
      val = counts().get(wildcard) or 0
      counts().put(wildcard, val + 1)
    return redirect(redir)
  abort(404)

def create_app():
  return app
