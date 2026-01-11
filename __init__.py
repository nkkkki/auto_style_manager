"""
Auto Style Manager Plugin for QGIS
"""

def classFactory(iface):
    from .auto_style_manager import AutoStyleManager
    return AutoStyleManager(iface)