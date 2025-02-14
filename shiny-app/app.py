import shiny
from shiny import App, ui, render

import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import contextily as ctx
from matplotlib.colors import ListedColormap
from matplotlib import colors as mcolors
import os
import numpy as np

# Data Preparation
import geopandas as gpd
import pandas as pd

def prepare_data():
    # Load the GeoDataFrame
    data_path = "../data/ev_final_demo_merged.geojson"
    gdf = gpd.read_file(data_path)

    # Drop rows where 'num_pop' is NaN and where 'num_pop' is 0
    gdf = gdf.dropna(subset=['num_pop'])
    gdf = gdf[gdf['num_pop'] > 0]

    # Ensure all values in 'groups_with_access_code' are lowercase
    gdf['groups_with_access_code'] = gdf['groups_with_access_code'].str.lower()

    # Assign 'time_acess' = 1 if 'groups_with_access_code' contains '24 hours'
    gdf['time_acess'] = gdf['groups_with_access_code'].apply(lambda x: 1 if '24 hours' in x else 0)

    # Assign 'nonpublic_acess' = 1 if 'groups_with_access_code' contains 'required' or 'only'
    gdf['nonpublic_acess'] = gdf['groups_with_access_code'].apply(lambda x: 1 if 'required' in x or 'only' in x else 0)

    # Path to the full census tract shapefile
    census_tract_path = "/Volumes/Nancy/data/tl_2024_06_tract/tl_2024_06_tract.shp"

    # Load the shapefile
    tracts = gpd.read_file(census_tract_path)

    # Filter for LA County using the FIPS code ('037' for Los Angeles)
    la_tracts = tracts[tracts['COUNTYFP'] == '037']

    # Group by 'GeoID' and 'year', apply specific aggregation rules
    gdf = (
        gdf.groupby(['GeoID', 'year'])
        .agg(
            unique_station_count=('station_name', 'nunique'),
            num_pop=('num_pop', 'first'),
            num_pop_m=('num_pop_m', 'first'),
            num_pop_f=('num_pop_f', 'first'),
            num_pop_25_to_34=('num_pop_25_to_34', 'first'),
            num_pop_18=('num_pop_18', 'first'),
            num_pop_21=('num_pop_21', 'first'),
            num_pop_62=('num_pop_62', 'first'),
            mu_income=('mu_income', 'first'),
            geometry=('geometry', lambda x: list(x.unique())),  # Collect all unique geometry values as a list
            area=('area', 'first'),
            city=('city', lambda x: list(x.unique()) if x.nunique() > 1 else x.iloc[0]),
            ev_level1_evse_num=('ev_level1_evse_num', 'sum'),
            ev_level2_evse_num=('ev_level2_evse_num', 'sum'),
            ev_dc_fast_num=('ev_dc_fast_num', 'sum'),
            time_acess=('time_acess', 'sum'),
            nonpublic_acess=('nonpublic_acess', 'sum'),
        )
        .reset_index()
    )

    # Drop unnecessary columns directly in the grouped DataFrame
    columns_to_drop_group = ['zip', 'groups_with_access_code', 'access_days_time', 'status_code', 'street_address','geometry']
    gdf = gdf.drop(columns=columns_to_drop_group, errors='ignore')

    numeric_columns = ['ev_level1_evse_num','ev_level2_evse_num', 'ev_dc_fast_num', 
                   'time_acess','nonpublic_acess',
                   'unique_station_count']
    gdf[numeric_columns] = gdf[numeric_columns].fillna(0)

    # Calculate 'accessibility', handle cases where 'num_pop' is 0 or NA
    gdf['accessibility'] = gdf.apply(
        lambda row: (row['unique_station_count'] / row['num_pop']) * 1000 
        if pd.notna(row['num_pop']) and row['num_pop'] != 0 else np.nan,
        axis=1
    )

    # Define the percentile-based bins
    num_bins = 5
    percentile_labels = [
        "0-20% (Lowest)",
        "20-40%",
        "40-60%",
        "60-80%",
        "80-100% (Highest)"
    ]

    # Separate NA values and non-NA values for 'accessibility'
    na_mask = gdf['accessibility'].isna()

    # Calculate percentile bins for numeric (non-NA) values
    gdf.loc[~na_mask, 'accessibility_bins'] = pd.qcut(
        gdf.loc[~na_mask, 'accessibility'], 
        q=num_bins, 
        labels=percentile_labels
    )

    # Assign 'Depopulated Zone' label for NA values
    gdf['accessibility_bins'] = gdf['accessibility_bins'].astype('category')
    gdf['accessibility_bins'] = gdf['accessibility_bins'].cat.add_categories(['Depopulated Zone'])
    gdf.loc[na_mask, 'accessibility_bins'] = 'Depopulated Zone'

    # Final step: Optionally convert to string for uniformity (if needed for export)
    gdf['accessibility_bins'] = gdf['accessibility_bins'].astype('str')

    # Convert 'mu_income' to numeric
    gdf['mu_income'] = pd.to_numeric(gdf['mu_income'], errors='coerce')

    # Create a mask for NA values in 'mu_income'
    na_mask_income = gdf['mu_income'].isna()

    # Define bins for 'mu_income'
    num_bins_income = 5
    income_bins = pd.cut(
        gdf.loc[~na_mask_income, 'mu_income'],  # Only consider non-NA values
        bins=num_bins_income,
        precision=2
    )

    # Extract range categories for non-NA values
    bin_ranges = income_bins.cat.categories

    # Map bin ranges to descriptive labels
    bin_labels = ["Low", "Middle Low", "Middle", "Middle High", "High"]
    bin_mapping = {i: label for i, label in enumerate(bin_labels)}

    # Assign bin indices for non-NA values
    gdf.loc[~na_mask_income, 'mu_income_bins'] = pd.cut(
        gdf.loc[~na_mask_income, 'mu_income'], 
        bins=num_bins_income, 
        precision=2, 
        labels=range(num_bins_income)
    ).astype(float)

    # Assign bin range and label for non-NA values
    gdf.loc[~na_mask_income, 'mu_income_bins_range'] = pd.cut(
        gdf.loc[~na_mask_income, 'mu_income'], 
        bins=num_bins_income, 
        precision=2
    ).astype(str)

    gdf.loc[~na_mask_income, 'mu_income_bins_label'] = pd.cut(
        gdf.loc[~na_mask_income, 'mu_income'], 
        bins=num_bins_income, 
        precision=2, 
        labels=bin_labels
    ).astype(str)

    # Assign 'Depopulated Zone' to NA values
    gdf.loc[na_mask_income, 'mu_income_bins'] = np.nan
    gdf.loc[na_mask_income, 'mu_income_bins_range'] = 'Depopulated Zone'
    gdf.loc[na_mask_income, 'mu_income_bins_label'] = 'Depopulated Zone'

    # Convert 'mu_income_bins_label' to categorical type with specified order
    gdf['mu_income_bins_label'] = pd.Categorical(
        gdf['mu_income_bins_label'], 
        categories=bin_labels + ['Depopulated Zone'], 
        ordered=True
    )

    # Optionally convert ranges and labels to string for export
    gdf['mu_income_bins_range'] = gdf['mu_income_bins_range'].astype(str)
    gdf['mu_income_bins_label'] = gdf['mu_income_bins_label'].astype(str)


    # Aggregate data by year and bins
    income_bins_data = gdf.groupby(['year', 'mu_income_bins_label']).size().reset_index(name='count')

    # Filter the data to include only the years 2022, 2023, and 2024
    filtered_data = income_bins_data[income_bins_data['year'].isin([2022, 2023, 2024])]

    # Merge gdf data onto LA County tracts (keep all LA tracts)
    merged_gdf = la_tracts.merge(gdf, left_on='GEOID', right_on='GeoID', how='left')

    # Merge gdf data onto LA County tracts (keep all LA tracts)
    merged_gdf = la_tracts.merge(gdf, left_on='GEOID', right_on='GeoID', how='outer')

    merged_gdf = merged_gdf.set_geometry('geometry')
    merged_gdf["year"] = merged_gdf["year"].astype("Int64").dropna() 
    
    return merged_gdf


