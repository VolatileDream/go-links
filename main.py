from flask import Flask, abort, escape, request, redirect, url_for
app = Flask(__name__)

import requests, json, config

def can_goto_redirect(request):
  host = request.host
  force_goto = request.args.get('force_goto')
  return host.startswith('goto.') or host.startswith("goto:") or host == "goto" or force_goto

def redirect_to_go_domain(request):
  return request.url_root.replace("goto", "go", 1) + "to" + request.full_path
  
def lookup_redirect(short):
  return url_for('echo', args=short)

# Really this should be a separate server that
# responds to all `goto` domain requests instead
# of having this built into the `go` server.
@app.before_request
def maybe_rewrite_for_goto_domain():
  if can_goto_redirect(request):
    # Redirect to go, assuming it resolves to where this request landed.
    return redirect(redirect_to_go_domain(request))

@app.route('/')
def index():
  return redirect(url_for('list'))

@app.route('/list')
def list():
  return json.dumps(config.REDIRECT)

# Debugging endpoint.
@app.route('/echo/<path:args>')
def echo(args):
  return "echo: " + args

@app.route('/to/<path:wildcard>')
def redirector(wildcard):
  redir = config.REDIRECT.get(wildcard)
  if redir:
    return redirect(redir)
  abort(404)

def create_app():
  return app
