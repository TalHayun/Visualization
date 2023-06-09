import pandas as pd
import streamlit as st
import altair as alt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
from matplotlib import cm
import numpy as np
from lifelines import KaplanMeierFitter
from plotly.subplots import make_subplots

image = Image.open('dataset-cover.jpg')
df = pd.read_csv('Breast_Cancer.csv')

# Define the bin edges
bin_edges = [30, 40, 50, 60, 70]

# Define the corresponding bin labels
bin_labels = ['30-39', '40-49', '50-59', '60-69']

# Convert numeric 'Age' to categorical using bins and labels
df['Age'] = pd.cut(df['Age'], bins=bin_edges, labels=bin_labels, right=False)


agg_df = df.groupby('Race').agg(malignancy_rate=('A Stage', lambda x: sum(x == 'Distant') / len(x) * 100),
                                    avg_tumor_size=('Tumor Size', 'mean')).reset_index()
grouped_df = agg_df.sort_values(by=['Race'], key=lambda x: x.map({v: i for i, v in enumerate(['Other', 'White', 'Black'])}))


def get_mortality_rate(feature_name):
    mortality_df = df.groupby(feature_name)['Status'].value_counts().unstack().fillna(0)
    mortality_df['Mortality Rate'] = mortality_df['Dead'] / (mortality_df['Dead'] + mortality_df['Alive'])
    return mortality_df

def build_st_query_for_line_charts(title: str, options: list):
    feature = st.radio(f"#### Select {title}", options)
    return feature

def build_st_query_for_ridge_charts(title: str, options: list):
    st.write(f"#### {title}")
    checkbox_states = {}
    # Add "Select All" checkbox
    if title == 'Age':
        select_all = st.checkbox("All Ages")
    elif title == 'Race':
        select_all = st.checkbox("All Races")
    else:
        select_all = st.checkbox("All Marital Statuses")
    checkbox_states = {}  # Dictionary to store checkbox states

    if select_all:
        for option in options:
            checkbox_key = f"{option} ({title})"
            checkbox_states[option] = st.checkbox(option, key=checkbox_key, value=True)
    else:
        for option in options:
            checkbox_key = f"{option} ({title})"
            checkbox_states[option] = st.checkbox(option, key=checkbox_key, value=checkbox_states.get(option, False))

    return checkbox_states

def get_checkbox_list(checkbox_dict):
    return [key for key, val in checkbox_dict.items() if val]


def create_virdis(num):
    viridis = cm.get_cmap('viridis', 12)
    virdis_list = viridis(np.linspace(0, 1, num))

    modified_array = []
    for lst in virdis_list:
        modified_list = lst[:-1]  # Remove the last element from the list
        rgb_string = f'rgb({modified_list[0]}, {modified_list[1]}, {modified_list[2]})'
        modified_array.append(rgb_string)

    return modified_array


def build_heatmap():
    st.markdown("<h3 style='text-align: left;'>What are the relationships between age, race, and marital status on the mortality of women with breast cancer in America?</h3>", unsafe_allow_html=True)

    col1 = st.columns(1)

    with col1[0]:
        options_feature1 = ['Age', 'Race', 'Marital Status']
        feature1 = build_st_query_for_line_charts("main feature", options_feature1)

    st.markdown(f"<h4 style='text-align: left;'>Mortality Rate by {feature1}</h4>", unsafe_allow_html=True)


    mortality_df = get_mortality_rate(feature1).sort_values(by='Mortality Rate')
    bar_fig = go.Figure()

    bar_fig.add_trace(go.Bar(
          x=mortality_df.index,
          y=mortality_df['Mortality Rate'],
          marker=dict(color='salmon')
      ))
    bar_fig.update_layout(
        yaxis=dict(title=dict(text="<b>Mortality Rate (%)</b>", font=dict(size=20))),
        xaxis=dict(title=dict(text=f"<b>{feature1}</b>", font=dict(size=20)), tickfont=dict(size=18)),
        yaxis_tickfont=dict(size=18),
        xaxis_tickfont=dict(size=18),
        bargap= 0.5)
    st.plotly_chart(bar_fig)


    col2 = st.columns(1)
    with col2[0]:
        options_feature2 = ['Age', 'Race', 'Marital Status']
        options_feature2.remove(feature1)
        feature2 = build_st_query_for_line_charts("secondary feature", options_feature2)

    st.markdown(f"<h4 style='text-align: left;'>Mortality Rate by {feature1} and {feature2}</h4>", unsafe_allow_html=True)

    # Calculate the mortality rates based on the "Dead" values
    pivot_df = df.pivot_table(index=feature1, columns=feature2, values='Status',
                              aggfunc=lambda x: round(sum(x == 'Dead') / len(x), 2))

    # Create a heatmap using Plotly Express
    fig = px.imshow(pivot_df, text_auto=True, color_continuous_scale='reds', labels=dict(color="Mortality rate (%)", font=dict(size=18)))
    fig.update_xaxes(side="top")
    fig.update_layout(height=600, width=800)
    fig.update_traces(textfont=dict(size=16))
    fig.update_layout(
    yaxis=dict(title=dict(text=f"<span style='font-weight:bold'>{feature1}</span>", font=dict(size=22)), tickfont=dict(size=16)),
    xaxis=dict(title=dict(text=f"<b>{feature2}</b>", font=dict(size=22)), tickfont=dict(size=16)),
    coloraxis_colorbar=dict(title=dict(text='<b>Mortality<br>Rate (%)<b>', font=dict(size=22)), tickfont=dict(size=16))
)
    # Display the heatmap in Streamlit
    st.plotly_chart(fig)