# Prepare data once at the start
merged_gdf = prepare_data()

# Clean and validate the 'year' column
merged_gdf = merged_gdf[merged_gdf["year"].notna()]  # Drop rows with NaN in 'year'
merged_gdf["year"] = merged_gdf["year"].astype(int)  # Convert 'year' to integers


# Generate dropdown choices as strings
year_choices = [str(year) for year in sorted(merged_gdf["year"].unique())]

# Accessibility colormap
reds_cmap = plt.cm.Reds
num_bins = 5
percentile_labels = [
    "0-20% (Lowest)",
    "20-40%",
    "40-60%",
    "60-80%",
    "80-100% (Highest)"
]
red_colors = [reds_cmap(i) for i in np.linspace(0.4, 1, num_bins)]  # Lighter to darker shades
accessibility_colors = dict(zip(percentile_labels, red_colors))
accessibility_colors["Depopulated Zone"] = "grey" 

# Extract unique cities for the dropdown
def extract_unique_cities(city_column):
    unique_cities = set()  # Use a set to avoid duplicates
    for value in city_column.dropna():  # Drop NA values
        if isinstance(value, list):  # If the value is a list
            unique_cities.update(value)  # Add all cities in the list to the set
        else:  # If it's a single city (not a list)
            unique_cities.add(value)
    return sorted(unique_cities)  # Return sorted list of unique cities

