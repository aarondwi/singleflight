"""
Coalesce multiple identical call into one, preventing thundering-herd/stampede to database/other backends

python port of https://github.com/golang/groupcache/blob/master/singleflight/singleflight.go
"""

__version__ = "0.1.0"
