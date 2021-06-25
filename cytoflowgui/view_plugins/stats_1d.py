#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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

import pandas as pd

from traits.api import provides, Property
from traitsui.api import View, Item, EnumEditor, VGroup, TextEditor, Controller, TupleEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

import cytoflow.utility as util

from ..workflow.views import Stats1DWorkflowView, Stats1DPlotParams
from ..editors import SubsetListEditor, ColorTextEditor, ExtendableEnumEditor, InstanceHandlerEditor
from ..subset_controllers import subset_handler_factory

from .i_view_plugin import IViewPlugin, VIEW_PLUGIN_EXT
from .view_plugin_base import ViewHandler, PluginHelpMixin, Stats1DPlotParamsView


class Stats1DParamsHandler(Controller):
    view_params_view = \
        View(Item('variable_lim',
                  label = "Variable\nLimits",
                  editor = TupleEditor(editors = [TextEditor(auto_set = False,
                                                             evaluate = float,
                                                             format_func = lambda x: "" if x == None else str(x)),
                                                  TextEditor(auto_set = False,
                                                             evaluate = float,
                                                             format_func = lambda x: "" if x == None else str(x))],
                                       labels = ["Min", "Max"],
                                       cols = 1)),
             Item('linestyle'),
             Item('marker'),
             Item('markersize',
                  editor = TextEditor(auto_set = False),
                  format_func = lambda x: "" if x == None else str(x)),
             Item('capsize',
                  editor = TextEditor(auto_set = False),
                  format_func = lambda x: "" if x == None else str(x)),
             Item('alpha'),
             Item('shade_error'),
             Item('shade_alpha'),
             Stats1DPlotParamsView.content)

  
class Stats1DHandler(ViewHandler):
    indices = Property(depends_on = "context.statistics, model.statistic, model.subset")
    numeric_indices = Property(depends_on = "context.statistics, model.statistic, model.subset")
    levels = Property(depends_on = "context.statistics, model.statistic")

    view_traits_view = \
        View(VGroup(
             VGroup(Item('statistic',
                         editor=EnumEditor(name='context_handler.numeric_statistics_names'),
                         label = "Statistic"),
                    Item('scale', label = "Statistic\nScale"),
                    Item('variable',
                         editor = EnumEditor(name = 'handler.numeric_indices')),
                    Item('variable_scale', label = "Variable\nScale"),
                    Item('xfacet',
                         editor=ExtendableEnumEditor(name='handler.indices',
                                                     extra_items = {"None" : ""}),
                         label = "Horizontal\nFacet"),
                    Item('yfacet',
                         editor=ExtendableEnumEditor(name='handler.indices',
                                                     extra_items = {"None" : ""}),
                         label = "Vertical\nFacet"),
                    Item('huefacet',
                         editor=ExtendableEnumEditor(name='handler.indices',
                                                     extra_items = {"None" : ""}),
                         label="Hue\nFacet"),
                    Item('huescale', 
                         label = "Hue\nScale"),
                    Item('error_statistic',
                         editor=ExtendableEnumEditor(name='context_handler.statistics_names',
                                                     extra_items = {"None" : ("", "")}),
                         label = "Error\nStatistic"),
                    label = "One-Dimensional Statistics Plot",
                    show_border = False),
             VGroup(Item('subset_list',
                         show_label = False,
                         editor = SubsetListEditor(conditions = "handler.levels",
                                                   editor = InstanceHandlerEditor(view = 'subset_view',
                                                                                  handler_factory = subset_handler_factory),
                                                   mutable = False)),
                    label = "Subset",
                    show_border = False,
                    show_labels = False),
             Item('context.view_warning',
                  resizable = True,
                  visible_when = 'context.view_warning',
                  editor = ColorTextEditor(foreground_color = "#000000",
                                          background_color = "#ffff99")),
             Item('context.view_error',
                  resizable = True,
                  visible_when = 'context.view_error',
                  editor = ColorTextEditor(foreground_color = "#000000",
                                           background_color = "#ff9191"))))
        
    view_params_view = \
        View(Item('plot_params',
                  editor = InstanceHandlerEditor(view = 'view_params_view',
                                                 handler_factory = Stats1DParamsHandler),
                  style = 'custom',
                  show_label = False))
        
    # MAGIC: gets the value for the property indices
    def _get_indices(self):
        if not (self.context and self.context.statistics 
                and self.model.statistic in self.context.statistics):
            return []
        
        stat = self.context.statistics[self.model.statistic]
        data = pd.DataFrame(index = stat.index)
        
        if self.model.subset:
            data = data.query(self.model.subset)
            
        if len(data) == 0:
            return []       
        
        names = list(data.index.names)
        for name in names:
            unique_values = data.index.get_level_values(name).unique()
            if len(unique_values) == 1:
                data.index = data.index.droplevel(name)
        
        return list(data.index.names)
    
    # MAGIC: gets the value for the property 'levels'
    # returns a Dict(Str, pd.Series)
    def _get_levels(self):        
        if not (self.context and self.context.statistics 
                and self.model.statistic in self.context.statistics):
            return {}
        
        stat = self.context.statistics[self.model.statistic]
        index = stat.index
        
        names = list(index.names)
        for name in names:
            unique_values = index.get_level_values(name).unique()
            if len(unique_values) == 1:
                index = index.droplevel(name)

        names = list(index.names)
        ret = {}
        for name in names:
            ret[name] = pd.Series(index.get_level_values(name)).sort_values()
            ret[name] = pd.Series(ret[name].unique())
            
        return ret
        
    # MAGIC: gets the value for the property numeric_indices
    def _get_numeric_indices(self):        
        if not (self.context and self.context.statistics 
                and self.model.statistic in self.context.statistics):
            return []
        
        stat = self.context.statistics[self.model.statistic]
        data = pd.DataFrame(index = stat.index)
        
        if self.model.subset:
            data = data.query(self.model.subset)
            
        if len(data) == 0:
            return []       
        
        names = list(data.index.names)
        for name in names:
            unique_values = data.index.get_level_values(name).unique()
            if len(unique_values) == 1:
                data.index = data.index.droplevel(name)
        
        data.reset_index(inplace = True)
        return [x for x in data if util.is_numeric(data[x])]


@provides(IViewPlugin)
class Stats1DPlugin(Plugin, PluginHelpMixin):

    id = 'edu.mit.synbio.cytoflowgui.view.stats1d'
    view_id = 'edu.mit.synbio.cytoflow.view.stats1d'
    short_name = "1D Statistics View"
    
    def get_view(self):
        return Stats1DWorkflowView()
    
    def get_handler(self, model, context):
        if isinstance(model, Stats1DWorkflowView):
            return Stats1DHandler(model = model, context = context)
        elif isinstance(model, Stats1DPlotParams):
            return Stats1DParamsHandler(model = model, context = context)

    def get_icon(self):
        return ImageResource('stats_1d')

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self
    