# Get unique cities
city_choices = ["All"] + extract_unique_cities(merged_gdf["city"])


page1 = ui.navset_card_underline(
    ui.nav_panel(
        "Maps",
        ui.layout_sidebar(
            ui.sidebar(
                # Dropdown for selecting year
                ui.input_select(
                    id="year",
                    label="Select Year:",
                    choices=year_choices,
                    selected="2024" if "2024" in year_choices else year_choices[0],
                ),
                # Multi-select dropdown for income bins
                ui.input_checkbox_group(
                    id="income_bins",
                    label="Select Income Bins:",
                    choices=["Low", "Middle Low", "Middle", "Middle High", "High"],
                    selected=["Low", "Middle Low", "Middle", "Middle High", "High"],  # Default all selected
                ),
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Summary Metrics", class_="text-center fw-bold fs-4"),  # Centered, bold, larger text
                    ui.layout_columns(
                        ui.card(
                            ui.card_header("Income Range($)", class_="text-center fw-bold"),  # Header aligned and bold
                            ui.div(
                                ui.output_text("income_range"), class_="small-card"   # Wrap in a div for alignment
                            ),
                        ),
                        ui.card(
                            ui.card_header("Accessibility Range", class_="text-center fw-bold"),
                            ui.div(
                                ui.output_text("accessibility_range"), class_="small-card" 
                            ),
                        ),
                        ui.card(
                            ui.card_header("Number of Census Tracts", class_="text-center fw-bold"),
                            ui.div(
                                ui.output_text("unique_geoids"), class_="small-card"  # Use a small card for this output
                            ),
                        ),
                        col_widths=(4, 4, 4),  # Each card takes 4 columns out of 12
                    ),
                    style="height: 300px;"  # Adjust height of Summary Metrics row
                ),
                col_widths=(12,),  # Metrics row occupies the full width
            ),
            ui.layout_columns(
                ui.card(
                    #ui.card_header("Income Levels", class_="text-center fw-bold fs-5"),
                    ui.output_plot("map_plot"),  # Map for Income Levels
                    full_screen=True,
                ),
                ui.card(
                    #ui.card_header("Accessibility", class_="text-center fw-bold fs-5"),
                    ui.output_plot("accessibility_map_plot"),  # Map for Accessibility
                    full_screen=True,
                ),
                col_widths=(6, 6),  # Maps occupy more space
                style="height: calc(100vh - 300px);"  # Dynamic height adjustment
            ),
        ),
    ),
    title="Income and EV Charger Accessibility",
)

