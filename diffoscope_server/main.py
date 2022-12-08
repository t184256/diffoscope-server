# SPDX-FileCopyrightText: 2022 Alexander Sosedkin <monk@unboiled.info>
# SPDX-License-Identifier: AGPL-3.0-or-later

import functools
import hashlib
import os
import subprocess

import flask
import werkzeug.utils


FILES_FOLDER = '/var/lib/diffoscope-server/files'
HASHES_FOLDER = '/var/lib/diffoscope-server/hashes'


def sanitize(*fnames):
    for f in fnames:
        assert f
        assert '/' not in f
    return [werkzeug.utils.secure_filename(f) for f in fnames]


def calc_hash_file(fname, uploader):
    sha256 = hashlib.sha256()
    with open(os.path.join(FILES_FOLDER, fname, uploader), 'rb') as f:
        while True:
            data = f.read(4096)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()


def hash_file(fname, uploader):
    if os.path.exists(fname + '.hash'):
        with open(os.path.join(HASHES_FOLDER, fname, uploader), 'r') as f:
            return f.read()
    else:
        os.makedirs(os.path.join(HASHES_FOLDER, fname), exist_ok=True)
        h = calc_hash_file(fname, uploader)
        with open(os.path.join(HASHES_FOLDER, fname, uploader), 'w') as f:
            f.write(h)
        return h


def create_app(config=None):
    app = flask.Flask(__name__)

    @app.route('/')
    def root():
        os.makedirs(FILES_FOLDER, exist_ok=True)
        os.makedirs(HASHES_FOLDER, exist_ok=True)
        r = '<pre>'
        for f in sorted(os.listdir(FILES_FOLDER)):
            us = sorted(os.listdir(os.path.join(FILES_FOLDER, f)))
            if not us:
                continue
            r += '<table style="border: 1px solid black">'
            r += f'<tr><th>{f}</th>'
            for u in us:
                r += f'<th style="text-align: center">{u}</th>'
            r += '</tr>'
            for u1 in us:
                r += '<tr>'
                r += f'<td>'
                r += f'<a style="color: grey" href="/remove/{f}/{u1}">'
                r += f'[del]</font></a>'
                r += f'<b>{u1}</b></td>'
                for u2 in us:
                    if u1 == u2:
                        r += f'<td></td>'
                    elif hash_file(f, u1) == hash_file(f, u2):
                        r += f'<td style="background-color: #e4ffc7;'
                        r += f' text-align: center">'
                        r += 'match</td>'
                    else:
                        r += f'<td style="background-color: #ffe0e0;'
                        r += f' text-align: center">'
                        r += f'<a style="color: black"'
                        r += f' href="/diff/{f}/{u1}/{u2}">'
                        r += 'diff</a></td>'
                r += '</tr>'
            r += '</table><br/>'
        r += '</pre>'
        return r

    @app.route('/remove/<fname>/<uploader>')
    def remove_file(fname, uploader):
        fname, uploader = sanitize(fname, uploader)
        if os.path.exists(os.path.join(FILES_FOLDER, fname, uploader)):
            assert '/' not in fname, '/' not in uploader
            os.unlink(os.path.join(HASHES_FOLDER, fname, uploader))
            os.unlink(os.path.join(FILES_FOLDER, fname, uploader))
            return flask.redirect('/')
        return f'{fname} by {uploader} does not exist\n', 400

    @app.route('/diff/<fname>/<uploader1>/<uploader2>')
    def diff(fname, uploader1, uploader2):
        fname, uploader1, uploader2 = sanitize(fname, uploader1, uploader2)
        if not os.path.exists(os.path.join(FILES_FOLDER, fname, uploader1)):
            return f'{fname} by {uploader1} does not exist\n', 400
        if not os.path.exists(os.path.join(FILES_FOLDER, fname, uploader2)):
            return f'{fname} by {uploader2} does not exist\n', 400
        s = subprocess.Popen((
            'diffoscope', '--html', '-',
            os.path.join(fname, uploader1),
            os.path.join(fname, uploader2),
        ), cwd=FILES_FOLDER, stdout=subprocess.PIPE)
        return flask.send_file(s.stdout, mimetype='text/html')


    @app.route('/upload', methods=['GET', 'POST'])
    def upload_file():
        os.makedirs(FILES_FOLDER, exist_ok=True)
        os.makedirs(HASHES_FOLDER, exist_ok=True)
        if flask.request.method == 'POST':
            if 'uploader' not in flask.request.form:
                return 'No uploader part\n', 400
            uploader, = sanitize(flask.request.form['uploader'])

            if 'file' not in flask.request.files:
                return 'No file part\n', 400
            file = flask.request.files['file']
            if file.filename == '':
                return 'No selected file\n', 400
            if file:
                filename, = sanitize(file.filename)
                os.makedirs(os.path.join(FILES_FOLDER, filename),
                            exist_ok=True)
                file.save(os.path.join(FILES_FOLDER, filename, uploader))
                new_hash = hash_file(filename, uploader)
                matches = []
                for u in os.listdir(os.path.join(FILES_FOLDER, filename)):
                    if u != uploader and new_hash == hash_file(filename, u):
                        matches.append(u)
                r = f'Upload of {filename} successful, '
                if not matches:
                    r += '0 matches'
                elif len(matches) == 1:
                    r += f'1 match: {matches[0]}'
                else:
                    r += f'{len(matches)} matches: ' + ' '.join(matches)
                root = flask.url_for('root', _external=True)
                return r + f'.\nCheck out {root} for comparisons.\n'

        return '''
        <!doctype html>
        <title>Upload new file</title>
        <h1>Upload new file</h1>
        <form method=post enctype=multipart/form-data>
          <input type=file name=file>
          <input type=input name=uploader>
          <input type=submit value=upload>
        </form>
        '''

    return app


def main():
    app = create_app()
    app.run(host='0.0.0.0', port=8080)  # debugging server for development


if __name__ == '__main__':
    main()
