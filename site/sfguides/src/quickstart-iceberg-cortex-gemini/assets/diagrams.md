# Diagrams

All diagram-related code for the notebook.


## Architecture Diagram (Graphviz DOT)


```dot
digraph cortex_stack {
    rankdir=LR
    splines=ortho;
    graph [fontname="Helvetica", bgcolor="transparent", pad=0.4 style=dashed]
    node  [fontname="Helvetica", fontsize=11, style="filled,rounded", shape=box,
           fillcolor="#BBDEFB", color="#1565C0"]
    edge  [fontname="Helvetica", fontsize=14, color="#555555", arrowsize=0.7]
    
    subgraph cluster_data {
        label = "Extract"
        marketplace iceberg horizon
    }
    
    subgraph cluster_exploration {
        label="Explore"
        looker warehouse explore
    }

    marketplace [label="Snowflake Marketplace" shape=record]
    horizon [shape=record label="Federated Catalogs | {Snowflake \n Horizon | Lakehouse \n Runtime Catalog}"]
    iceberg [label="Customer GCS Iceberg \n - Parquet Data Files \n - Metadata json", shape=cylinder  fillcolor="#ddffdd"]
    warehouse [label="Adaptive Warehouse \n (on Google Axion)"]
    explore [label="Data Exploration | {Snowsight | Notebook}" shape=record]
    analyst [label="Cortex Analyst\n(Semantic Context)"]
    agent   [label="Cortex Agents \n (Powered by Gemini)"]
    cowork  [label="CoWork \n (Insights and Reports)"]
    gemini  [label="Gemini Enterprise \n (Corporate AI Hub)"  fillcolor="#ddffdd"]
    looker  [label="Looker Dashboard" fillcolor="#ddffdd" ]
    coco    [label="CoCo \n (Agentic Assistent)"]

    horizon -> iceberg [xlabel="manages"  constraint=false]
    iceberg -> marketplace [dir=back constraint=false] 

    iceberg -> warehouse
    warehouse -> analyst
    looker -> warehouse [dir=back  constraint=false]
    warehouse -> explore [ constraint=false]

    analyst -> agent
    agent -> gemini [label="MCP"]
    agent -> {cowork coco}
    
    subgraph cluster_end_user {
        label="Enterprise AI Apps"
        gemini
        cowork
        coco
    }
}
```


## Spotlight Display Snippet (Python)

Used in the notebook to show the architecture diagram with a spotlight region highlighting the current section. The SVG is pre-rendered from the DOT above and stored at `input/arch-diagram.svg`.

```python
from IPython.display import display, HTML
import base64, pathlib

def spotlight(image_path, left=0, top=0, right=100, bottom=100):
    """Display an image with a dark overlay and a bright cutout region (percentages)."""
    svg_data = pathlib.Path(image_path).read_text()
    b64 = base64.b64encode(svg_data.encode()).decode()
    img_src = f"data:image/svg+xml;base64,{b64}"
    display(HTML(f'''
    <div style="position:relative; width:100%; line-height:0;">
      <img src="{img_src}" style="width:100%; display:block;" />
      <svg style="position:absolute; top:0; left:0; width:100%; height:100%;" viewBox="0 0 100 100" preserveAspectRatio="none">
        <defs>
          <mask id="spotlight">
            <rect x="0" y="0" width="100" height="100" fill="white" />
            <rect x="{left}" y="{top}" width="{right-left}" height="{bottom-top}" fill="black" />
          </mask>
        </defs>
        <rect x="0" y="0" width="100" height="100" fill="black" fill-opacity="0.55" mask="url(#spotlight)" />
      </svg>
    </div>
    '''))
```


## Spotlight Calls Per Section

Each section shows the diagram with a different region highlighted:

```python
# Marketplace + Iceberg (left side)
spotlight("input/arch-diagram.svg", left=3, top=10, right=23, bottom=90)

# GCS Bucket + Iceberg Table (center-left)
spotlight("input/arch-diagram.svg", left=23, top=10, right=42, bottom=90)

# Cortex: Semantic View + Agent (center-right)
spotlight("input/arch-diagram.svg", left=42, top=10, right=75, bottom=90)

# MCP + Gemini Enterprise (right side)
spotlight("input/arch-diagram.svg", left=57, top=45, right=100, bottom=60)
```
