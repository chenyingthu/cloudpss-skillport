"""
viz_renderers: Auto-register all result renderers.

Importing this package triggers registration of all renderer modules
via their @register_renderer decorators.
"""
from web.components.viz_renderers import power_flow       # noqa: F401
from web.components.viz_renderers import emt_simulation    # noqa: F401
from web.components.viz_renderers import n1_security       # noqa: F401
from web.components.viz_renderers import generic           # noqa: F401
from web.components.viz_renderers import pipeline          # noqa: F401
from web.components.viz_renderers import vsi_weak_bus      # noqa: F401
from web.components.viz_renderers import short_circuit     # noqa: F401
from web.components.viz_renderers import emt_fault_study   # noqa: F401
