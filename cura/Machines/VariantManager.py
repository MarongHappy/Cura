from typing import Optional

from UM.Logger import Logger
from UM.Settings.ContainerRegistry import ContainerRegistry
from UM.Settings.InstanceContainer import InstanceContainer


class VariantType:
    BUILD_PLATE = "buildplate"
    NOZZLE = "nozzle"


ALL_VARIANT_TYPES = (VariantType.BUILD_PLATE, VariantType.NOZZLE)


#
# VariantManager is THE place to look for a specific variant. It maintains a variant lookup table with the following
# structure:
#
#   [machine_definition_id] ->  [variant_type]  -> [variant_name]   -> "metadata" and "container"
# Example:   "ultimaker3"   ->    "buildplate"  ->   "Glass" (if present)  -> "metadata": {...}
#                                                                          -> "container": None/InstanceContainer
#                                               ->    ...
#                           ->    "nozzle"      ->   "AA 0.4"
#                                               ->   "BB 0.8"
#                                               ->    ...
#
# Note that the "container" field is not loaded in the beginning because it would defeat the purpose of lazy-loading.
# A container is loaded when getVariant() is called to load a variant InstanceContainer.
#
class VariantManager:

    def __init__(self, container_registry):
        self._container_registry = container_registry  # type: ContainerRegistry

        self._machine_to_variant_dict_map = {}  # <machine_type> -> <variant_dict>

        self._exclude_variant_id_list = ["empty_variant"]

    #
    # Initializes the VariantManager including:
    #  - initializing the variant lookup table based on the metadata in ContainerRegistry.
    #
    def initialize(self):
        # Cache all variants from the container registry to a variant map for better searching and organization.
        variant_metadata_list = self._container_registry.findContainersMetadata(type = "variant")
        for variant_metadata in variant_metadata_list:
            if variant_metadata["id"] in self._exclude_variant_id_list:
                Logger.log("d", "exclude variant [%s]", variant_metadata["id"])
                continue

            variant_name = variant_metadata["name"]
            variant_definition = variant_metadata["definition"]
            if variant_definition not in self._machine_to_variant_dict_map:
                self._machine_to_variant_dict_map[variant_definition] = {}
                for variant_type in ALL_VARIANT_TYPES:
                    self._machine_to_variant_dict_map[variant_definition][variant_type] = {}

            variant_type = variant_metadata["hardware_type"]
            variant_dict = self._machine_to_variant_dict_map[variant_definition][variant_type]
            if variant_name in variant_dict:
                # ERROR: duplicated variant name.
                raise RuntimeError("Found duplicated variant name [%s], type [%s] for machine [%s]" %
                                   (variant_name, variant_type, variant_definition))

            variant_dict[variant_name] = {"metadata": variant_metadata,
                                          "container": None,
                                          }

    #
    # Gets the metadata dict of the variant with the given:
    #  - machine_type_name: a machine definition ID, which represents a certain machine type.
    #  - variant_type: type of the variant, see class VariantType.
    #  - variant_name: name of the variant, such as "AA 0.4", "0.4 mm", etc.
    #
    # Returns the metadata dict if present, otherwise None.
    #
    def getVariantMetadata(self, machine_type_name: str, variant_type: str, variant_name: str) -> Optional[dict]:
        variant_dict = self._machine_to_variant_dict_map[machine_type_name].get(variant_type, {}).get(variant_name)
        if not variant_dict:
            return None

        return variant_dict["metadata"]

    #
    # Gets the variant InstanceContainer with the given information.
    # Almost the same as getVariantMetadata() except that this returns an InstanceContainer if present.
    #
    def getVariant(self, machine_type_name: str, variant_type: str, variant_name: str) -> Optional["InstanceContainer"]:
        variant_dict = self._machine_to_variant_dict_map[machine_type_name].get(variant_type, {}).get(variant_name)
        if not variant_dict:
            return None

        # Lazy-load the container if it hasn't been loaded yet.
        if variant_dict["container"] is None:
            variant_id = variant_dict["id"]
            variant_list = self._container_registry.findInstanceContainers(id = variant_id)
            if not variant_list:
                raise RuntimeError("Cannot lazy-load variant container [%s], cannot be found in ContainerRegistry" %
                                   variant_id)
            variant_dict["container"] = variant_list[0]

        return variant_dict["container"]
