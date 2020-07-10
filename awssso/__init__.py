from pkg_resources import get_distribution, DistributionNotFound

try:
    __version__ = '1.1.2rev3'
except DistributionNotFound:
    # package is not installed
    pass
