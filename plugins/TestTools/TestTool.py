# Copyright (c) 2016 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.
from UM.Extension import Extension

from PyQt5.QtCore import QObject


class TestTool(Extension, QObject):
    def __init__(self, parent = None):
        QObject.__init__(self, parent)
        Extension.__init__(self)

        self.addMenuItem("Test material manager", self._testMaterialManager)

    def _testMaterialManager(self):
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        from cura.CuraApplication import CuraApplication
        CuraApplication.getInstance()._material_manager._test_metadata()
