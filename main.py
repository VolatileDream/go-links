from flask import Flask, abort, current_app, escape, render_template, request, redirect, url_for
from putato.putato import Storage, Transaction, Table

app = Flask(__name__)
app.config.from_pyfile("config.py")
storage = Storage(app.config['DB_FILE'])
table = storage.table('r')

import requests, json

def use_config():
  return current_app.config.get('STORAGE') == "config"

def lookup_redirect(short):
  return table.get(short)

def list_redirects():
  # needs to output [{ id: "...", target: "..."}, ...]
  def convert(items):
    return { "id": items[0], "target": items[1] }
  return [convert(i) for i in table.list()]

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

  current = table.get(name)
  if current is None:
    current = ""

  if request.method == 'GET':
    return render_template('edit.html', name=name, dest=current, mode="edit")

  if mode == "create" and current:
    # Attempted a create that already existed.
    return render_template('edit.html', name=name, dest=current, error="exists", mode="edit")

  with storage.transaction():
    table.put(name, dest)

  return render_template('edit.html', name=name, dest=dest, success=True, mode="edit")

@app.route('/delete', methods=['POST'])
def delete():
  name = request.values.get('name', None)

  if not name:
    return redirect('/list')
 
  current = table.get(name)
  if current is None:
    current = ""

  with storage.transaction():
    table.remove(name)

  return render_template('delete.html', name=name, dest=current)

@app.route('/list')
def list_links():
  return render_template("listing.html", listing=list_redirects())
  return json.dumps(list_redirects())

# Debugging endpoint.
@app.route('/echo/<path:args>')
def echo(args):
  return "echo: " + args

@app.route('/to/<path:wildcard>')
def redirector(wildcard):
  redir = lookup_redirect(wildcard)
  if redir:
    return redirect(redir)
  abort(404)

def create_app():
  return app
