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

    
storage_cost_buckets = {
    "S3": [[50000, 0.023], [450000, 0.022], [np.inf, 0.021]],
    "glacier": [[np.inf, 0.004]],
    "deepglacier": [[np.inf, 0.00099]],
    "S3IA":    [[np.inf, 0.0125]],
    "S3IASAZ": [[np.inf, 0.01]],
    "gcp_regional": [[np.inf, 0.02]],
    "gcp_nearline": [[np.inf, 0.01]],
    "gcp_coldline": [[np.inf, 0.007]],
    "gcp_archive": [[np.inf, 0.0025]],
    "azure_zrs_hot": [[50000, 0.023], [450000, 0.0221], [np.inf, 0.0212]],
    "azure_zrs_cool": [[np.inf, 0.0125]],
    "azure_lrs_hot": [[50000, 0.0184], [450000, 0.0177], [np.inf, 0.017]],
    "azure_lrs_cool": [[np.inf, 0.01]],
    "azure_lrs_archive": [[np.inf, 0.00099]],
}

transfer_cost_buckets = {
    "s3": [[1, 0], [9999, 0.09], [40000, 0.085], [100000, 0.07], [np.inf, 0.05]],
    "glacier": [[1, 0], [9999, 0.09], [40000, 0.085], [100000, 0.07], [np.inf, 0.05]],
    "gcp": [[1000, 0.12], [9000, 0.11], [np.inf, 0.08]],
    "azure": [[5, 0], [9995, 0.087], [40000, 0.083], [100000, 0.07], [np.inf, 0.05]]
}

def calc_storage_cost(storage_type, gb):
    return calc_cost(storage_cost_buckets[storage_type], gb)

def calc_reaccess_cost(storage_type, gb):
    if storage_type in ["S3"]:
        return 0
    elif storage_type in ["S3IA", "S3IASAZ"]:
        return gb * 0.01
    elif storage_type in ["glacier", "deepglacier"]:
        return gb * 0.0025
    elif storage_type == "gcp_regional":
        return 0
    elif storage_type == "gcp_nearline":
        return gb * 0.01
    elif storage_type == "gcp_coldline":
        return gb * 0.02
    elif storage_type == "gcp_archive":
        return gb * 0.05
    elif storage_type in ["azure_lrs_hot", "azure_zrs_hot"]:
        return 0
    elif storage_type in ["azure_lrs_cool", "azure_zrs_cool"]:
        return gb * 0.01
    elif storage_type in ["azure_lrs_archive"]:
        return gb * 0.02
    else:
        raise Exception("unknown reaccess costs")


def calc_transfer_cost(storage_type, destination, gb):
    assert destination in ["internet", "within-cloud"]
    if destination == "within-cloud":
        return 0
    else: # to internet
        if storage_type in ["S3", "S3IA", "S3IASAZ"]:
            return calc_cost(transfer_cost_buckets["s3"], gb)
        elif storage_type in ["glacier", "deepglacier"]:
            return calc_cost(transfer_cost_buckets["glacier"], gb)
        elif storage_type.startswith("gcp"):
            return calc_cost(transfer_cost_buckets["gcp"], gb)
        elif storage_type.startswith("azure"):
            return calc_cost(transfer_cost_buckets["azure"], gb)
        else:
            raise Exception("unknown transfer costs")

def get_compression_factor(file_type):
    if file_type == "BAM":
        return 1
    elif file_type == "CRAMV2":
        return 0.7
    elif file_type == "CRAMV3":
        return 0.6
    else:
        raise("Invalid compression type")


def resample(array, interval, func=np.sum):
    a = np.array(array).reshape(-1, interval)
    return list(np.apply_along_axis(func, 1, a))

def convert_int64(o):
        if isinstance(o, np.int64): return int(o)  
        raise TypeError

