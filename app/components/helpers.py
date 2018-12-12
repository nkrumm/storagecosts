import dash_core_components as dcc
import dash_html_components as html

def row(children, **kwargs):
    return html.Div(className='row', children=children, **kwargs)

def col(className, children):
    return html.Div(className=className, children=children)

def container(children, fluid=False, **kwargs):
    classname = "container-fluid" if fluid else "container"
    return html.Div(className=classname, children=children, **kwargs)

def well(children):
    return html.Div(className='well', children=children)

def panel(title, children):
    if title:
        title = html.Div(className='panel-heading', children=[html.H4(title, className="panel-title")])
    else:
        title = None
    body =  html.Div(className='panel-body', children=children)
    return html.Div(className='panel panel-default', children=[
        title, 
        body
    ])

def stat_summary_box(title, value):
    return well([
        html.H4(title, className="stats-title"),
        html.H4(value, className="stats-value")
    ])