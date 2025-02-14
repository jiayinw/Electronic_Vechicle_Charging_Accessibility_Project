# Electronic_Vechicle_Charging_Accessibility_Project
An exploration on Electronic Vechicle Charging Station Accessibility in LA County

**Research Topic and questions**

California’s push for electric vehicles (EVs) aims to reduce greenhouse gas emissions, but disparities in EV charger distribution raise concerns about equitable access.
This project addresses three key questions:How has EV charger availability changed over time across regions in Los Angeles County? How does accessibility vary by income groups and geographic areas? What policies can address these disparities to promote equitable EV infrastructure development?


**Approach and Methodology**

We use 4 datasets:1.EV charger dataset (2017~2024); 2.Income census data (2017~2024); 3.Population census data (2017~2024); 4.Census Tract datasets of LA county

First, we clean Population and Income Census Data (2017~2024) in LA county: (1)Automatically select columns in need; (2)Clean columns' names; (3)Merge population and income datasets in each year together as a demographic datasets. Second, we clean EV charger datasets in LA county:(1)Narrow down from CA to LA county; (2)Select columns in need; (3)Clean values' format; (4)Merge each year dataset together. Third, we merge census tract dataset with EV Charger datasets as one geojson file. Fourth, we merge all datasets together.

To account for population differences across regions, we introduced a crucial metric: 
Accessibility = the number of EV chargers in a region / Total population in that region, 
which normalized per 1,000 residents. This adjustment allowed us to compare regions on a more equitable basis, highlighting disparities in per capita access to charging stations.

Our analysis included yearly trend (line chart), spatial density maps, and accessibility comparisons by income groups (map and shiny app). Visuals were created to demonstrate how charger availability has evolved and to highlight inequities across Los Angeles County.


**Key Findings**

EV Charger Availability Over Time:

- Plot 1: Number of EV Charging Stations (2017-2024)
We observed a significant increase in the number of EV charging Stations in Los Angeles County from 2017 to 2024. This growth was particularly pronounced between 2017 and 2021, with a slight dip in 2022 likely attributed to the pandemic and economic slowdown, and charger deployment resumed post-2022. 
- Plot 2: Spatial Map of EV Charging Stations (2017-2024)
Spatial density maps for 2017, 2020, and 2024 revealed that areas with previously low charger density experienced significant increases. Regions that initially had only one or two chargers now show three to five stations or more, indicating broader coverage. 
Accessibility and Income
- Plot 3&4: Accessibility in 2024
Accessibility, measured as chargers per 1,000 residents, varied significantly across Los Angeles County. Central urban areas and coastal regions exhibited the highest accessibility, while peripheral and low-income regions were underserved. This disparity suggests that wealthier and densely populated areas benefit disproportionately from EV infrastructure investments.
- Plot 7: Bar Chart on Income Accessibility 
- Plot 8: Income Bins Distribution (2022-2024)
- Plot 9: Income Level Trend Map by Year (2022~2024)
- Plot 10: Income Level Distribution Map in 2024
Income analysis further underscored this inequity. A positive correlation emerged between income levels and accessibility, with higher-income areas consistently enjoying greater per capita access to chargers. Some middle-income regions also demonstrated relatively high accessibility due to higher population densities driving demand for public chargers.

Other Graphs:

Plot 5 & 6: Percentage of 25-34 Age Group in Total Population (Overall & 2024)
We also analyzed the relationship between the percentage of the 25-34 age group in the population and EV charger accessibility. While there appeared to be a slight correlation—regions with a higher proportion of young adults seemed to have better accessibility—the relationship was not particularly strong or consistent. Given the lack of salient findings, we decided not to include these results in the final presentation. This highlights the need for further exploration and potentially controlling for additional factors to better understand the dynamics between demographic composition and EV charger accessibility.


**Shiny App Features Showcase**

The first page allows users to select a year by clicking on the box and income bins using drop-down menus, while displaying summary statistics for the income data, and accessibility metrics for the chosen year. The second page lets users select a specific city with the drop-down menu to view its accessibility and income details, highlighting the positive correlation between income and EV charger accessibility.


**Challenges and Limitations**

Data Cleaning: Merging large datasets with over 200 variables required significant effort to standardize formats, remove irrelevant columns, and address redundancy.
Accessibility Metric Bias: Our accessibility calculations occasionally overestimated values in sparsely populated areas, inflating accessibility metrics. To mitigate this, we focused on densely populated regions in our visualizations while acknowledging this bias.
Mapping Visualizations: Early maps lacked consistency due to missing data for regions without chargers. Assigning a distinct color to these regions improved clarity but required careful interpretation to avoid drawing misleading conclusions.
Preliminary Nature of Findings: The results represent preliminary relationships or correlations rather than causal conclusions. Due to the absence of experimental design and covariant controls, we could not establish causality.


**Policy Implications**

Our findings highlight persistent disparities in EV charger accessibility that demand targeted policy interventions. Recommendations include:
- Targeted Investments in Low-Income Areas:
- Prioritize charger deployment in underserved regions through subsidies or incentives for both public and private installations.
- Partner with community organizations to identify high-impact locations for new chargers.
- Equity-Focused Infrastructure Planning
- Incorporate demographic and geographic data into planning efforts to ensure that charger deployment reduces inequalities rather than exacerbates them.
- Establish benchmarks for accessibility across income groups and monitor progress regularly.
- Private Sector Collaboration
- Encourage partnerships with businesses to accelerate charger installation in low-accessibility areas, offering tax incentives or grants to support deployment.


**Future Directions**

Our study provides a foundation for understanding disparities in EV infrastructure, but additional research can deepen these insights:
Expanding Variables: Future studies could include factors like education level, racial demographics, and vehicle ownership rates to examine their influence on accessibility.
Regression Analysis: Conducting rigorous statistical tests would strengthen causal inferences, accounting for confounding variables and covariates.
Broader Geographic Scope: Expanding the analysis beyond Los Angeles County to other regions or states could provide a more comprehensive view of EV infrastructure inequities.
Longitudinal Policy Impact: Tracking the effects of targeted investments over time would help assess the effectiveness of equity-focused strategies.


**Conclusion**

The growth of EV infrastructure in Los Angeles County demonstrates progress toward California’s ambitious climate goals. However, the disparities in accessibility across income groups and geographic areas highlight the need for more equitable planning and investment. Policymakers must address these inequities to ensure that the transition to EVs benefits all communities, particularly those historically underserved.