@app.callback(
    Output('data-store', 'children'),
    [
     Input(component_id='control-panel-volumes-pane-toggle', component_property='on'),
     Input(component_id='simple-volumes-genome-count', component_property='value'),
     Input(component_id='simple-volumes-exomes-count', component_property='value'),
     Input(component_id='simple-volumes-large-panel-count', component_property='value'),
     #Input(component_id='simple-volumes-small-panel-count', component_property='value'),
     Input(component_id='volumes-genome-count', component_property='value'),
     Input(component_id='volumes-exome-count', component_property='value'),
     Input(component_id='volumes-panel-count', component_property='value'),
     Input(component_id='volumes-genome-size', component_property='value'),
     Input(component_id='volumes-exome-size', component_property='value'),
     Input(component_id='volumes-panel-size', component_property='value'),
     Input(component_id='file-type-radio', component_property='value'),
     Input(component_id='retention-time-tier1', component_property='value'),
     Input(component_id='retention-time-tier1-units', component_property='value'),
     Input(component_id='retention-years-tier2', component_property='value'),
     Input(component_id='tier1-storage-type', component_property='value'),
     Input(component_id='tier2-storage-type', component_property='value'),
     Input(component_id='volume-growth', component_property='value'),
     Input(component_id='total-years-simulated', component_property='value'),
     Input(component_id='reaccess-count', component_property='value'),
     Input(component_id='reaccess-target', component_property='value'),
     Input(component_id='time-interval-setting', component_property='value')]
)
def do_calculation(
                is_custom,
                simple_genome_count, simple_exome_count, 
                simple_large_panel_count, #simple_small_panel_count,
                genome_count, exome_count, panel_count,
                genome_size, exome_size, panel_size, 
                file_type,
                retention_time_tier1, retention_time_tier1_units, 
                retention_years_tier2,
                tier1_storage_type, tier2_storage_type,
                volume_growth, total_years_simulated,
                reaccess_count, reaccess_target,
                interval):

    compression = get_compression_factor(file_type)

    if not is_custom:
        genome_count = simple_genome_count
        genome_size = 120 * compression
        exome_count = simple_exome_count
        exome_size = 6 * compression
        panel_count = simple_large_panel_count
        panel_size = 1 * compression

    # note this routine defines timepoints in MONTHS
    
    # convert years from input to months (for calculations)
    if retention_time_tier1_units == "years":
        retention_time_tier1 = retention_time_tier1 * 12
    retention_time_tier2 = retention_years_tier2 * 12
    total_time_simulated = total_years_simulated * 12

    # find maximum timeframe we need to calculate
    m = max(retention_time_tier1, retention_time_tier1+retention_time_tier2, total_time_simulated+1)
    timepoints = list(range(1,m))

    # for first month, define running_total_samples as 1/12th of total yearly samples
    yearly_total_samples = (genome_count + exome_count + panel_count)
    running_total_samples = yearly_total_samples / 12.
    
    # same for total gb stored
    yearly_total_gb = (genome_count * genome_size) + (exome_count * exome_size) + (panel_count * panel_size)
    running_total_gb = yearly_total_gb / 12.
    
    # define monthly multiplier based on yearly percent growth
    monthly_volume_multiplier = (1 + float(volume_growth/12./100))

    # same for reaccess-count
    monthly_reaccess_count = reaccess_count/12.

    # initialize arrays and counters
    costs_array = []
    tier1_storage_cost_array = []
    tier2_storage_cost_array = []
    reaccess_cost_array = []
    total_stored_array = []
    total_gb_stored_array = []
    samples_run_array = []
    running_total_tier1 = 0
    running_total_tier2 = 0

    for y in timepoints:
        total_gb_stored_array.append(running_total_gb)
        if y <= retention_time_tier1:
            # while in tier1 retention phase, all data is simply 
            # put into tier1 storage
            running_total_tier1 += running_total_gb
        elif y <= (retention_time_tier1 + retention_time_tier2):
            # once we are in the range where tier2 storage is used
            # data from `y - retention_time_tier1` is moved into 
            # tier2, and the runnign total is added to tier1
            running_total_tier1 -= total_gb_stored_array[y-retention_time_tier1]
            running_total_tier2 += total_gb_stored_array[y-retention_time_tier1]
            running_total_tier1 += running_total_gb
        else:
            # Once we are outside the life of the data, we discard tier2 
            running_total_tier2 -= total_gb_stored_array[y-(retention_time_tier1 + retention_time_tier2)]
            # data is still moved from tier1 to tier2
            running_total_tier1 -= total_gb_stored_array[y-retention_time_tier1]
            running_total_tier2 += total_gb_stored_array[y-retention_time_tier1]
            # we add new data to tier1
            running_total_tier1 += running_total_gb

        # calculate storage costs
        tier1_cost = calc_storage_cost(tier1_storage_type, running_total_tier1)
        tier2_cost = calc_storage_cost(tier2_storage_type, running_total_tier2)

        # calculate re-access costs, includes transfer cost
        if (running_total_tier1 + running_total_tier2) > 0:
            total_gb_reaccessed = ((monthly_reaccess_count * genome_count / yearly_total_samples) * genome_size) + \
                                  ((monthly_reaccess_count * exome_count / yearly_total_samples) * exome_size) + \
                                  ((monthly_reaccess_count * panel_count / yearly_total_samples) * panel_size)

            fraction_in_tier1 = running_total_tier1 / float(running_total_tier1 + running_total_tier2)
            fraction_in_tier2 = running_total_tier2 / float(running_total_tier1 + running_total_tier2)

            tier1_reaccess_cost = calc_reaccess_cost(tier1_storage_type, total_gb_reaccessed * (fraction_in_tier1))            
            tier2_reaccess_cost = calc_reaccess_cost(tier2_storage_type, total_gb_reaccessed * (fraction_in_tier2))
            
            tier1_transfer_cost = calc_transfer_cost(tier1_storage_type, reaccess_target, total_gb_reaccessed * (fraction_in_tier1))
            tier2_transfer_cost = calc_transfer_cost(tier2_storage_type, reaccess_target, total_gb_reaccessed * (fraction_in_tier2))
            
            reaccess_cost = tier1_reaccess_cost + tier2_reaccess_cost + tier1_transfer_cost + tier2_transfer_cost
        else:
            reaccess_cost = 0

        
        # record costs in arrays
        tier1_storage_cost_array.append(tier1_cost)
        tier2_storage_cost_array.append(tier2_cost)
        reaccess_cost_array.append(reaccess_cost)
        total_stored_array.append(running_total_tier1 + running_total_tier2)
        samples_run_array.append(running_total_samples)
        costs_array.append(tier1_cost + tier2_cost + reaccess_cost)
        
        # increase total samples and GB generated in this iteration
        running_total_gb = running_total_gb * monthly_volume_multiplier
        running_total_samples = running_total_samples * monthly_volume_multiplier

    # resample data to 1-month, 3-month, 6-month or 12-month intervals
    timepoints = list(((np.array(timepoints)-1).reshape(-1, interval)[:,0]/interval).astype(int))
    total_stored_array = resample(total_stored_array, interval, max)
    samples_run_array = resample(samples_run_array, interval)
    costs_array = resample(costs_array, interval)
    tier1_storage_cost_array = resample(tier1_storage_cost_array, interval)
    tier2_storage_cost_array = resample(tier2_storage_cost_array, interval)
    reaccess_cost_array = resample(reaccess_cost_array, interval)
    
    y_max = max(50, max(costs_array) * 1.1)
    y_max2 = max(50, max(total_stored_array) * 1.8)
    if y_max2 >= 1000:
        total_stored_array = list(np.array(total_stored_array)/1000.)
        y_max2 = y_max2 / 1000.
        units = "TB"
    else:
        units = "GB"

    data = {
        "timepoints": timepoints,
        "total_stored_array": total_stored_array,
        "samples_run_array": samples_run_array,
        "costs_array": costs_array,
        "tier1_storage_cost_array": tier1_storage_cost_array,
        "tier2_storage_cost_array": tier2_storage_cost_array,
        "reaccess_cost_array": reaccess_cost_array,
        "units": units,
        "interval": int(interval),
        "y_max": int(y_max),
        "y_max2": int(y_max2),
        "test_count_fractional": {  
            "genome": genome_count / yearly_total_samples,
            "exome": exome_count / yearly_total_samples,
            "panel": panel_count / yearly_total_samples,
        } if yearly_total_samples > 0 else {"genome": 0, "exome": 0, "panel": 0},
        "test_gb_fractional": {
            "genome": (genome_count * genome_size) / yearly_total_gb,
            "exome": (exome_count * exome_size) / yearly_total_gb,
            "panel": (panel_count * panel_size) / yearly_total_gb,
        } if yearly_total_gb > 0 else {"genome": 0, "exome": 0, "panel": 0},
    }
    # see here for info about the `default` arg (needed to serialize np.int64s in python3)
    # https://stackoverflow.com/questions/11942364/typeerror-integer-is-not-json-serializable-when-serializing-json-in-python
    return json.dumps(data, default=convert_int64)


