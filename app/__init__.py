import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go

import json
import numpy as np

from app.components.helpers import row, col, container, panel, stat_summary_box
from app.components.output_panel import output_panel
from app.components.control_panel import control_panel

external_stylesheets = [
    'https://codepen.io/chriddyp/pen/bWLwgP.css', 
    'https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css'
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.Div(id="data-store", style={'display': 'none'}),
    html.H2("The cost of genomic data storage in the clinical lab"),
    row([
        col('col-md-4', control_panel, style={"width": 600}),
        col('col-md-8', output_panel, style={"width": "auto"})
    ], style={"marginTop": 30})
])


def calc_cost(cost_buckets: list, amount):
    if amount <= cost_buckets[0][0] or len(cost_buckets) < 2:
        return cost_buckets[0][1] * amount
    return calc_cost(cost_buckets, cost_buckets[0][0]) + calc_cost(cost_buckets[1:], amount - cost_buckets[0][0])

def marginal_s3_cost(gb):
    # First 50 TB / Month $0.023 per GB
    # Next 450 TB / Month $0.022 per GB
    # Over 500 TB / Month $0.021 per GB
    buckets = [[50000, 0.023], [450000, 0.022], [np.inf, 0.021]]
    return calc_cost(buckets, gb)

def tier1_marginal_transfer_cost(gb, dest="internet"):
    if dest == "internet":
        # S3 to INTERNET
        # Up to 1 GB / Month  $0.00 per GB
        # Next 9.999 TB / Month   $0.09 per GB
        # Next 40 TB / Month  $0.085 per GB
        # Next 100 TB / Month $0.07 per GB
        # Greater than 150 TB / Month $0.05 per GB
        buckets = [[1, 0], [9999, 0.09], [40000, 0.085], [100000, 0.07], [np.inf, 0.05]]
        return calc_cost(buckets, gb)
    else:
    # to EC2 = $0.02 per GB
        return 0

def tier2_marginal_transfer_cost(gb, dest="internet"):
    if dest == "internet":
        # Glacier to INTERNET
        # Up to 1 GB / Month  $0.00 per GB
        # Next 9.999 TB / Month   $0.09 per GB
        # Next 40 TB / Month  $0.085 per GB
        # Next 100 TB / Month $0.07 per GB
        # Greater than 150 TB / Month $0.05 per GB
        buckets = [[1, 0], [9999, 0.09], [40000, 0.085], [100000, 0.07], [np.inf, 0.05]]
        return calc_cost(buckets, gb)
    else:
    # to EC2 = $0.02 per GB
        return gb * 0.02
    

