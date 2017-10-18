import bpy
from ... base_types import AnimationNode
from bpy.props import *
from ... data_structures import LongList
from ... events import propertyChanged

class Midi_Indices_Node(bpy.types.Node, AnimationNode):
    bl_idname = "an_Midi_Indices_Node"
    bl_label = "MIDI Indices Node (1); Vers 1.1"
    bl_width_default = 250

    indk = []
    message1 = StringProperty("Start")

    def create(self):
        self.newInput("Object Group", "Controls", "cont_list")
        self.newInput("Object Group", "Keys", "key_list")
        self.newOutput("Integer List", "Indices", "indices")

    def draw(self,layout):
        col = layout.column()
        col.scale_y = 1.5
        self.invokeFunction(col, "createIndices", icon = "NEW",
            text = "Create Controls-to-Notes Index")

        if (self.message1 != ""):
            layout.label(self.message1, icon = "INFO")

    def execute(self, cont_list, key_list):
        if cont_list is None or key_list is None:
            cont_objs = None
            keys_objs = None
            self.indk = []
            self.message1 = "Select Controls and Keys"
            return
        else:
            cont_objs = list(getattr(cont_list, "objects", []))
            keys_objs = list(getattr(key_list, "objects", []))
            global cont_objs
            global keys_objs

        if (len(self.indk) == 0):
            self.Message1 = "Check Groups & Run Script"
            self.indk = []
            return
        else:
            self.message1 = ""
            return LongList.fromValues(self.indk)

    def createIndices(self):
        # Check the variables
        if cont_objs is None or keys_objs is None:
            self.indk = []
            return

        else:
            contn = len(cont_objs)
            keysn = len(keys_objs)

        if (keysn < contn):
            self.message1 = "Insufficient Keys for Controls"
        else:
            # Loop through controls to get key indices.
            for cont in cont_objs:
                cont_n = str(cont).split('"')[1].split("_")[1]
                ind = 0
                for key in keys_objs:
                    key_n = str(key).split('"')[1].split('_')[0]
                    if (cont_n == key_n):
                        self.indk.append(ind)
                        break
                    ind = (ind + 1)
