"""
Coalesce multiple identical call into one, preventing thundering-herd/stampede to database/other backends

python port of https://github.com/golang/groupcache/blob/master/singleflight/singleflight.go

This module **does not** provide caching mechanism. Rather, this module can used behind a caching abstraction to deduplicate cache-filling call
"""

__version__ = "0.1.2"
