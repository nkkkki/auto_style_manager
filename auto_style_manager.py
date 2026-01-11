"""
Auto Style Manager - QGIS Plugin
Automatically applies default styling to raster and vector layers
"""

import os
from qgis.PyQt.QtCore import QSettings, Qt, QByteArray
from qgis.PyQt.QtGui import QIcon, QColor, QPixmap
from qgis.PyQt.QtSvg import QSvgRenderer
from qgis.PyQt.QtWidgets import (QAction, QDialog, QVBoxLayout, QHBoxLayout, 
                                 QGroupBox, QLabel, QSpinBox, QDoubleSpinBox, 
                                 QPushButton, QCheckBox, QComboBox, QTabWidget, 
                                 QWidget, QMessageBox, QLineEdit)
from qgis.core import (QgsProject, QgsRasterLayer, QgsVectorLayer, 
                       QgsWkbTypes, QgsPalLayerSettings, QgsTextFormat, 
                       QgsVectorLayerSimpleLabeling, QgsTextBufferSettings)
from qgis.gui import QgsColorButton


class AutoStyleManagerDialog(QDialog):
    def __init__(self, parent=None, plugin=None):
        super().__init__(parent)
        self.setWindowTitle("Auto Style Manager")
        self.setMinimumWidth(550)
        self.settings = QSettings()
        self.plugin = plugin
        self.initUI()
        self.loadSettings()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        # Create tab widget
        tabs = QTabWidget()
        
        # ==================== RASTER TAB ====================
        raster_tab = QWidget()
        raster_layout = QVBoxLayout()
        
        # Enable raster auto-styling
        self.raster_enabled = QCheckBox("Enable automatic raster styling")
        raster_layout.addWidget(self.raster_enabled)
        
        # Exclude basemaps
        self.exclude_basemaps = QCheckBox("Exclude WMS/XYZ/basemap layers (e.g., Google, OSM)")
        self.exclude_basemaps.setChecked(True)
        raster_layout.addWidget(self.exclude_basemaps)
        
        # Raster opacity
        opacity_group = QGroupBox("Default Raster Opacity")
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Opacity:"))
        self.opacity_spin = QDoubleSpinBox()
        self.opacity_spin.setRange(0.0, 1.0)
        self.opacity_spin.setValue(0.7)
        self.opacity_spin.setSingleStep(0.05)
        self.opacity_spin.setDecimals(2)
        opacity_layout.addWidget(self.opacity_spin)
        opacity_layout.addWidget(QLabel("(0.0 = transparent, 1.0 = opaque)"))
        opacity_layout.addStretch()
        opacity_group.setLayout(opacity_layout)
        raster_layout.addWidget(opacity_group)
        
        raster_layout.addStretch()
        raster_tab.setLayout(raster_layout)
        tabs.addTab(raster_tab, "Raster Layers")
        
        # ==================== VECTOR TAB ====================
        vector_tab = QWidget()
        vector_layout = QVBoxLayout()
        
        # Enable vector auto-styling
        self.vector_enabled = QCheckBox("Enable automatic vector styling")
        vector_layout.addWidget(self.vector_enabled)
        
        # Point styling
        point_group = QGroupBox("Point Layers")
        point_layout = QVBoxLayout()
        
        point_color_layout = QHBoxLayout()
        point_color_layout.addWidget(QLabel("Fill Color:"))
        self.point_color = QgsColorButton()
        self.point_color.setColor(QColor("#e74c3c"))
        point_color_layout.addWidget(self.point_color)
        point_color_layout.addStretch()
        point_layout.addLayout(point_color_layout)
        
        point_size_layout = QHBoxLayout()
        point_size_layout.addWidget(QLabel("Size (mm):"))
        self.point_size = QDoubleSpinBox()
        self.point_size.setRange(0.1, 50)
        self.point_size.setValue(2.5)
        self.point_size.setSingleStep(0.5)
        point_size_layout.addWidget(self.point_size)
        point_size_layout.addStretch()
        point_layout.addLayout(point_size_layout)
        
        point_group.setLayout(point_layout)
        vector_layout.addWidget(point_group)
        
        # Line styling
        line_group = QGroupBox("Line Layers")
        line_layout = QVBoxLayout()
        
        line_color_layout = QHBoxLayout()
        line_color_layout.addWidget(QLabel("Color:"))
        self.line_color = QgsColorButton()
        self.line_color.setColor(QColor("#3498db"))
        line_color_layout.addWidget(self.line_color)
        line_color_layout.addStretch()
        line_layout.addLayout(line_color_layout)
        
        line_width_layout = QHBoxLayout()
        line_width_layout.addWidget(QLabel("Width (mm):"))
        self.line_width = QDoubleSpinBox()
        self.line_width.setRange(0.1, 20)
        self.line_width.setValue(0.4)
        self.line_width.setSingleStep(0.1)
        line_width_layout.addWidget(self.line_width)
        line_width_layout.addStretch()
        line_layout.addLayout(line_width_layout)
        
        line_group.setLayout(line_layout)
        vector_layout.addWidget(line_group)
        
        # Polygon styling
        polygon_group = QGroupBox("Polygon Layers")
        polygon_layout = QVBoxLayout()
        
        poly_fill_layout = QHBoxLayout()
        poly_fill_layout.addWidget(QLabel("Fill Color:"))
        self.polygon_fill = QgsColorButton()
        self.polygon_fill.setColor(QColor(144, 238, 144, 100))
        poly_fill_layout.addWidget(self.polygon_fill)
        poly_fill_layout.addStretch()
        polygon_layout.addLayout(poly_fill_layout)
        
        poly_stroke_layout = QHBoxLayout()
        poly_stroke_layout.addWidget(QLabel("Stroke Color:"))
        self.polygon_stroke = QgsColorButton()
        self.polygon_stroke.setColor(QColor("#2ecc71"))
        poly_stroke_layout.addWidget(self.polygon_stroke)
        poly_stroke_layout.addStretch()
        polygon_layout.addLayout(poly_stroke_layout)
        
        poly_width_layout = QHBoxLayout()
        poly_width_layout.addWidget(QLabel("Stroke Width (mm):"))
        self.polygon_width = QDoubleSpinBox()
        self.polygon_width.setRange(0.1, 10)
        self.polygon_width.setValue(0.4)
        self.polygon_width.setSingleStep(0.1)
        poly_width_layout.addWidget(self.polygon_width)
        poly_width_layout.addStretch()
        polygon_layout.addLayout(poly_width_layout)
        
        polygon_group.setLayout(polygon_layout)
        vector_layout.addWidget(polygon_group)
        
        vector_layout.addStretch()
        vector_tab.setLayout(vector_layout)
        tabs.addTab(vector_tab, "Vector Layers")
        
        # ==================== LABELS TAB ====================
        labels_tab = QWidget()
        labels_layout = QVBoxLayout()
        
        # Enable labels
        self.labels_enabled = QCheckBox("Enable automatic labeling for vector layers")
        labels_layout.addWidget(self.labels_enabled)
        
        labels_layout.addWidget(QLabel("<i>Note: Labels will try common field names like 'name', 'NAME', 'id', etc.</i>"))
        
        # Label field
        field_layout = QHBoxLayout()
        field_layout.addWidget(QLabel("Primary Label Field:"))
        self.label_field = QLineEdit()
        self.label_field.setText("name")
        self.label_field.setPlaceholderText("e.g., name, id, label")
        field_layout.addWidget(self.label_field)
        labels_layout.addLayout(field_layout)
        
        # Font size
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("Font Size (pt):"))
        self.label_size = QDoubleSpinBox()
        self.label_size.setRange(4, 72)
        self.label_size.setValue(10)
        self.label_size.setSingleStep(1)
        font_size_layout.addWidget(self.label_size)
        font_size_layout.addStretch()
        labels_layout.addLayout(font_size_layout)
        
        # Font color
        font_color_layout = QHBoxLayout()
        font_color_layout.addWidget(QLabel("Font Color:"))
        self.label_color = QgsColorButton()
        self.label_color.setColor(QColor("#000000"))
        font_color_layout.addWidget(self.label_color)
        font_color_layout.addStretch()
        labels_layout.addLayout(font_color_layout)
        
        # Buffer
        self.label_buffer = QCheckBox("Enable text buffer (outline)")
        self.label_buffer.setChecked(True)
        labels_layout.addWidget(self.label_buffer)
        
        buffer_size_layout = QHBoxLayout()
        buffer_size_layout.addWidget(QLabel("Buffer Size (mm):"))
        self.buffer_size = QDoubleSpinBox()
        self.buffer_size.setRange(0.1, 10)
        self.buffer_size.setValue(1.0)
        self.buffer_size.setSingleStep(0.1)
        buffer_size_layout.addWidget(self.buffer_size)
        buffer_size_layout.addStretch()
        labels_layout.addLayout(buffer_size_layout)
        
        buffer_color_layout = QHBoxLayout()
        buffer_color_layout.addWidget(QLabel("Buffer Color:"))
        self.buffer_color = QgsColorButton()
        self.buffer_color.setColor(QColor("#ffffff"))
        buffer_color_layout.addWidget(self.buffer_color)
        buffer_color_layout.addStretch()
        labels_layout.addLayout(buffer_color_layout)
        
        labels_layout.addStretch()
        labels_tab.setLayout(labels_layout)
        tabs.addTab(labels_tab, "Labels")
        
        layout.addWidget(tabs)
        
        # ==================== BUTTONS ====================
        button_layout = QHBoxLayout()
        
        apply_existing_btn = QPushButton("Apply to Existing Layers")
        apply_existing_btn.setToolTip("Save settings and apply them to all layers currently in the project")
        apply_existing_btn.clicked.connect(self.applyToExisting)
        button_layout.addWidget(apply_existing_btn)
        
        button_layout.addStretch()
        
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.saveSettings)
        button_layout.addWidget(save_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def loadSettings(self):
        """Load settings from QSettings"""
        self.raster_enabled.setChecked(self.settings.value("AutoStyleManager/raster_enabled", True, type=bool))
        self.exclude_basemaps.setChecked(self.settings.value("AutoStyleManager/exclude_basemaps", True, type=bool))
        self.opacity_spin.setValue(self.settings.value("AutoStyleManager/opacity", 0.7, type=float))
        
        self.vector_enabled.setChecked(self.settings.value("AutoStyleManager/vector_enabled", True, type=bool))
        
        point_color = self.settings.value("AutoStyleManager/point_color", "#e74c3c")
        self.point_color.setColor(QColor(point_color))
        self.point_size.setValue(self.settings.value("AutoStyleManager/point_size", 2.5, type=float))
        
        line_color = self.settings.value("AutoStyleManager/line_color", "#3498db")
        self.line_color.setColor(QColor(line_color))
        self.line_width.setValue(self.settings.value("AutoStyleManager/line_width", 0.4, type=float))
        
        poly_fill = self.settings.value("AutoStyleManager/polygon_fill", "#90EE9064")
        self.polygon_fill.setColor(QColor(poly_fill))
        poly_stroke = self.settings.value("AutoStyleManager/polygon_stroke", "#2ecc71")
        self.polygon_stroke.setColor(QColor(poly_stroke))
        self.polygon_width.setValue(self.settings.value("AutoStyleManager/polygon_width", 0.4, type=float))
        
        self.labels_enabled.setChecked(self.settings.value("AutoStyleManager/labels_enabled", False, type=bool))
        self.label_field.setText(self.settings.value("AutoStyleManager/label_field", "name"))
        self.label_size.setValue(self.settings.value("AutoStyleManager/label_size", 10, type=float))
        
        label_color = self.settings.value("AutoStyleManager/label_color", "#000000")
        self.label_color.setColor(QColor(label_color))
        
        self.label_buffer.setChecked(self.settings.value("AutoStyleManager/label_buffer", True, type=bool))
        self.buffer_size.setValue(self.settings.value("AutoStyleManager/buffer_size", 1.0, type=float))
        
        buffer_color = self.settings.value("AutoStyleManager/buffer_color", "#ffffff")
        self.buffer_color.setColor(QColor(buffer_color))
    
    def saveSettings(self):
        """Save settings to QSettings"""
        self.settings.setValue("AutoStyleManager/raster_enabled", self.raster_enabled.isChecked())
        self.settings.setValue("AutoStyleManager/exclude_basemaps", self.exclude_basemaps.isChecked())
        self.settings.setValue("AutoStyleManager/opacity", self.opacity_spin.value())
        
        self.settings.setValue("AutoStyleManager/vector_enabled", self.vector_enabled.isChecked())
        self.settings.setValue("AutoStyleManager/point_color", self.point_color.color().name(QColor.HexArgb))
        self.settings.setValue("AutoStyleManager/point_size", self.point_size.value())
        
        self.settings.setValue("AutoStyleManager/line_color", self.line_color.color().name(QColor.HexArgb))
        self.settings.setValue("AutoStyleManager/line_width", self.line_width.value())
        
        self.settings.setValue("AutoStyleManager/polygon_fill", self.polygon_fill.color().name(QColor.HexArgb))
        self.settings.setValue("AutoStyleManager/polygon_stroke", self.polygon_stroke.color().name(QColor.HexArgb))
        self.settings.setValue("AutoStyleManager/polygon_width", self.polygon_width.value())
        
        self.settings.setValue("AutoStyleManager/labels_enabled", self.labels_enabled.isChecked())
        self.settings.setValue("AutoStyleManager/label_field", self.label_field.text())
        self.settings.setValue("AutoStyleManager/label_size", self.label_size.value())
        self.settings.setValue("AutoStyleManager/label_color", self.label_color.color().name(QColor.HexArgb))
        self.settings.setValue("AutoStyleManager/label_buffer", self.label_buffer.isChecked())
        self.settings.setValue("AutoStyleManager/buffer_size", self.buffer_size.value())
        self.settings.setValue("AutoStyleManager/buffer_color", self.buffer_color.color().name(QColor.HexArgb))
        
        QMessageBox.information(self, "Success", "Settings saved successfully!")
    
    def applyToExisting(self):
        """Apply current settings to all existing layers"""
        if not self.plugin:
            QMessageBox.warning(self, "Error", "Plugin reference not available!")
            return
        
        # First, save the current settings
        self.settings.setValue("AutoStyleManager/raster_enabled", self.raster_enabled.isChecked())
        self.settings.setValue("AutoStyleManager/exclude_basemaps", self.exclude_basemaps.isChecked())
        self.settings.setValue("AutoStyleManager/opacity", self.opacity_spin.value())
        
        self.settings.setValue("AutoStyleManager/vector_enabled", self.vector_enabled.isChecked())
        self.settings.setValue("AutoStyleManager/point_color", self.point_color.color().name(QColor.HexArgb))
        self.settings.setValue("AutoStyleManager/point_size", self.point_size.value())
        
        self.settings.setValue("AutoStyleManager/line_color", self.line_color.color().name(QColor.HexArgb))
        self.settings.setValue("AutoStyleManager/line_width", self.line_width.value())
        
        self.settings.setValue("AutoStyleManager/polygon_fill", self.polygon_fill.color().name(QColor.HexArgb))
        self.settings.setValue("AutoStyleManager/polygon_stroke", self.polygon_stroke.color().name(QColor.HexArgb))
        self.settings.setValue("AutoStyleManager/polygon_width", self.polygon_width.value())
        
        self.settings.setValue("AutoStyleManager/labels_enabled", self.labels_enabled.isChecked())
        self.settings.setValue("AutoStyleManager/label_field", self.label_field.text())
        self.settings.setValue("AutoStyleManager/label_size", self.label_size.value())
        self.settings.setValue("AutoStyleManager/label_color", self.label_color.color().name(QColor.HexArgb))
        self.settings.setValue("AutoStyleManager/label_buffer", self.label_buffer.isChecked())
        self.settings.setValue("AutoStyleManager/buffer_size", self.buffer_size.value())
        self.settings.setValue("AutoStyleManager/buffer_color", self.buffer_color.color().name(QColor.HexArgb))
        
        layers = QgsProject.instance().mapLayers().values()
        raster_count = 0
        vector_count = 0
        label_count = 0
        
        for layer in layers:
            if isinstance(layer, QgsRasterLayer) and self.raster_enabled.isChecked():
                self.plugin.styleRasterLayer(layer)
                raster_count += 1
            elif isinstance(layer, QgsVectorLayer) and self.vector_enabled.isChecked():
                self.plugin.styleVectorLayer(layer)
                vector_count += 1
                if self.labels_enabled.isChecked() and layer.labelsEnabled():
                    label_count += 1
        
        total = raster_count + vector_count
        msg = f"Styling applied to {total} layer(s)!\n\n"
        if raster_count > 0:
            msg += f"• {raster_count} raster layer(s)\n"
        if vector_count > 0:
            msg += f"• {vector_count} vector layer(s)\n"
        if label_count > 0:
            msg += f"• {label_count} layer(s) labeled"
        
        QMessageBox.information(self, "Success", msg)


class AutoStyleManager:
    def __init__(self, iface):
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions = []
        self.menu = '&Auto Style Manager'
        self.toolbar = self.iface.addToolBar('Auto Style Manager')
        self.toolbar.setObjectName('AutoStyleManager')
        self.settings = QSettings()
        self.dialog = None
        
    def getIcon(self):
        """Create icon from SVG"""
        svg_data = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="24" height="24" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <circle cx="12" cy="12" r="11" fill="#4A90E2" stroke="#2E5C8A" stroke-width="1.5"/>
  <path d="M 7 9 Q 7 7 9 7 L 15 7 Q 17 7 17 9 Q 17 10 16 11 L 14 13 Q 13 14 12 14 Q 11 14 10 13 L 8 11 Q 7 10 7 9 Z" 
        fill="#FFFFFF" stroke="#2E5C8A" stroke-width="1"/>
  <circle cx="10" cy="9" r="1.2" fill="#E74C3C"/>
  <circle cx="14" cy="9" r="1.2" fill="#2ECC71"/>
  <circle cx="12" cy="11.5" r="1.2" fill="#F39C12"/>
  <path d="M 15 15 L 18 18" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/>
  <circle cx="18.5" cy="18.5" r="1.5" fill="#FFFFFF"/>
  <g transform="translate(16, 5) scale(0.6)">
    <circle cx="0" cy="0" r="2.5" fill="none" stroke="#FFD700" stroke-width="1.2"/>
    <circle cx="0" cy="0" r="1" fill="#FFD700"/>
  </g>
</svg>"""
        
        svg_bytes = QByteArray(svg_data.encode())
        renderer = QSvgRenderer(svg_bytes)
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        
        from qgis.PyQt.QtGui import QPainter
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        
        return QIcon(pixmap)
        
    def initGui(self):
        action = QAction(
            self.getIcon(),
            "Auto Style Manager Settings",
            self.iface.mainWindow()
        )
        action.triggered.connect(self.run)
        action.setToolTip("Configure automatic styling for raster and vector layers")
        self.toolbar.addAction(action)
        self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)
        
        # Connect to layer added signal
        QgsProject.instance().layersAdded.connect(self.onLayersAdded)
        
    def unload(self):
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar
        
        # Disconnect signal
        try:
            QgsProject.instance().layersAdded.disconnect(self.onLayersAdded)
        except:
            pass
    
    def run(self):
        if not self.dialog:
            self.dialog = AutoStyleManagerDialog(plugin=self)
        self.dialog.loadSettings()  # Reload settings each time
        self.dialog.show()
        self.dialog.exec_()
    
    def onLayersAdded(self, layers):
        """Called when new layers are added to the project"""
        for layer in layers:
            if not layer or not layer.isValid():
                continue
                
            if isinstance(layer, QgsRasterLayer):
                if self.settings.value("AutoStyleManager/raster_enabled", True, type=bool):
                    self.styleRasterLayer(layer)
            elif isinstance(layer, QgsVectorLayer):
                if self.settings.value("AutoStyleManager/vector_enabled", True, type=bool):
                    self.styleVectorLayer(layer)
    
    def isBasemapLayer(self, layer):
        """Check if layer is a basemap/WMS/XYZ layer that should be excluded"""
        if not isinstance(layer, QgsRasterLayer):
            return False
        
        # Check provider type
        try:
            provider = layer.dataProvider().name() if layer.dataProvider() else ""
            if provider.lower() in ['wms', 'xyz', 'wmts', 'arcgismapserver', 'wfs']:
                return True
        except:
            pass
        
        # Check if source contains http (web tiles)
        try:
            source = layer.source()
            if "http" in source.lower():
                return True
        except:
            pass
        
        # Check layer name for common basemap keywords
        layer_name = layer.name().lower()
        basemap_keywords = ['google', 'osm', 'openstreetmap', 'bing', 'esri', 
                           'mapbox', 'satellite', 'basemap', 'background', 'imagery']
        
        for keyword in basemap_keywords:
            if keyword in layer_name:
                return True
        
        return False
    
    def styleRasterLayer(self, layer):
        """Apply default styling to raster layer"""
        # Check if we should exclude basemaps
        exclude_basemaps = self.settings.value("AutoStyleManager/exclude_basemaps", True, type=bool)
        if exclude_basemaps and self.isBasemapLayer(layer):
            return  # Skip styling for basemap layers
        
        try:
            # Only set opacity, don't touch renderer or resampling
            opacity = self.settings.value("AutoStyleManager/opacity", 0.7, type=float)
            
            # Use the renderer's opacity setting
            if layer.renderer():
                layer.renderer().setOpacity(opacity)
                layer.triggerRepaint()
        except Exception as e:
            # Silently fail if there's an issue
            pass
    
    def styleVectorLayer(self, layer):
        """Apply default styling to vector layer"""
        try:
            geom_type = layer.geometryType()
            renderer = layer.renderer()
            
            if not renderer or not renderer.symbol():
                return
            
            symbol = renderer.symbol()
            
            # Apply symbology based on geometry type
            if geom_type == QgsWkbTypes.PointGeometry:
                color = QColor(self.settings.value("AutoStyleManager/point_color", "#e74c3c"))
                size = self.settings.value("AutoStyleManager/point_size", 2.5, type=float)
                symbol.setColor(color)
                symbol.setSize(size)
                
            elif geom_type == QgsWkbTypes.LineGeometry:
                color = QColor(self.settings.value("AutoStyleManager/line_color", "#3498db"))
                width = self.settings.value("AutoStyleManager/line_width", 0.4, type=float)
                symbol.setColor(color)
                if hasattr(symbol, 'setWidth'):
                    symbol.setWidth(width)
                
            elif geom_type == QgsWkbTypes.PolygonGeometry:
                fill_color = QColor(self.settings.value("AutoStyleManager/polygon_fill", "#90EE9064"))
                stroke_color = QColor(self.settings.value("AutoStyleManager/polygon_stroke", "#2ecc71"))
                width = self.settings.value("AutoStyleManager/polygon_width", 0.4, type=float)
                
                symbol.setColor(fill_color)
                # Set outline color
                if symbol.symbolLayerCount() > 0:
                    symbol_layer = symbol.symbolLayer(0)
                    if hasattr(symbol_layer, 'setStrokeColor'):
                        symbol_layer.setStrokeColor(stroke_color)
                    if hasattr(symbol_layer, 'setStrokeWidth'):
                        symbol_layer.setStrokeWidth(width)
            
            # Apply labels if enabled
            if self.settings.value("AutoStyleManager/labels_enabled", False, type=bool):
                self.applyLabels(layer)
            
            layer.triggerRepaint()
            
        except Exception as e:
            # Silently fail if there's an issue
            pass
    
    def applyLabels(self, layer):
        """Apply default labels to vector layer"""
        try:
            label_field = self.settings.value("AutoStyleManager/label_field", "name")
            
            # Check if field exists (case-insensitive)
            field_names = [field.name() for field in layer.fields()]
            matching_field = None
            
            # Try exact match first
            if label_field in field_names:
                matching_field = label_field
            else:
                # Try case-insensitive match
                for field in field_names:
                    if field.lower() == label_field.lower():
                        matching_field = field
                        break
            
            # If no match, try common field names
            if not matching_field:
                common_names = ['name', 'NAME', 'Name', 'id', 'ID', 'Id', 
                               'label', 'LABEL', 'Label', 'text', 'TEXT', 'Text']
                for common in common_names:
                    if common in field_names:
                        matching_field = common
                        break
            
            # If still no field found, skip labeling
            if not matching_field:
                return
            
            # Create label settings
            label_settings = QgsPalLayerSettings()
            label_settings.fieldName = matching_field
            label_settings.enabled = True
            
            # Enable placement
            label_settings.placement = QgsPalLayerSettings.AroundPoint if layer.geometryType() == QgsWkbTypes.PointGeometry else QgsPalLayerSettings.Horizontal
            
            # Text format
            text_format = QgsTextFormat()
            
            # Font size
            font_size = self.settings.value("AutoStyleManager/label_size", 10, type=float)
            text_format.setSize(font_size)
            
            # Font color
            font_color = QColor(self.settings.value("AutoStyleManager/label_color", "#000000"))
            text_format.setColor(font_color)
            
            # Buffer
            if self.settings.value("AutoStyleManager/label_buffer", True, type=bool):
                buffer = QgsTextBufferSettings()
                buffer.setEnabled(True)
                buffer.setSize(self.settings.value("AutoStyleManager/buffer_size", 1.0, type=float))
                buffer_color = QColor(self.settings.value("AutoStyleManager/buffer_color", "#ffffff"))
                buffer.setColor(buffer_color)
                text_format.setBuffer(buffer)
            
            label_settings.setFormat(text_format)
            
            # Apply labeling
            labeling = QgsVectorLayerSimpleLabeling(label_settings)
            layer.setLabeling(labeling)
            layer.setLabelsEnabled(True)
            
            # Force refresh
            layer.triggerRepaint()
            
        except Exception as e:
            # Debug: print error to help troubleshoot
            print(f"Label error: {e}")
            pass


# Required functions for QGIS plugin
def classFactory(iface):
    return AutoStyleManager(iface)
