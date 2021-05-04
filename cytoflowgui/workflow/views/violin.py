#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
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
Violin Plot
-----------

Plots a violin plot, which is a nice way to compare several distributions.

.. object:: X Variable

    The variable to compare on the X axis.

.. object:: Y Channel

    The channel to plot on the Y axis.
    
.. object:: Y Channel Scale

    How to scale the Y axis of the plot.
    
.. object:: Horizonal Facet

    Make multiple plots.  Each column has a unique value of this variable.
    
.. object:: Vertical Facet

    Make multiple plots.  Each row has a unique value of this variable.
    
.. object:: Color Facet

    Plot with multiple colors.  Each color has a unique value of this variable.
    
.. object:: Color Scale

    If **Color Facet** is a numeric variable, use this scale for the color
    bar.
    
.. object:: Tab Facet

    Make multiple plots in differen tabs; each tab's plot has a unique value
    of this variable.
    
.. object:: Subset

    Plot only a subset of the data in the experiment.
  
.. plot::
        
    import cytoflow as flow
    import_op = flow.ImportOp()
    import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
                                 conditions = {'Dox' : 10.0}),
                       flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
                                 conditions = {'Dox' : 1.0})]
    import_op.conditions = {'Dox' : 'float'}
    ex = import_op.apply()

    flow.ViolinPlotView(channel = 'Y2-A',
                        scale = 'log',
                        variable = 'Dox').plot(ex)
"""

from textwrap import dedent

from traits.api import provides, Enum, Bool, Instance, CInt

from cytoflow import ViolinPlotView

from cytoflowgui.workflow.serialization import camel_registry, traits_repr, traits_str
from .view_base import IWorkflowView, WorkflowDataView, Data1DPlotParams

ViolinPlotView.__repr__ = traits_repr
    
class ViolinPlotParams(Data1DPlotParams):
    bw = Enum('scott', 'silverman')
    scale_plot = Enum('area', 'count', 'width')
    scale_hue = Bool(False)
    gridsize = CInt(100)
    inner = Enum("box", "quartile", None)
    split = Bool(False)
    
@provides(IWorkflowView)
class ViolinPlotWorkflowView(WorkflowDataView, ViolinPlotView):
    plot_params = Instance(ViolinPlotParams, ())
    
    def get_notebook_code(self, wi, idx):
        view = ViolinPlotView()
        view.copy_traits(self, view.copyable_trait_names())
        
        plot_params_str = traits_str(self.plot_params)

        return dedent("""
        {repr}.plot(ex_{idx}{plot}{plot_params})
        """
        .format(repr = repr(view),
                idx = idx,
                plot = ", plot_name = " + repr(self.current_plot) if self.plot_names else "",
                plot_params = ", " + plot_params_str if plot_params_str else ""))


@camel_registry.dumper(ViolinPlotView, 'violin-plot', version = 2)
def _dump(view):
    return dict(variable = view.variable,
                channel = view.channel,
                scale = view.scale,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                plotfacet = view.plotfacet,
                subset_list = view.subset_list,
                plot_params = view.plot_params,
                current_plot = view.current_plot)
    
@camel_registry.dumper(ViolinPlotWorkflowView, 'violin-plot', version = 1)
def _dump_v1(view):
    return dict(variable = view.variable,
                channel = view.channel,
                scale = view.scale,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                huescale = view.huescale,
                plotfacet = view.plotfacet,
                subset_list = view.subset_list)
    
@camel_registry.loader('violin-plot', version = any)
def _load(data, version):
    return ViolinPlotWorkflowView(**data)

@camel_registry.dumper(ViolinPlotParams, 'violin-plot-params', version = 1)
def _dump_params(params):
    return dict(
                # BasePlotParams
                title = params.title,
                xlabel = params.xlabel,
                ylabel = params.ylabel,
                huelabel = params.huelabel,
                col_wrap = params.col_wrap,
                sns_style = params.sns_style,
                sns_context = params.sns_context,
                legend = params.legend,
                sharex = params.sharex,
                sharey = params.sharey,
                despine = params.despine,

                # DataplotParams
                min_quantile = params.min_quantile,
                max_quantile = params.max_quantile,
                
                # Data1DPlotParams
                lim = params.lim,
                orientation = params.orientation,
                
                # Violin params
                bw = params.bw,
                scale_plot = params.scale_plot,
                scale_hue = params.scale_hue,
                gridsize = params.gridsize,
                inner = params.inner,
                split = params.split )
    
@camel_registry.loader('violin-plot-params', version = 1)
def _load_params(data, version):
    return ViolinPlotParams(**data)