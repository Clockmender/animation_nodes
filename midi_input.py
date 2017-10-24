import bpy
import os
from bpy.props import *
from ... base_types import AnimationNode
from ... data_structures import DoubleList
from ... events import propertyChanged
from ... utils.sequence_editor import getOrCreateSequencer, getEmptyChannel
from ... utils.path import getAbsolutePathOfSound

class MidiNoteData(bpy.types.PropertyGroup):
    noteName = StringProperty() # e.g. C4, B5, ...
    # This value can be keyframed.
    # It is possible but not easy to 'find' the fcurve of this property.
    # Therefor only the value in the current frame can be accessed efficiently.
    # In most use cases this should be enough, otherwise you'll have to find another alternative.
    value = FloatProperty()

class MidiInputNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_MidiInputNode"
    bl_label = "MIDI Input Node, Vers 1.0"
    bl_width_default = 400

    # Setup variables
    useV = BoolProperty(name = "Use MIDI Velocity", default = False, update = propertyChanged)
    offset = IntProperty(name = "Offset", default = 0, min = -1000, max = 10000)
    easing = FloatProperty(name = "Easing", default = 0.2, precision = 3)
    soundName = StringProperty(name = "Sound")
    keys_grp = StringProperty(name = "Keys Group")
    message1 = StringProperty("")
    message2 = StringProperty("")
    midiFilePath = StringProperty()
    midiName = StringProperty()

    # I'd suggest to bake one channel per node for now.
    # You can have multiple nodes of course.
    Channel_Number = StringProperty() # e.g. Piano, ...
    notes = CollectionProperty(type = MidiNoteData)

    def create(self):
        self.newOutput("Text List", "Notes", "notes")
        self.newOutput("Float List", "Values", "values")
        self.newOutput("Float List", "Index", "index1")

    def draw(self, layout):
        layout.prop(self, "Channel_Number")
        layout.prop(self, "useV")
        layout.prop(self, "easing")
        layout.prop(self, "offset")
        layout.prop(self, "keys_grp")
        layout.separator()
        col = layout.column()
        col.scale_y = 1.5
        self.invokeSelector(col ,"PATH", "bakeMidi", icon = "NEW",
            text = "Bake Midi")
        layout.separator()
        self.invokeSelector(col, "PATH", "loadSound",
            text = "Load Sound for MIDI File (Uses Offset)", icon = "NEW")
        if (self.message1 != ""):
            layout.label(self.message1, icon = "INFO")
        if (self.message2 != ""):
            layout.label(self.message2, icon = "INFO")

    def execute(self):
        notes = [item.noteName for item in self.notes]
        values = [item.value for item in self.notes]
        return notes, DoubleList.fromValues(values)

    def loadSound(self, path):
        editor = getOrCreateSequencer(self.nodeTree.scene)
        channel = getEmptyChannel(editor)
        sequence = editor.sequences.new_sound(
            name = os.path.basename(path),
            filepath = path,
            channel = channel,
            frame_start = self.offset)
        self.soundName = sequence.sound.name
        self.message2 = "Sound Loaded."

    def removeFCurvesOfThisNode(self):
        try: action = self.id_data.animation_data.action
        except: return
        if action is None:
            return

        fCurvesToRemove = []
        pathPrefix = "nodes[\"{}\"]".format(self.name)
        for fCurve in action.fcurves:
            if fCurve.data_path.startswith(pathPrefix):
                fCurvesToRemove.append(fCurve)

        for fCurve in fCurvesToRemove:
            action.fcurves.remove(fCurve)

    def bakeMidi(self, path):
        # remove previously baked data
        self.notes.clear()
        self.removeFCurvesOfThisNode()

        self.midiFilePath = str(path)
        self.midiName = str(os.path.basename(path)).split(".")[0]
        self.message1 = "Midi File Loaded: " + str(os.path.basename(path)) + "MIDI File"

        if (self.midiFilePath == ""):
            self.message1 = "Load MIDI CSV File First! Have you set Use Velocity, Easing & Offset?"
        else:
            self.message1 = ""
            self.message2 = ""

            note_list = ['a0','a0s','b0','c1','c1s','d1','d1s','e1','f1','f1s','g1','g1s','a1','a1s','b1','c2','c2s','d2','d2s','e2','f2','f2s','g2','g2s','a2','a2s','b2','c3','c3s','d3','d3s','e3','f3','f3s','g3','g3s','a3','a3s','b3',
                'c4','c4s','d4','d4s','e4','f4','f4s','g4','g4s','a4','a4s','b4','c5','c5s','d5','d5s','e5','f5','f5s','g5','g5s','a5','a5s','b5','c6','c6s','d6','d6s','e6','f6','f6s','g6','g6s','a6','a6s','b6',
                    'c7','c7s','d7','d7s','e7','f7','f7s','g7','g7s','a7','a7s','b7','c8']

            events_list = []
            control_list = []
            midi_file = self.midiFilePath
            offsetp = self.offset
            velp = self.useV
            easingp = self.easing
            t_name = 'Unknown'
            t_ind = 2
            fps = bpy.context.scene.render.fps

            #This section Opens and reads the MIDI file.
            with open(midi_file) as f1:
                for line in f1:
                    in_l = [elt.strip() for elt in line.split(',')]
                    if (in_l[2] == 'Header'):
                        # Get Pulse variable.
                        pulse = int(in_l[5])

                    elif (in_l[2] == 'Tempo'):
                        if (in_l[0] == '1'):
                            # Get Initial Tempo.
                            tempo = in_l[3]
                            bpm = float( round( (60000000 / int(tempo)), 5) )
                            bps = float( round( (bpm / 60), 5) )
                        else:
                            # Add Tempo Changes to events list.
                            events_list.append(in_l)

                    elif (in_l[2] == 'Title_t') and (int(in_l[0]) > 1):
                        t_name = in_l[3].strip('"')
                        # Get First Track Title
                        if (not t_name):
                            t_name = 'Channel_' + str(t_ind)
                            t_ind = t_ind + 1
                            control_list.append(t_name)
                        else:
                            control_list.append(t_name)

                    # Only process note events, ignore control events.
                    if ( len(in_l) == 6) and ( in_l[2].split('_')[0] == 'Note') and (in_l[0] == self.Channel_Number):
                        note_n = note_list[(int(in_l[4]) - 21)]
                        on_off = in_l[2]
                        velo = int(in_l[5]) / 127
                        if (on_off == "Note_on_c"):
                            if velp:
                                on_off = velo
                            else:
                                on_off = "1"
                        else:
                            on_off = "0"
                        # On-Off, Frame, Note, Velocity
                        conv = (60 / (bpm * pulse))
                        frame_e = int(in_l[1])
                        frame_e = frame_e * conv * fps
                        frame_e = round(frame_e, 2) + self.offset
                        in_n = [on_off, str(frame_e), note_n, in_l[5] ]
                        events_list.append(in_n)
                        control = note_n
                        if control not in control_list:
                            control_list.append(control)

            # Get list lengths
            numb_1 = 0
            numb_2 = 0
            numb_1 = len(control_list)
            numb_2 = len(events_list)
            self.message1 = "Baking File: " + self.midiName + ", Controls= " + str(numb_1 - 1) + ", Channel No = " + self.Channel_Number
            self.message2 = "Events = " +str(numb_2) + ", Pulse = " + str(pulse) + ", BPM = " + str(int(bpm)) + ", Tempo = " + str(tempo)

        # This function creates an abstraction for the somewhat complicated stuff
        # that is needed to insert the keyframes. It is needed because in Blender
        # custom node trees don't work well with fcurves yet.
        def createNote(name):
            dataPath = "nodes[\"{}\"].notes[{}].value".format(self.name, len(self.notes))
            item = self.notes.add()
            item.noteName = name

            def insertKeyframe(value, frame):
                item.value = value
                self.id_data.keyframe_insert(dataPath, frame = frame)

            return insertKeyframe

        # Get Channel Name and process events for each note
        channelName = control_list[0]
        # Loop through Notes
        for rec in range(1, numb_1):  # len(control_list)
            f_n = control_list[rec][0]
            name = channelName + "_" + f_n
            ev_list = [bit for bit in events_list if bit[2] == f_n]
            addKeyframe = createNote(name)
            # Value, then Frame
            addKeyframe(value = 0 , frame = 1)
            # Range used so I can test a smal section:
            for ind in range(0,len(ev_list)):
                addKeyframe(value = float(ev_list[ind][0]), frame = float(ev_list[ind][1]) )

        # Build Index file if group name is good
        group = bpy.data.groups.get(self.keys_grp)
        assert group is not None
        keys_objs = group.objects
        control_list.pop(0)
        ke_names = []
        index = []
        for obj in keys_objs:
            note = obj.name.split("_")[0]
            ke_names.append(note)

        for note in control_list:
            indx = ke_names.index(note)
            index.append(indx)