@app.callback(
    Output('plot', 'figure'),
    [Input(component_id='data-store', component_property='children')])
def update_plot(data):
    data = json.loads(data)
    
    if data["interval"] == 1:
        interval_str = "Monthly"
        x_tickvals = list(np.array(data["timepoints"]).reshape(-1,12)[:,0])
        x_ticklabels = x_tickvals
    else:
        interval_str = "Yearly"
        x_tickvals = data["timepoints"]
        x_ticklabels = x_tickvals

    traces = [
        go.Bar(
            x= data["timepoints"],
            y = data["total_stored_array"],
            name="Total %s Stored" % data["units"],
            yaxis='y2',
            opacity=0.6,
        ),
        go.Scatter(
            x = data["timepoints"],
            y = data["costs_array"],
            name="Total %s Cost" % interval_str
        ),
        go.Scatter(
            x = data["timepoints"],
            y = data["tier1_storage_cost_array"],
            name="Tier 1 Cost",
            visible = "legendonly"
        ),
        go.Scatter(
            x = data["timepoints"],
            y = data["tier2_storage_cost_array"],
            name="Tier 2 Cost",
            visible = "legendonly"
        ),
    ]
    return {
        'data': traces,
        'layout': {
            "margin": dict(l=70,r=60,t=20,b=60),
            "height": 500,
            "yaxis": go.layout.YAxis(
                        range=[0,data["y_max"]],
                        title="Total %s Cost" % interval_str,
                        tickprefix="$",
                        hoverformat = '.0f',
                        fixedrange=True),
            "yaxis2": go.layout.YAxis(
                        range=[0,data["y_max2"]],
                        showgrid=False,
                        title="Total %s Stored" % data["units"], 
                        ticksuffix=data["units"],
                        overlaying='y',
                        hoverformat = '.1f',
                        side='right',
                        fixedrange=True),
            "xaxis": go.layout.XAxis(
                        title=interval_str.replace("ly", "s"),
                        ticktext=x_ticklabels,
                        tickvals=x_tickvals,
                        fixedrange=True),
            "legend": dict(orientation="h", y=1.05, x=0.18),
            "uirevision": 'same' # preserve layout even when parameters change
        }
    }