def build_two_y_axis_chart():
    st.markdown("<h3 style='text-align: left;'>Are there racial disparities in breast cancer diagnosiss?</h3>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: left;'>Malignancy Rate and Average Tumor Size by Race</h4>", unsafe_allow_html=True)


    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=grouped_df['Race'],
        y=grouped_df['malignancy_rate'],
        name='Malignancy Rate',
        yaxis='y',
        offsetgroup=0,
        width=0.25,
        marker=dict(color='salmon')
    ))

    fig.add_trace(go.Bar(
        x=grouped_df['Race'],
        y=grouped_df['avg_tumor_size'],
        name='Average Tumor Size',
        yaxis='y2',
        offsetgroup=1,
        width=0.25,
        marker=dict(color='lightseagreen')
    ))

    fig.update_layout(height=500, width=900,
        xaxis=dict(title='<b>Race<b>', title_font=dict(size=22), tickfont=dict(size=16)),
                      yaxis=dict(
                          title='<b>Malignancy Rate (%)</b>',
                          title_font=dict(size=22),
                          tickfont=dict(size=16),
                          range=[0, 3],  # Set the y-axis range from 0 to 3
                          dtick=0.5  # Set the tick increment to 0.5
                      ),
        yaxis2=dict(title='<b>Average Tumor Size (mm)<b>', overlaying='y', side='right', title_font=dict(size=22), tickfont=dict(size=16), range=[0, 30],dtick=5),
        barmode='group',
        legend_x=1.2,
        legend_font=dict(size=16),  # Increase the legends' font size
        bargap=0.5  # Adjust the spacing between the bars
    )

    st.plotly_chart(fig)


def create_ridge(age_dict, race_dict, marital_dict, fig, row_fig, col):
    survived = df[df['Status'] == 'Alive']

    age_list = [key for key, val in age_dict.items() if val]
    race_list = [key for key, val in race_dict.items() if val]
    marital_list = [key for key, val in marital_dict.items() if val]

    grouped = survived
    group_by_list = []
    if age_list:
        grouped = grouped[grouped['Age'].isin(age_list)]
        group_by_list.append('Age')
    if race_list:
        grouped = grouped[grouped['Race'].isin(race_list)]
        group_by_list.append('Race')
    if marital_list:
        grouped = grouped[grouped['Marital Status'].isin(marital_list)]
        group_by_list.append('Marital Status')

    if age_list or race_list or marital_list:
        grouped = grouped.groupby(group_by_list).agg(
            {'Survival Months': ['mean', 'count']}).reset_index()
        grouped = grouped[grouped['Survival Months']['count'] >= 2]
        grouped = grouped.sort_values(by=[('Survival Months', 'mean')], ascending=False)

        num_of_colors = len(grouped)
        colors = create_virdis(num_of_colors)
        i = 0

        # Iterate through each group
        for _, row in grouped.iterrows():
            name = ""
            survived_copy = survived.copy()
            if age_list:
                age = row['Age'][0]
                survived_copy = survived_copy[(survived_copy['Age'] == age)]
                name += f'{age},'
            if race_list:
                race = row['Race'][0]
                survived_copy = survived_copy[(survived_copy['Race'] == race)]
                name += f'{race},'
            if marital_list:
                marital_status = row['Marital Status'][0]
                survived_copy = survived_copy[(survived_copy['Marital Status'] == marital_status)]
                name += f'{marital_status},'
            values = survived_copy['Survival Months']
            name = name[:len(name) - 1]
            fig.add_trace(go.Violin(x=values, line_color=colors[i], name=name, showlegend=False,
                                    meanline_visible=True, legendgroup='1'), row=row_fig, col=col)

            annotation = dict(
                xref='x',
                yref='y',
                x=150,
                y=i * 1,
                text=name,
                showarrow=False,
                font=dict(color='black'),
                xanchor='left'
            )
            fig.add_annotation(annotation, row=row_fig, col=col)

            i += 1
    else:
        fig.add_trace(go.Violin(visible='legendonly', showlegend=False))



