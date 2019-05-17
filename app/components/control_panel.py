import dash
import dash_core_components as dcc
import dash_html_components as html
from dash_daq import BooleanSwitch
from app.components.helpers import row, col, container, panel, stat_summary_box

custom_size_toggle = html.Div([
    html.Span("Customize", style={'color': 'darkgray', 'position': 'relative', 'top': '-8px', 'left': '-4px', 'float': 'left !important', 'display': 'inline-block'}),
    BooleanSwitch(id='control-panel-volumes-pane-toggle', on=False, style={'position': 'relative', 'top': '-2px', 'float': 'left !important', 'display': 'inline-block'})
], style={'display': 'inline-block'}, className='pull-right')

storage_types = [
    {'label': "Amazon S3", 'value': "S3"},
    {'label': "Amazon S3 Infrequent Access", 'value': "S3IA"},
    {'label': "Amazon S3 IA Single-AZ", 'value': "S3IASAZ"},
    {'label': "Amazon Glacier", 'value': "glacier"},
    {'label': "Amazon Deep Glacier", 'value': "deepglacier"},
    {'label': "Google Regional", 'value': "gcp_regional"},
    {'label': "Google Nearline", 'value': "gcp_nearline"},
    {'label': "Google Coldline", 'value': "gcp_coldline"},
    {'label': "Azure ZRS Hot", 'value': "azure_zrs_hot"},
    {'label': "Azure ZRS Cool", 'value': "azure_zrs_cool"},
    {'label': "Azure LRS Hot", 'value': "azure_lrs_hot"},
    {'label': "Azure LRS Cool", 'value': "azure_lrs_cool"},
    {'label': "Azure LRS Archive", 'value': "azure_lrs_archive"},
]

control_panel = [
    panel(title="1. Test volumes", 
        additional_controls=[custom_size_toggle],
        children=[
        # potentially support ranges? Also allow for average size to be modified?
        html.Div(
            id="control-panel-volumes-simple-pane",
            style={'display': 'block'},
            children=[
                container([
                    row([dcc.Input(id='simple-volumes-genome-count', className='border-bottom', min=0, value=0, type='number'),
                        " Genomes per year ", html.Span("(30x coverage / 120GB each).", className='text-muted', style={'fontSize': "14px"})]),
                    row([dcc.Input(id='simple-volumes-exomes-count', className='border-bottom', min=0, value=0, type='number'),
                        " Exomes per year ", html.Span("(6GB each).", className='text-muted', style={'fontSize': "14px"})]),
                    row([dcc.Input(id='simple-volumes-large-panel-count', className='border-bottom', min=0, value=0, type='number'),
                        " Large panels per year ", html.Span("(300 genes / 1GB each).", className='text-muted', style={'fontSize': "14px"})]),
                    # row([dcc.Input(id='simple-volumes-small-panel-count', className='border-bottom', min=0, value=0, type='number'),
                    #     " Small panel (30 genes) per year"]),
                ])
            ]),
        html.Div(
            id="control-panel-volumes-custom-pane",
            style={'display': 'none'},
            children=[
                container([
                    row(["Genomes/year: ", 
                         dcc.Input(id='volumes-genome-count', className='border-bottom', min=0, value=0, type='number'),
                         " tests of ",
                         dcc.Input(id='volumes-genome-size', className='border-bottom', min=1, value=120, type='number'),
                         " GB each."]),
                    row(["Exomes/year: ", 
                         dcc.Input(id='volumes-exome-count', className='border-bottom', min=0, value=0, type='number'),
                         " tests of ",
                         dcc.Input(id='volumes-exome-size', className='border-bottom', min=1, value=6, type='number'),
                         " GB each."]),
                    row(["Targeted Panels/year: ", 
                         dcc.Input(id='volumes-panel-count', className='border-bottom', min=0, value=0, type='number'),
                         " tests of ",
                         dcc.Input(id='volumes-panel-size', className='border-bottom', min=0.1, value=1, type='number'),
                         " GB each."])
                ])
            ])
    ]),
    panel(title="2. File types", children=[
        html.Div([dcc.RadioItems(
            id='file-type-radio',
            options=[
                {'label': 'BAM', 'value': 'BAM'},
                {'label': 'CRAM v2', 'value': 'CRAMV2'},
                {'label': 'CRAM v3', 'value': 'CRAMV3'}
            ],
            value='BAM',
            labelStyle={'fontWeight': 'normal', 'paddingLeft': 10}
        )])
        ]),
        # Likely just some check/radio boxes
    panel(title="3. Retention time and storage", children=[
        # use a slider to create two storage tiers
        # have info buttons to describe tiers/differences on AWS (and other cloud providers?)
        container([
            row(["Store data in ", 
                dcc.Dropdown(
                    id='tier1-storage-type',
                    options=storage_types,
                    value='S3', clearable=False, multi=False, className='border-bottom-input', style={"width": "200px", "display": "inline-block"}),
                " for ", 
                dcc.Input(id='retention-time-tier1', className='border-bottom', min=0, value=2, type='number'),
                dcc.Dropdown(
                    id='retention-time-tier1-units',
                    options=[
                        {'label': 'year(s)', 'value': 'years'}, 
                        {'label': 'month(s)', 'value': 'months'}],
                    value='years', clearable=False, multi=False, className='border-bottom-input', 
                    style={"width": "100px", "display": "inline-block"})
                ]),
            row(["Then, store data in ", 
                 dcc.Dropdown(
                    id='tier2-storage-type',
                    options=storage_types,
                    value='glacier', clearable=False, multi=False, className='border-bottom-input', style={"width": "200px", "display": "inline-block"}),
                 " for ",
                 dcc.Input(id='retention-years-tier2', className='border-bottom', min=0, value=3, type='number', style={"width": "80px"}),
                 " years."])
        ])
    ]),
    panel(title="4. Data re-access", children=[
        #"rate/# of cases accessed each year; potentially split by years/storage tiers"
        container([
            row(["Re-access", 
                 dcc.Input(id='reaccess-count', className='border-bottom', min=0, value=0, type='number'),
                 "cases per year to ",
                 html.Div([dcc.Dropdown(
                        id='reaccess-target', 
                        options=[
                            {'label': "to the cloud", 'value': "within-cloud"},
                            {'label': "to the internet", 'value': "internet"}
                        ], value='within-cloud', clearable=False, multi=False, 
                        className='border-bottom-input')],
                    style={"display": "inline-block", "width": 200})
                 ])

        ])
    ]),
    panel(title="5. Other", children=[
        container([
            row(["Expected volume growth of ", 
                        dcc.Input(id='volume-growth', className='border-bottom', min=0, max=100, value=5, type='number'),
                        " percent per year."]),
            row(["Simulate ",
                 dcc.Input(id='total-years-simulated', className='border-bottom', min=0, max=25, value=15, type='number'),
                 " years total"
                ]),
            row(["Plot data in  ",
                 dcc.Dropdown(
                        id='time-interval-setting', 
                        options=[
                            {'label': "monthly", 'value': 1},
                            {'label': "yearly", 'value': 12},
                        ], value=12, clearable=False, multi=False, 
                        className='border-bottom-input',
                        style={"display": "inline-block", "width": 200}),
                " intervals."
                ])
        ])
    ])
]
