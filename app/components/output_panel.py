import dash
import dash_core_components as dcc
import dash_html_components as html

from app.components.helpers import row, col, container, panel, stat_summary_box, well

output_panel = [
    html.Div(stat_summary_box(
        "Costs over time",
        dcc.Graph(id='plot', config={'displayModeBar': False}, style={'width': 800})
    )),
    row([
        col("col-md-4", [
            html.Div(id="stats-boxes")
        ]),
        col("col-md-5", [
            html.Div(stat_summary_box(
            "Cost breakdown",
            dcc.Graph(id='piechart', config={'displayModeBar': False}, 
                style={'width': 320, 'height': 150, 'position': 'relative', 'top': "-10px"})
            ))
        ]),
        col("col-md-3", [
            html.Div(
            )
        ])
    ])
    
]