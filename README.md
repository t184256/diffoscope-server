# diffoscope-server

A trivial Flask app that allows several people to compare files over network
with ease.
Written for [a mini-workshop on reproduciblity](https://github.com/t184256/reproducibility-demo).

Usage example:

```
$ curl -F file=@somefile.bin -F uploader=my_name localhost:8080
Upload of somefile.bin successful, 0 matches.
Check out http://localhost:8080/ for comparisons.
```
