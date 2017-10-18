import bpy
from ... base_types import AnimationNode
from ... data_structures import LongList
from ... events import propertyChanged

class Midi_Indices_Node(bpy.types.Node, AnimationNode):
    bl_idname = "an_Midi_Indices_Node"
    bl_label = "MIDI Indices Node; Version 1.0"
    bl_width_default = 250

    def create(self):
        self.newInput("Object Group", "Controls", "cont_list")
        self.newInput("Object Group", "Keys", "key_list")
        self.newOutput("Integer List", "Indices", "indices")

    def draw(self,layout):
        layout.label("Select Controls & Keys by Group Names", icon = "INFO")

    def execute(self, cont_list, key_list):
        if cont_list is None or key_list is None:
            return

        indk = []
        cont_objs = list(getattr(cont_list, "objects", []))
        keys_objs = list(getattr(key_list, "objects", []))
        # Loop through controls to get key indices.
        for cont in cont_objs:
            cont_n = str(cont).split('"')[1].split("_")[1]
            ind = 0
            for key in keys_objs:
                key_n = str(key).split('"')[1].split('_')[0]
                if (cont_n == key_n):
                    indk.append(ind)
                    break
                ind = (ind + 1)

        return LongList.fromValues(indk)