@app.callback(
    Output('piechart', 'figure'),
    [Input(component_id='data-store', component_property='children')])
def update_piechart(data):
    data = json.loads(data)
    labels = ["Tier 1 Cost", "Tier 2 Cost", "Reaccess Cost"]
    values = [
        sum(data["tier1_storage_cost_array"]),
        sum(data["tier2_storage_cost_array"]),
        sum(data["reaccess_cost_array"])
    ]
    traces = [go.Pie(
        labels=labels, values=values, 
        direction='clockwise',
        sort=False,
        textinfo="percent",
        hoverinfo="none"

    )]
    return {
        'data': traces,
        'layout': go.Layout(
            margin=dict(l=30,r=10,t=20,b=0),
            legend=dict(x=1.3, y=0.8)
        )
    }

@app.callback(
    Output('stats-boxes', 'children'),
    [Input(component_id='data-store', component_property='children')])
def update_stats(data):
    data = json.loads(data)
    lifetime_cost = int(np.array(data["costs_array"]).sum())
    total_samples = np.array(data["samples_run_array"]).sum()
    if total_samples > 0:
        cost_stats = []
        for tt in ["genome", "exome", "panel"]:
            if data["test_gb_fractional"][tt] > 0:
                cost = float(lifetime_cost) * data["test_gb_fractional"][tt] / (total_samples * data["test_count_fractional"][tt])
                e = html.Div([
                        html.Span("%s: " % tt, style={"fontSize": 21, "fontWeight": 400, "paddingRight": 6}),
                        html.Span("$%0.2f" % cost)
                ])
                cost_stats.append(e)
    else:
        cost_stats = []
    return [
        stat_summary_box("Total lifetime cost: ", '${:,}'.format(lifetime_cost)),
        stat_summary_box("Average cost per test: ", cost_stats)   
    ]

@app.callback(
    Output('control-panel-volumes-custom-pane', 'style'),
    [Input(component_id='control-panel-volumes-pane-toggle', component_property='on')])
def display_volume_pane_custom(pane_state_is_complex):
    if pane_state_is_complex:
        return {'display': 'block'}
    else:
        return {'display': 'none'}

@app.callback(
    Output('control-panel-volumes-simple-pane', 'style'),
    [Input(component_id='control-panel-volumes-pane-toggle', component_property='on')])
def display_volume_pane_simple(pane_state_is_complex):
    if pane_state_is_complex:
        return {'display': 'none'}
    else:
        return {'display': 'block'}