@app.callback(
    Output('data-store', 'children'),
    [Input(component_id='volumes-genome-count', component_property='value'),
     Input(component_id='volumes-exome-count', component_property='value'),
     Input(component_id='volumes-panel-count', component_property='value'),
     Input(component_id='volumes-genome-size', component_property='value'),
     Input(component_id='volumes-exome-size', component_property='value'),
     Input(component_id='volumes-panel-size', component_property='value'),
     Input(component_id='retention-years-tier1', component_property='value'),
     Input(component_id='retention-years-tier2', component_property='value'),
     Input(component_id='volume-growth', component_property='value'),
     Input(component_id='reaccess-count', component_property='value'),
     Input(component_id='reaccess-target', component_property='value')]
)
def do_calculation(genome_count, exome_count, panel_count,
                genome_size, exome_size, panel_size, 
                retention_years_tier1, retention_years_tier2,
                volume_growth, reaccess_count, reaccess_target):
    
    running_total_samples = yearly_total_samples = genome_count + exome_count + panel_count
    running_total_gb = yearly_total_gb = (genome_count * genome_size) + (exome_count * exome_size) + (panel_count * panel_size)
    
    volume_multiplier = (1 + float(volume_growth/100))
    
    year_range = list(range(1,max(retention_years_tier1, retention_years_tier1+retention_years_tier2, 21)))

    yearly_costs = []
    yearly_total_stored = []
    yearly_total_gb_stored = []
    yearly_samples_run = []
    running_total_tier1 = 0
    running_total_tier2 = 0

    tier1_access_cost = 0
    tier2_access_cost = 0.01

    for y in year_range:
        yearly_total_gb_stored.append(running_total_gb)
        if y <= retention_years_tier1:
            # while in tier1 retention phase, all data is simply 
            # put into tier1 storage
            running_total_tier1 += running_total_gb
        elif y <= (retention_years_tier1 + retention_years_tier2):
            # once we are in the range where tier2 storage is used
            # data from `y - retention_years_tier1` is moved into 
            # tier2, and the runnign total is added to tier1
            running_total_tier1 -= yearly_total_gb_stored[y-retention_years_tier1]
            running_total_tier2 += yearly_total_gb_stored[y-retention_years_tier1]
            running_total_tier1 += running_total_gb
        else:
            # Once we are outside the life of the data, we discard tier2 
            running_total_tier2 -= yearly_total_gb_stored[y-(retention_years_tier1 + retention_years_tier2)]
            # data is still moved from tier1 to tier2
            running_total_tier1 -= yearly_total_gb_stored[y-retention_years_tier1]
            running_total_tier2 += yearly_total_gb_stored[y-retention_years_tier1]
            # we add new data to tier1
            running_total_tier1 += running_total_gb
        
        # calculate re-access costs
        if (running_total_tier1 + running_total_tier2) > 0:
            total_gb_reaccessed = ((reaccess_count * genome_count / yearly_total_samples) * genome_size) + \
                                  ((reaccess_count * exome_count / yearly_total_samples) * exome_size) + \
                                  ((reaccess_count * panel_count / yearly_total_samples) * panel_size)

            fraction_in_tier1 = running_total_tier1 / float(running_total_tier1 + running_total_tier2)
            fraction_in_tier2 = running_total_tier2 / float(running_total_tier1 + running_total_tier2)
            
            tier1_reaccess_cost = total_gb_reaccessed * (1-fraction_in_tier2) * tier1_access_cost
            tier2_reaccess_cost = total_gb_reaccessed * (fraction_in_tier2) * tier2_access_cost
            transfer_cost = tier1_marginal_transfer_cost(total_gb_reaccessed * (fraction_in_tier1), dest=reaccess_target) + \
                            tier2_marginal_transfer_cost(total_gb_reaccessed * (fraction_in_tier2), dest=reaccess_target)
            reaccess_cost = tier1_reaccess_cost + tier2_reaccess_cost + transfer_cost
        else:
            reaccess_cost = 0

        # calculate costs
        s3_cost      = marginal_s3_cost(12 * running_total_tier1)
        glacier_cost = 0.004 * 12 * running_total_tier2
        yearly_total_stored.append(running_total_tier1 + running_total_tier2)
        yearly_samples_run.append(running_total_samples)
        yearly_costs.append(s3_cost + glacier_cost + reaccess_cost)
        
        # increase total samples and GB generated in this iteration
        running_total_gb = running_total_gb * volume_multiplier
        running_total_samples = running_total_samples * volume_multiplier

    y_max = max(50, max(yearly_costs) * 1.1)
    y_max2 = max(50, max(yearly_total_stored) * 1.8)
    if y_max2 >= 1000:
        yearly_total_stored = list(np.array(yearly_total_stored)/1000.)
        y_max2 = y_max2 / 1000.
        units = "TB"
    else:
        units = "GB"

    data = {
        "year_range": year_range,
        "yearly_total_stored": yearly_total_stored,
        "yearly_samples_run": yearly_samples_run,
        "yearly_costs": yearly_costs,
        "units": units,
        "yearly_total_gb": yearly_total_gb,
        "yearly_total_samples": yearly_total_samples,
        "y_max": y_max,
        "y_max2": y_max2
    }
    return json.dumps(data)


@app.callback(
    Output('plot', 'figure'),
    [Input(component_id='data-store', component_property='children')])
def update_plot(data):
    data = json.loads(data)
    traces = [
        go.Bar(
            x= data["year_range"],
            y = data["yearly_total_stored"],
            name="Total %s Stored" % data["units"],
            yaxis='y2',
            opacity=0.6,
        ),
        go.Scatter(
            x = data["year_range"],
            y = data["yearly_costs"],
            name="Yearly Cost"
        ),
    ]
    return {
        'data': traces,
        'layout': go.Layout(
            margin=dict(l=70,r=40,t=10,b=30),
            height=500,
            yaxis = go.layout.YAxis(range=[0,data["y_max"]], title="Yearly Cost", tickprefix="$", fixedrange=True),
            yaxis2 = go.layout.YAxis(range=[0,data["y_max2"]], showgrid=False, title="Total %s Stored" % data["units"], 
                ticksuffix=data["units"], overlaying='y', side='right', fixedrange=True),
            xaxis = go.layout.XAxis(title="Year", fixedrange=True),
            legend=dict(orientation="h"),
        )
    }

@app.callback(
    Output('stats-boxes', 'children'),
    [Input(component_id='data-store', component_property='children')])
def update_stats(data):
    data = json.loads(data)
    lifetime_cost = int(np.array(data["yearly_costs"]).sum())
    total_samples = np.array(data["yearly_samples_run"]).sum()
    if total_samples > 0:
        cost_per_sample = lifetime_cost / total_samples
    else:
        cost_per_sample = 0
    return [
        row([
            col("col-md-4", [stat_summary_box("Total lifetime cost: ", "$%s" % lifetime_cost)]),
            col("col-md-4", [stat_summary_box("Total tests run: ", int(total_samples))]),
            col("col-md-4", [stat_summary_box("Average cost per test: ", "$%0.2f" % cost_per_sample)])
        ]),
        row([
            col("col-md-4", [stat_summary_box("Yearly tests run: ", data["yearly_total_samples"])]),
            col("col-md-4", [stat_summary_box("Yearly data generated: ", "%d GB" % data["yearly_total_gb"])])
        ])
    ]
