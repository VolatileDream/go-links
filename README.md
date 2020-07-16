# go-links
==========

A small (and insecure) short-linking service.

## Running

 * Run `./install` to install python dependencies (requires virtualenv).
 * Update `short-links.service` to have the correct path to the ./start executable.
 * Copy `short-links.service` into `/etc/systemd/system/`
 * Make `go` and `goto` resolve to the device hosting it.

## Configuring

You can change where the database file is located, in addition to the two
domains (`go`, `goto` by default) that the services uses by editing
`config.py`.
