# go-links
==========

A small (and insecure) short-linking service.

## Running

 * Run `./install` to install python dependencies (requires virtualenv).
 * Update `short-links.service` to have the correct path to the ./start executable, and user.
 * Change the `-b 127.0.0.1` to `-b 0.0.0.0` if you want it to be network accessible.
 * Copy `short-links.service` into `/etc/systemd/system/`
 * Make `go` and `goto` resolve to the device hosting it.
   Either by adding `hosts-fragment.txt` to `/etc/hosts`,
   or some other way if available to the network.

## Configuring

You can change where the database file is located, in addition to the two
domains (`go`, `goto` by default) that the services uses by editing
`config.py`.
