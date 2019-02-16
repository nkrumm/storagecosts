import dash
import dash_core_components as dcc
import dash_html_components as html

from app.components.helpers import row, col, container, panel, stat_summary_box

output_panel = [
    html.Div(stat_summary_box(
        "Costs per year",
        dcc.Graph(id='plot', config={'displayModeBar': False}, style={'width': 800})
    )),
    html.Div(id="stats-boxes")
]