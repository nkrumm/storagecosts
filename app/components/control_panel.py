import dash
import dash_core_components as dcc
import dash_html_components as html

from app.components.helpers import row, col, container, panel, stat_summary_box

control_panel = [
    panel(title="1. Test volumes", children=[
        # potentially support ranges? Also allow for average size to be modified?
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
                 " GB each."]),
            row(["Expected volume growth of ", 
                dcc.Input(id='volume-growth', className='border-bottom', min=0, max=100, value=10, type='number'),
                " percent per year."])
        ])
        
    ]),
    panel(title="2. File types", children=["BAM or FASTQ? Compression?"]),
        # Likely just some check/radio boxes
    panel(title="3. Retention time and storage", children=[
        # use a slider to create two storage tiers
        # have info buttons to describe tiers/differences on AWS (and other cloud providers?)
        container([
            row(["Store data in ", 
                 html.Div([dcc.Dropdown(disabled=True, options=[
                    {'label': "Amazon S3", 'value': "S3"},
                    {'label': "Amazon S3 Single AZ", 'value': "S3SAZ"},
                    {'label': "Amazon Glacier", 'value': "glacier"}],
                    value='S3', clearable=False, multi=False, className='border-bottom-input')], style={"display": "inline-block", "width": 200}),
                 " for ", 
                 dcc.Input(id='retention-years-tier1', className='border-bottom', min=0, value=2, type='number'),
                 " years."]),
            row(["Then, store data in ", 
                 html.Div([dcc.Dropdown(disabled=True, options=[
                    {'label': "Amazon S3", 'value': "S3"},
                    {'label': "Amazon S3 Single AZ", 'value': "S3SAZ"},
                    {'label': "Amazon Glacier", 'value': "glacier"}],
                    value='glacier', clearable=False, multi=False, className='border-bottom-input')], style={"display": "inline-block", "width": 200}),
                 " for ",
                 dcc.Input(id='retention-years-tier2', className='border-bottom', min=0, value=3, type='number'),
                 " years."]),
        ])
    ]),
    panel(title="4. Data re-access", children=[
        #"rate/# of cases accessed each year; potentially split by years/storage tiers"
        container([
            row(["# of cases re-accessed per year: ", 
                 dcc.Input(id='reaccess-count', className='border-bottom', min=0, value=0, type='number')])
        ])
    ]),
    panel(title="5. Other", children=[
        container([
            row(["other: Inflation, test volume growth, expected storage cost decrease"]),
        ])
    ])
]