def create_km_graph(name, name_dict, fig, row, col):
    survived = df.copy()
    survived['Status'] = survived['Status'].map({'Alive': 1, 'Dead': 0})

    name_list = [key for key, val in name_dict.items() if val]

    if name == 'Age':
        legendgroup = '2'
    elif name == 'Race':
        legendgroup = '3'
    else:
        legendgroup = '4'

    if name_list:
        survived = survived[survived[name].isin(name_list)]

        n_colors = len(survived[name].unique())

        # Define a color palette with different colors
        color_palette = create_virdis(n_colors)

        for i, value in enumerate(survived[name].unique()):
            kmf = KaplanMeierFitter()

            # Filter data for the current value
            group_survived = survived[survived[name] == value]

            survival_time = group_survived['Survival Months']
            status = group_survived['Status']

            kmf.fit(survival_time, status)
            survival_probs = kmf.survival_function_

            # Flip the survival probabilities
            survival_probs['KM_estimate'] = 1 - survival_probs['KM_estimate']

            fig.add_trace(go.Scatter(
                x=kmf.survival_function_.index, y=kmf.survival_function_['KM_estimate'],
                mode='lines',  # Update the mode to 'lines'
                line=dict(shape='hv', width=3, color=color_palette[i]),
                name=value,
                legendgroup=legendgroup,
                legendgrouptitle=dict(text=f'{name}', font=dict(size=18))
            ), row=row, col=col)

    else:
        # Add a dummy trace with invisible lines and markers to represent the legend title
        fig.add_trace(go.Scatter(
            x=[0],
            y=[0],
            marker=dict(color='rgba(0, 0, 0, 0)', opacity=0),
            name="",
            legendgroup=legendgroup,
            showlegend=True,
            legendgrouptitle=dict(text=f'{name}', font=dict(size=18))
        ), row=row, col=col)

def figure3():
    st.markdown("<h3 style='text-align: left;'>Women with which characteristics are more likely to have a short recovery from breast cancer?</h3>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: left;'>Select Characteristics</h4>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    st.markdown("<h4 style='text-align: left;'>Kaplan-Meier Recovery Estimates and Recovery Time Distribution charts</h4>", unsafe_allow_html=True)
    st.markdown("<h6 style='text-align: left;'>Only groups with more than one patient were added</h6>", unsafe_allow_html=True)

    with col1:
        age_dict = build_st_query_for_ridge_charts(
            "Age", ['60-69', '50-59', '40-49', '30-39']
        )

    with col2:
        race_dict = build_st_query_for_ridge_charts(
            "Race", ['White', 'Black', 'Other']
        )

    with col3:
        marital_dict = build_st_query_for_ridge_charts(
            "Marital Status", ['Married', 'Divorced', 'Single ', 'Widowed', 'Separated']
        )

    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=("", "--Dashed line represents the average recovery time", "", ""),
        specs=[[{}, {"rowspan": 3}],
               [{}, None],
               [{}, None]],
        column_widths=[0.35, 0.65],
        print_grid=True
    )

    create_ridge(age_dict, race_dict, marital_dict, fig, 1, 2)

    create_km_graph('Age', age_dict, fig, 1, 1)
    create_km_graph('Race', race_dict, fig, 2, 1)
    create_km_graph('Marital Status', marital_dict, fig, 3, 1)

    age_list = [key for key, val in age_dict.items() if val]
    if age_list:
        tracegroupgap = 180
    else:
        tracegroupgap = 220

    # Update x_range
    fig.update_xaxes(range=[0, 60], row=1, col=1)
    fig.update_xaxes(range=[0, 60], row=2, col=1)
    fig.update_xaxes(range=[0, 60], row=3, col=1)
    fig.update_xaxes(range=[0, 220], dtick=20, tickvals=list(range(0, 141, 20)), row=1, col=2)

    # Update y_range
    fig.update_yaxes(range=[0, 0.25], row=1, col=1)
    fig.update_yaxes(range=[0, 0.25], row=2, col=1)
    fig.update_yaxes(range=[0, 0.25], row=3, col=1)
    fig.update_yaxes(showticklabels=False, row=1, col=2)

    # Violin positive
    fig.update_traces(orientation='h', side='positive', width=5, points=False, row=1, col=2)

    fig.update_layout(height=900, width=800,
                      xaxis1=dict(title='<b>Time (Months)<b>', title_font=dict(size=20)),
                      xaxis2=dict(title='<b>Time to Recover (Months)<b>', title_font=dict(size=20)),
                      xaxis3=dict(title='<b>Time (Months)<b>', title_font=dict(size=20)),
                      xaxis4=dict(title='<b>Time (Months)<b>', title_font=dict(size=20)),
                      yaxis1=dict(title='<b>Recovery Probability<b>', title_font=dict(size=18)),
                      yaxis2_title='',
                      yaxis3=dict(title='<b>Recovery Probability<b>', title_font=dict(size=18)),
                      yaxis4=dict(title='<b>Recovery Probability<b>', title_font=dict(size=18)),
                      legend_tracegroupgap=tracegroupgap,
                      legend_font=dict(size=14),  # Increase the legends' font size
                      legend_x=-0.35)



    st.plotly_chart(fig)


st.markdown("""
    <h1 style='text-align: center;'>Visualization Final Project</h1>
    """, unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>Breast Cancer</h2>", unsafe_allow_html=True)
st.image(image)
build_heatmap()
build_two_y_axis_chart()
figure3()
