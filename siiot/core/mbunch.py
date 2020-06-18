def mbunchify(data):
    try:
        from bunch import bunchify
        return bunchify(data)
    except ImportError:
        from munch import munchify
        return munchify(data)


try:
    from bunch import Bunch as MBunch
except ImportError:
    from munch import Munch as MBunch
