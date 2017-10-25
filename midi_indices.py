import bpy
import os
from bpy.props import *
from ... base_types import AnimationNode

class MidiIndex(bpy.types.PropertyGroup):
    noteName = StringProperty() # e.g. C4, B5, ...
    noteIndex = IntProperty()

class MidiIndexNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_MidiIndexNode"
    bl_label = "MIDI Evaluate Node, Vers 1.0"
    bl_width_default = 400

    notes = CollectionProperty(type = MidiIndex)
    cont_grp = StringProperty(name = "Controls Group")
    keys_grp = StringProperty(name = "Keys Group")
    message1 = StringProperty("")
    message2 = StringProperty("")

    def create(self):
        self.newInput("Object Group", "Channel Controls", "group1")
        self.newInput("Object Group", "Key Meshes to Link", "group")
        self.newOutput("Object List", "Control Objects", "objects1")
        self.newOutput("Object List", "Key Objects", "objects")
        self.newOutput("Text List", "Notes Played in Channel", "notes")
        self.newOutput("Integer List", "Control to Key Index", "indices")

    def draw(self, layout):
        layout.prop(self, "cont_grp")
        layout.prop(self, "keys_grp")
        layout.separator()
        col = layout.column()
        col.scale_y = 1.5
        self.invokeFunction(col, "makeIndices", icon = "NEW",
            text = "Create Control to Key Indices")

        if (self.message1 != ""):
            layout.label(self.message1, icon = "INFO")
        if (self.message2 != ""):
            layout.label(self.message2, icon = "INFO")

    def execute(self, group1, group):
        notes = [item.noteName for item in self.notes]
        indices = [item.noteIndex for item in self.notes]
        control_Objs = list(getattr(group1, "objects", []))
        keys_Objs = list(getattr(group, "objects", []))
        return control_Objs, keys_Objs, notes, indices

    def makeIndices(self):
        self.notes.clear()
        cont_g = bpy.data.groups.get(self.cont_grp)
        keys_g = bpy.data.groups.get(self.keys_grp)
        if cont_g == None or keys_g == None:
            self.message1 = "Problems with Controls or Keys Group Names"
        else:
            cont_objs = cont_g.objects
            keys_objs = keys_g.objects
            numb_c = len(cont_objs)
            numb_k = len(keys_objs)

            def createNote(f_n):
                item = self.notes.add()
                item.noteName = f_n

                def insertKeyframe(noteIndex):
                    item.noteIndex = noteIndex

                return insertKeyframe

            if numb_k < numb_c:
                self.message1 = "Insufficient Keys " + str(numb_k) + " / " + str(numb_c)
            else:
                self.message1 = "Processed " + str(numb_c) + " Controls & " + str(numb_k) + " Keys"
                ke_names = []
                for obj in keys_objs:
                    note = obj.name.split("_")[0]
                    ke_names.append(note)

                for rec in cont_objs:
                    f_n = rec.name.split("_")[1]
                    indx = 0
                    for i in range( 0, (len(ke_names) - 1)):
                        if ke_names[i] == f_n:
                            indx = i

                    addKeyframe = createNote(f_n)
                    addKeyframe(noteIndex = indx)