page2 = ui.navset_card_underline(
    ui.nav_panel(
        "City-Year Analysis",
        ui.layout_sidebar(
            ui.sidebar(
                # Dropdown for selecting city
                ui.input_select(
                    id="city",
                    label="Select City:",
                    choices=city_choices,
                    selected="Rancho Palos Verdes",  # Default to All cities
                ),
                # Dropdown for selecting year
                ui.input_select(
                    id="year_page2",
                    label="Select Year:",
                    choices=year_choices,
                    selected="2024",
                ),
            ),
            ui.layout_columns(
                ui.card(
                    ui.card_header("Summary Metrics", class_="text-center fw-bold fs-4"),
                    ui.layout_columns(
                        ui.card(
                            ui.card_header("Income Range($)", class_="text-center fw-bold"),
                            ui.div(ui.output_text("income_range_city"), class_="small-card"),
                        ),
                        ui.card(
                            ui.card_header("Accessibility Range", class_="text-center fw-bold"),
                            ui.div(ui.output_text("accessibility_range_city"), class_="small-card"),
                        ),
                        ui.card(
                            ui.card_header("Number of Census Tracts", class_="text-center fw-bold"),
                            ui.div(ui.output_text("unique_geoids_city"), class_="small-card"),
                        ),
                        col_widths=(4, 4, 4),
                    ),
                    style="height: 300px;",
                ),
                col_widths=(12,),
            ),
            ui.layout_columns(
                ui.card(
                    ui.output_plot("city_income_map"),
                    full_screen=True,
                ),
                ui.card(
                    ui.output_plot("city_accessibility_map"),
                    full_screen=True,
                ),
                col_widths=(6, 6),
                style="height: calc(100vh - 300px);",
            ),
        ),
    ),
    title="City Level Analysis of Income and Accessibility",
)


# Main UI: Include all pages in the navbar
app_ui = ui.page_fillable(
    ui.head_content(
        ui.tags.style("""
            /* 确保整体页面填充整个网页 */
            html, body, .container-fluid {
                height: 100%; /* 填满视口高度 */
                margin: 0; /* 去除外边距 */
                padding: 0; /* 去除内边距 */
                display: flex; /* 使用弹性布局 */
                flex-direction: column; /* 垂直排列 */
            }

            /* 导航栏样式 */
            .navbar {
                flex: 0 0 auto; /* 固定导航栏高度 */
                display: flex;
                justify-content: space-between; /* 左右两端对齐 */
                align-items: center; /* 垂直居中 */
            }

            /* 主页面内容布局 */
            .page-content {
                flex: 1; /* 填充剩余高度 */
                display: flex;
                flex-direction: column;
            }

            /* 卡片样式 */
            .card {
                background-color: #D8E7EA; /* 背景颜色 */
                border: none; /* 边框 */
                border-radius: 8px; /* 圆角 */
                box-shadow: none; /* 阴影效果 */
                display: flex; /* 弹性布局 */
                height: calc(100vh - 20px); /* 调整高度为页面视口高度，减去顶部和底部的 20px */
                flex-direction: column; /* 垂直排列内容 */
                flex-grow: 1; /* 自动调整高度 */
                margin: 10px; /* 卡片之间的间距 */
            }

            /* 小卡片样式 */
            .small-card {
                background-color: white; /* 小卡片背景颜色 */
                border: 1px solid #cccccc; /* 边框 */
                border-radius: 8px; /* 圆角 */
                box-shadow: none; /* 阴影效果 */
                padding: 15px; /* 内边距 */
                text-align: center; /* 文本居中 */
                flex-grow: 1; /* 自动填充父容器高度 */
            }
            .navbar-brand {
                font-size: 38px; /* 调整字体大小 */
                color: "#4884F7"; /* 调整字体颜色（蓝色） */
                font-weight: bold; /* 设置加粗 */
            }
        """)
    ),
    ui.page_navbar(
        ui.nav_panel("Page 1", page1),
        ui.nav_panel("Page 2", page2),
        title="EV Charger Accessibility Analysis"
    )
)

