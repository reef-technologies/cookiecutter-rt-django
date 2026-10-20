"""Interpreter start hook of the production image.

Python imports ``sitecustomize`` on startup when it can be found on ``sys.path``.  The
production image sets ``PYTHONPATH=/root/src``, so this runs first in every Python
process of the image, before any application code.  Development setups do not set
``PYTHONPATH``, so it is inert there.

If this raises, Python prints "Error in sitecustomize" and starts the process anyway.
"""

import memray_autostart

memray_autostart.autostart()
