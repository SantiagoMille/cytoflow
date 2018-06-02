#!/usr/bin/env python3.4

# (c) Massachusetts Institute of Technology 2015-2017
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Import Files
------------

Import FCS files and associate them with experimental conditions (metadata.)

.. object:: Edit samples

    Open the sample editor dialog box.

.. object:: Events per sample

    For very large data sets, *Cytoflow*'s interactive operation may be too slow.
    By setting **Events per sample**, you can tell *Cytoflow* to import a
    smaller number of events from each FCS file, which will make interactive
    data exploration much faster.  When you're done setting up your workflow,
    set **Events per sample** to empty or 0 and *Cytoflow* will re-run your
    workflow with the entire data set.
    

..  object:: The import dialog

    .. image:: _images/import.png

    Allows you to specify FCS files in the experiment, and
    the experimental conditions that each tube (or well) was subject to.
    
    .. note::
    
        You can select sort the table by clicking on a row header.
        
    .. note::
    
        You can select multiple entries in a column by clicking one, holding
        down *Shift*, and clicking another (to select a range); or, by holding
        down *Ctrl* and clicking multiple additional cells in the table.  If 
        multiple cells are selected, typing a value will update all of them.
        
    .. note:: 
    
        **Each tube must have a unique set of experimental conditions.**  If a
        tube's conditions are not unique, the row is red and you will not be
        able to click "OK".
    
    .. object:: Add tubes
    
        Opens a file selector to add tubes.
        
    .. object: Remove tubes
    
        Removes the currently selected tubes (rows) in the table.
        
    .. object: Add condition
    
        Opens a dialog (see below) to add a new experimental condition.
        
    .. object: Remove condition
    
        Removes the currently selected condition (column) in the table.

    .. object:: The new condition dialog box

    
        .. image:: _images/condition.png
        
            
        .. object:: Condition name
        
            The name of the new condition.  The name must be a valid Python identifier:
            it must start with a letter or _, and contain only letters, numbers and _.
            
        .. object: Condition type
        
            The type of the new condition.  Allowed types are **Category**, **Number**
            and **True/False**.

"""
from textwrap import dedent

from traitsui.api import (View, Item, Controller, TextEditor, ButtonEditor, 
                          InstanceEditor, HGroup, VGroup)
from traits.api import (Button, Property, cached_property, provides, Callable, 
                        HasTraits, String, List, on_trait_change, Instance,
                        Bool, Dict, Str, Enum)

from envisage.api import Plugin, contributes_to

import cytoflow.utility as util
from cytoflow import Tube, ImportOp
from cytoflow.operations.i_operation import IOperation
                       
from cytoflowgui.vertical_list_editor import VerticalListEditor
from cytoflowgui.serialization import camel_registry, traits_repr
from cytoflowgui.import_dialog import ExperimentDialogModel, ExperimentDialogHandler
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin, PluginHelpMixin

ImportOp.__repr__ = Tube.__repr__ = traits_repr

class Channel(HasTraits):
    channel = String
    name = String
    
    default_view = View(HGroup(Item('channel', style = 'readonly'),
                               Item('name')))

class ImportHandler(OpHandlerMixin, Controller):
    
    setup_event = Button(label="Set up experiment...")
    samples = Property(depends_on = 'model.tubes', status = True)
    dialog_model = Instance(ExperimentDialogModel)
        
    def default_traits_view(self):
        return View(VGroup(Item('handler.setup_event',
                                show_label=False),
                           Item('object.channels_list',
                                editor = VerticalListEditor(editor = InstanceEditor(),
                                                            style = 'custom',
                                                            mutable = False,
                                                            deletable = True),
                                show_label = False)),
                    Item('object.events',
                         editor = TextEditor(auto_set = False,
                                             format_func = lambda x: "" if x == None else str(x)),
                         label="Events per\nsample"),
                    Item('handler.samples',
                         label='Samples',
                         style='readonly'),
                    Item('ret_events',
                         label='Events',
                         style='readonly'),
                    Item('do_estimate',
                         editor = ButtonEditor(value = True,
                                               label = "Import!"),
                         show_label = False),
                    shared_op_traits)
        
    def _setup_event_fired(self):
        """
        Import data; save as self.result
        """

        self.dialog_model = ExperimentDialogModel(import_op = self.model,
                                                  conditions = self.context.conditions,
                                                  metadata = self.context.metadata)

        handler = ExperimentDialogHandler(model = self.dialog_model)
        handler.edit_traits(kind = 'livemodal')        
        
        
    @cached_property
    def _get_samples(self):
        return len(self.model.tubes)
    
    
    @on_trait_change('model.events', post_init = True)
    def _events_changed(self):
        if not self.dialog_model:
            return
        
        ret_events = 0
        for tube in self.dialog_model.tubes:
            if self.model.events:
                ret_events += min(tube.metadata['$TOT'], self.model.events)
            else:
                ret_events += tube.metadata['$TOT']
        
        self.model.ret_events = ret_events
        

@provides(IOperation)
class ImportPluginOp(PluginOpMixin, ImportOp):
    handler_factory = Callable(ImportHandler, transient = True)
    
    channels_list = List(Channel, estimate = True)
    events = util.CIntOrNone(None, estimate = True)
    tubes = List(Tube, estimate = True)
    channels = Dict(Str, Str, estimate = True)
    name_metadata =  Enum(None, "$PnN", "$PnS", estimate = True)
    
    ret_events = util.PositiveInt(0, allow_zero = True, transient = True)
    do_import = Bool(False)
    
    @on_trait_change('channels, channels_items')
    def _channels_changed(self):
        new_channels = []
        for channel, name in self.channels.items():
            new_channels.append(Channel(channel = channel, name = name))
            
        self.channels_list = new_channels

    def estimate(self, _):
        self.do_import = True
        
        
    def apply(self, experiment = None):
        if self.do_import:
            return super().apply(experiment = experiment)
        else:
            if not self.tubes:
                raise util.CytoflowOpError(None, 'Must specify some tubes by '
                                                 'pressing "Experimental Setup"')
            raise util.CytoflowOpError(None, "Press 'Import!'")
        
        
    def clear_estimate(self):
        self.do_import = False

    
    def get_notebook_code(self, idx):
        op = ImportOp()
        op.copy_traits(self, op.copyable_trait_names())
        
        return dedent("""
            op_{idx} = {repr}
            
            ex_{idx} = op_{idx}.apply()"""
            .format(repr = repr(op),
                    idx = idx))
        

@provides(IOperationPlugin)
class ImportPlugin(Plugin, PluginHelpMixin):
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.import'
    operation_id = 'edu.mit.synbio.cytoflow.operations.import'

    short_name = "Import data"
    menu_group = "TOP"
    
    def get_operation(self):
        return ImportPluginOp()
    
    def get_icon(self):
        return None
        
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
### Serialization
    
@camel_registry.dumper(ImportPluginOp, 'import', version = 2)
def _dump_op(op):
    return dict(tubes = op.tubes,
                conditions = op.conditions,
                channels = op.channels,
                events = op.events,
                name_metadata = op.name_metadata)

@camel_registry.loader('import', version = any)
def _load_op(data, version):
    data.pop('ret_events', None)
    return ImportPluginOp(**data)

@camel_registry.dumper(Tube, 'tube', version = 1)
def _dump_tube(tube):
    return dict(file = tube.file,
                conditions = tube.conditions)

@camel_registry.loader('tube', version = 1)
def _load_tube(data, version):
    return Tube(**data)
            