# Server logic
def server(input, output, session):
    @output
    @render.text
    def income_range():
        # Get selected income bins
        selected_bins = input.income_bins()
        if not selected_bins:
            return "No Income Bins Selected"
        
        # Get range of selected bins
        bin_ranges = merged_gdf.loc[
            merged_gdf["mu_income_bins_label"].isin(selected_bins), "mu_income_bins_range"
        ].dropna().unique()

        # Parse and find min and max from the ranges
        numeric_ranges = []
        for r in bin_ranges:
            # Extract numeric values from range strings (e.g., '(6613.21, 100437.2]')
            if isinstance(r, str) and ("," in r):
                try:
                    low, high = r.strip("()[]").split(",")
                    numeric_ranges.append((float(low), float(high)))
                except ValueError:
                    continue  # Skip invalid ranges
        
        if numeric_ranges:
            min_value = min(r[0] for r in numeric_ranges)  # Find the smallest lower bound
            max_value = max(r[1] for r in numeric_ranges)  # Find the largest upper bound
            return f"({min_value}, {max_value}]"
        else:
            return "No Valid Ranges"


    @output
    @render.text
    def accessibility_range():
        # Filter data by year and selected bins
        filtered_gdf = merged_gdf[
            (merged_gdf["year"] == int(input.year())) &
            (merged_gdf["mu_income_bins_label"].isin(input.income_bins()))
        ]

        # Get accessibility range
        if filtered_gdf.empty:
            return "No Data"

        # Extract unique accessibility values
        accessibility_values = filtered_gdf["accessibility_bins"].unique()

        # Process to find range
        min_val = None
        max_val = None
        for label in accessibility_values:
            if isinstance(label, str):
                # Extract numeric parts before and after the '-' separator
                parts = label.split("-")
                try:
                    start = int("".join(filter(str.isdigit, parts[0])))  # Extract numbers from the first part
                    end = int("".join(filter(str.isdigit, parts[1])))    # Extract numbers from the second part
                except (IndexError, ValueError):
                    continue  # Skip invalid ranges

                if min_val is None or start < min_val:
                    min_val = start
                if max_val is None or end > max_val:
                    max_val = end

        if min_val is not None and max_val is not None:
            return f"{min_val}-{max_val}%"
        else:
            return "No Valid Range"

    @output
    @render.text
    def unique_geoids():
        # Filter data by year and selected bins
        filtered_gdf = merged_gdf[
            (merged_gdf["year"] == int(input.year())) &
            (merged_gdf["mu_income_bins_label"].isin(input.income_bins()))
        ]
        # Count unique GeoIDs
        unique_count = filtered_gdf["GeoID"].nunique()
        return str(unique_count)

    @output
    @render.plot
    def map_plot():
        # Filter the data by year and selected bins
        filtered_gdf = merged_gdf[
            (merged_gdf["year"] == int(input.year())) &
            (merged_gdf["mu_income_bins_label"].isin(input.income_bins()))
        ].to_crs(epsg=3857)

        # Define custom colors for income bins
        custom_colors = {
            "Depopulated Zone": "white",  # white
            "Low": "#9ACBEA",  # blue
            "Middle Low": "#CFE8F5",  # lightblue
            "Middle": "#FFC1C1",  # lightred
            "Middle High": "#F6C3C2",  # red
            "High": "#E34234"  # dark red
        }
        # Ensure categories of 'mu_income_bins_label' match the order of custom_colors
        merged_gdf['mu_income_bins_label'] = merged_gdf['mu_income_bins_label'].astype('category')
        merged_gdf['mu_income_bins_label'] = merged_gdf['mu_income_bins_label'].cat.set_categories(
            list(custom_colors.keys()), ordered=True
        )
        # Map the categorical values to the correct order and colors
        cmap = ListedColormap([custom_colors[label] for label in custom_colors.keys()])
        norm = mcolors.BoundaryNorm(
            boundaries=range(len(custom_colors) + 1),
            ncolors=len(custom_colors)
        )
        # Plot the map with the specified colormap
        fig, ax = plt.subplots(figsize=(10, 8))

        # Set the figure's background transparency
        fig.patch.set_alpha(0)

        filtered_gdf.plot(
            column="mu_income_bins_label",  # Column to visualize
            cmap=cmap,  # Apply custom colormap
            linewidth=0.5,  # Boundary line width
            edgecolor="white",  # Boundary color
            legend=True,  # Enable legend
            ax=ax,
        )

        # Add basemap
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.Voyager)
        # Set the map background to transparent
        ax.set_facecolor('none')
        # Add a custom legend title manually
        legend = ax.get_legend()
        if legend:
            legend.set_bbox_to_anchor((1.5, 0.5))  # right
            legend.set_frame_on(False)  # frame
            legend.set_title("Income Bins")

        ax.set_title(f"Income Levels ({input.year()})", fontsize=16)
        ax.axis("off")
        return fig

    @output
    @render.plot
    def accessibility_map_plot():
        accessibility_colors = {
            "Depopulated Zone": "#cccccc",  # grey for Depopulated Zone
            "0-20% (Lowest)": "#9ACBEA",  # blue
            "20-40%": "#CFE8F5",  # lightblue
            "40-60%": "#FFC1C1",  # lightred
            "60-80%": "#F6C3C2",  # red
            "80-100% (Highest)": "#E34234"  # dark red
        }
        # Filter the data by year and selected bins
        filtered_gdf = merged_gdf[
            (merged_gdf["year"] == int(input.year())) &
            (merged_gdf["mu_income_bins_label"].isin(input.income_bins()))
        ].to_crs(epsg=3857)

        # Ensure categories of 'mu_income_bins_label' match the order of custom_colors
        merged_gdf['accessibility_bins'] = merged_gdf['accessibility_bins'].astype('category')
        merged_gdf['accessibility_bins'] = merged_gdf['accessibility_bins'].cat.set_categories(
            list(accessibility_colors.keys()), ordered=True
        )
        
        # Create a colormap for accessibility bins
        cmap = ListedColormap([accessibility_colors[label] for label in accessibility_colors])

        # Plot the accessibility map
        fig, ax = plt.subplots(figsize=(10, 8))
        # Set the figure's background transparency
        fig.patch.set_alpha(0)
        filtered_gdf.plot(
            column="accessibility_bins",  # Column for visualization
            cmap=cmap,  # Use the custom colormap
            linewidth=0.2,  # Boundary line width
            edgecolor="white",  # Boundary color
            legend=True,  # Enable legend
            ax=ax,
        )

        # Add a basemap (OpenStreetMap)
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.Voyager)
        # Set the map background to transparent
        ax.set_facecolor('none')
        # Add a custom legend title manually
        legend = ax.get_legend()
        if legend:
            legend.set_bbox_to_anchor((1.5, 0.5))  # right
            legend.set_frame_on(False)  # frame
            legend.set_title("Accessibility Percentile")
        
        # Finalize the plot
        ax.set_title(f"Accessibility ({input.year()})", fontsize=16)
        ax.axis("off")
        return fig

    @output
    @render.text
    def income_range_city():
        # Get selected city and year
        selected_city = input.city()
        selected_year = int(input.year_page2())

        # Filter rows where the selected city is in the list or single value
        if selected_city != "All":
            filtered_gdf = merged_gdf[
                merged_gdf["city"].apply(
                    lambda cities: selected_city in cities if isinstance(cities, list) else selected_city == cities
                ) &
                (merged_gdf["year"] == selected_year)
            ]
        else:
            filtered_gdf = merged_gdf[merged_gdf["year"] == selected_year]

        # Check if filtered data is empty
        if filtered_gdf.empty:
            return "No Data"

        # Extract income ranges
        income_ranges = filtered_gdf["mu_income_bins_range"].dropna().unique()

        # Parse and find min and max from the ranges
        min_value = None
        max_value = None
        for income_range in income_ranges:
            if isinstance(income_range, str) and ("," in income_range):
                try:
                    # Extract numeric values from range strings (e.g., "(1000, 2000]")
                    low, high = income_range.strip("()[]").split(",")
                    low = float(low.strip())
                    high = float(high.strip())
                    # Update min and max values
                    if min_value is None or low < min_value:
                        min_value = low
                    if max_value is None or high > max_value:
                        max_value = high
                except ValueError:
                    continue  # Skip invalid ranges

        # Return the income range as a formatted string
        if min_value is not None and max_value is not None:
            return f"(${min_value:,.2f}, ${max_value:,.2f})"
        else:
            return "No Valid Range"


    @output
    @render.text
    def accessibility_range_city():
        # Get selected city and year
        selected_city = input.city()
        selected_year = int(input.year_page2())

        # Filter rows where the selected city is in the list or single value
        if selected_city != "All":
            filtered_gdf = merged_gdf[
                merged_gdf["city"].apply(
                    lambda cities: selected_city in cities if isinstance(cities, list) else selected_city == cities
                ) &
                (merged_gdf["year"] == selected_year)
            ]
        else:
            filtered_gdf = merged_gdf[merged_gdf["year"] == selected_year]

        # Check if filtered data is empty
        if filtered_gdf.empty:
            return "No Data"

        # Extract unique accessibility values
        accessibility_values = filtered_gdf["accessibility_bins"].unique()

        # Process to find the minimum and maximum range
        min_val = None
        max_val = None
        for label in accessibility_values:
            if isinstance(label, str):  # Ensure the label is a string
                parts = label.split("-")  # Split the range string
                try:
                    start = int("".join(filter(str.isdigit, parts[0])))  # Extract the start value
                    end = int("".join(filter(str.isdigit, parts[1])))    # Extract the end value
                except (IndexError, ValueError):
                    continue  # Skip invalid ranges

                # Update min and max values
                if min_val is None or start < min_val:
                    min_val = start
                if max_val is None or end > max_val:
                    max_val = end

        # Return the range as a formatted string
        if min_val is not None and max_val is not None:
            return f"{min_val}-{max_val}%"
        else:
            return "No Valid Range"



    @output
    @render.text
    def unique_geoids_city():
        # Debug: Print the 'city' column and its types
        print(merged_gdf["city"].head())
        print(merged_gdf["city"].apply(type).unique())

        # Filter by selected city and year
        selected_city = input.city()
        selected_year = int(input.year_page2())

        # Filter rows where the selected city is in the list or single value
        if selected_city != "All":
            filtered_gdf = merged_gdf[
                merged_gdf["city"].apply(
                    lambda cities: selected_city in cities if isinstance(cities, list) else selected_city == cities
                ) &
                (merged_gdf["year"] == selected_year)
            ]
        else:
            filtered_gdf = merged_gdf[merged_gdf["year"] == selected_year]

        # Count unique GeoIDs
        unique_count = filtered_gdf["GeoID"].nunique()
        return str(unique_count)


    @output
    @render.plot
    def city_income_map():
        # Filter by selected city and year
        selected_city = input.city()
        selected_year = int(input.year_page2())

        # Filter rows where the selected city is in the list or single value
        if selected_city != "All":
            filtered_gdf = merged_gdf[
                merged_gdf["city"].apply(
                    lambda cities: selected_city in cities if isinstance(cities, list) else selected_city == cities
                ) &
                (merged_gdf["year"] == selected_year)
            ]
        else:
            filtered_gdf = merged_gdf[merged_gdf["year"] == selected_year]

        # Check if filtered data is empty
        if filtered_gdf.empty:
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.text(0.5, 0.5, "No data available for selected city and year.", 
                    ha="center", va="center", transform=ax.transAxes, fontsize=12)
            ax.set_axis_off()
            return fig

        # Define custom colors for income bins
        custom_colors = {
            "Depopulated Zone": "white",  # White
            "Low": "#9ACBEA",  # Blue
            "Middle Low": "#CFE8F5",  # Light blue
            "Middle": "#FFC1C1",  # Light red
            "Middle High": "#F6C3C2",  # Red
            "High": "#E34234"  # Dark red
        }

        # Create a colormap for income bins
        cmap = ListedColormap([custom_colors[label] for label in custom_colors.keys()])

        # Ensure categories match the custom color order
        filtered_gdf = filtered_gdf.copy()  # Avoid SettingWithCopyWarning
        filtered_gdf['mu_income_bins_label'] = filtered_gdf['mu_income_bins_label'].astype('category')
        filtered_gdf['mu_income_bins_label'] = filtered_gdf['mu_income_bins_label'].cat.set_categories(
            list(custom_colors.keys()), ordered=True
        )

        # Reproject to EPSG:3857 for basemap compatibility
        filtered_gdf = filtered_gdf.to_crs(epsg=3857)

        # Plot the map
        fig, ax = plt.subplots(figsize=(10, 8))
        filtered_gdf.plot(
            column="mu_income_bins_label",  # Column to visualize
            cmap=cmap,  # Apply custom colormap
            linewidth=0.5,  # Boundary line width
            edgecolor="white",  # Boundary color
            legend=True,  # Enable legend
            ax=ax,
        )

        # Add basemap
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.Voyager)
        # Set the figure's background transparency
        fig.patch.set_alpha(0)
        # Customize the map
        ax.set_facecolor('none')  # Set map background to transparent
        legend = ax.get_legend()
        if legend:
            legend.set_bbox_to_anchor((1.5, 0.5))  # Adjust legend position
            legend.set_frame_on(False)  # Remove legend frame
            legend.set_title("Income Bins")

        # Finalize the plot
        ax.set_title(f"Income Levels ({selected_city}, {selected_year})", fontsize=16)
        ax.axis("off")
        return fig


    @output
    @render.plot
    def city_accessibility_map():
        # Filter by selected city and year
        selected_city = input.city()
        selected_year = int(input.year_page2())
        
        # Filter rows where the selected city is in the list or single value
        if selected_city != "All":
            filtered_gdf = merged_gdf[
                merged_gdf["city"].apply(
                    lambda cities: selected_city in cities if isinstance(cities, list) else selected_city == cities
                ) &
                (merged_gdf["year"] == selected_year)
            ]
        else:
            filtered_gdf = merged_gdf[merged_gdf["year"] == selected_year]

        # Check if filtered data is empty
        if filtered_gdf.empty:
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.text(0.5, 0.5, "No data available for selected city and year.", 
                    ha="center", va="center", transform=ax.transAxes, fontsize=12)
            ax.set_axis_off()
            return fig

        # Define accessibility colors
        accessibility_colors = {
            "Depopulated Zone": "#cccccc",  # Grey for Depopulated Zone
            "0-20% (Lowest)": "#9ACBEA",  # Blue
            "20-40%": "#CFE8F5",  # Light blue
            "40-60%": "#FFC1C1",  # Light red
            "60-80%": "#F6C3C2",  # Red
            "80-100% (Highest)": "#E34234"  # Dark red
        }

        # Create colormap for accessibility bins
        cmap = ListedColormap([accessibility_colors[label] for label in accessibility_colors])

        # Ensure categories of 'accessibility_bins' match the order of colors
        filtered_gdf = filtered_gdf.copy()  # Avoid SettingWithCopyWarning
        filtered_gdf['accessibility_bins'] = filtered_gdf['accessibility_bins'].astype('category')
        filtered_gdf['accessibility_bins'] = filtered_gdf['accessibility_bins'].cat.set_categories(
            list(accessibility_colors.keys()), ordered=True
        )

        # Reproject to EPSG:3857 for basemap compatibility
        filtered_gdf = filtered_gdf.to_crs(epsg=3857)

        # Plot the accessibility map
        fig, ax = plt.subplots(figsize=(10, 8))
        filtered_gdf.plot(
            column="accessibility_bins",  # Column for visualization
            cmap=cmap,  # Use the custom colormap
            linewidth=0.2,  # Boundary line width
            edgecolor="white",  # Boundary color
            legend=True,  # Enable legend
            ax=ax,
        )
        # Set the figure's background transparency
        fig.patch.set_alpha(0)
        # Add a basemap
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.Voyager)
        # Customize the map
        ax.set_facecolor('none')  # Set the map background to transparent
        legend = ax.get_legend()
        if legend:
            legend.set_bbox_to_anchor((1.5, 0.5))  # Adjust legend position
            legend.set_frame_on(False)  # Remove legend frame
            legend.set_title("Accessibility Percentile")

        # Finalize the plot
        ax.set_title(f"Accessibility ({selected_city}, {selected_year})", fontsize=16)
        ax.axis("off")
        return fig



# Create the app
app = App(app_ui, server)
