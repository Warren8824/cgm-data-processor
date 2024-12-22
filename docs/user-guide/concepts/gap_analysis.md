# Understanding CGM Data Gaps

Continuous Glucose Monitoring (CGM) data often contains gaps - periods where glucose readings are missing. Understanding these gaps is crucial for:
- Assessing data quality
- Ensuring accurate analysis
- Identifying potential device issues
- Making informed decisions about data processing

## What is a Gap?

In CGM data, a gap occurs when one or more expected glucose readings are missing. Since our data is aligned to 5-minute intervals, a gap can be:
- A single missing reading (5 minutes)
- Multiple consecutive missing readings
- Longer periods without data (sensor removal, device issues, etc.)

## Types of Gaps

### 1. Short Gaps (≤20 minutes)
- Can be interpolated automatically
- Usually don't significantly impact analysis
- Often caused by temporary sensor issues
- Filled using linear interpolation

### 2. Long Gaps (>20 minutes)
- Cannot be reliably interpolated
- May indicate significant events:
  * Sensor changes
  * Device malfunctions
  * Sensor removal
- Remain as missing values in the final dataset

## Gap Analysis Metrics

Our gap analysis provides comprehensive metrics to understand data quality:

### Basic Metrics
- **Initial Missing Count**: Total number of missing readings before processing
- **Initial Missing Percentage**: Proportion of missing data in the raw dataset
- **Remaining Missing Count**: Gaps that couldn't be interpolated
- **Remaining Missing Percentage**: Final proportion of missing data

### Gap Statistics
- **Total Gap Duration**: Combined length of all gaps in minutes
- **Average Gap Duration**: Mean length of gaps
- **Median Gap Duration**: Middle value of gap lengths
- **Gap Distribution**: Range from shortest to longest gaps
  * 25th percentile (Q1)
  * 75th percentile (Q3)
  * Standard deviation
  * Minimum and maximum gaps

## Visual Analysis

The gap dashboard provides several visualizations:

### 1. Gauge Indicators
- Show initial and remaining gap counts
- Display missing data percentages
- Provide quick visual assessment of data quality

### 2. Top 10 Largest Gaps
- Bar chart showing the longest gaps
- Helps identify major data collection issues
- Includes timing and duration information

### 3. Gap Distribution
- Scatter plot of all gaps
- Shows patterns in data collection
- Helps identify systematic issues

### 4. Comprehensive Statistics Table
- Detailed numerical metrics
- Complete statistical overview
- Useful for documentation and reporting

## Example Usage

```python
from analysis.gap_analysis import analyse_glucose_gaps
from visualization.gap_dashboard import create_gap_dashboard

# Analyze gaps in your processed data
gaps_data = analyse_glucose_gaps(aligned_df)

# Create visualization dashboard
dashboard = create_gap_dashboard(
    gaps_data,
    save_path="gaps_dashboard.png",
    width=1000,
    height=1900
)
```

## Example Gap Analysis Data

```markdown
{'initial_missing_count': 6575,
 'initial_missing_percentage': np.float64(4.73),
 'total_readings': 138979,
 'remaining_missing_count': np.int64(792),
 'remaining_missing_percentage': np.float64(0.57),
 'total_gap_minutes': np.float64(3960.0),
 'average_gap_minutes': np.float64(208.42),
 'median_gap_minutes': np.float64(40.0),
 'largest_gaps':             start_time            end_time  length_minutes duration
 5  2023-12-20 14:50:00 2023-12-22 07:05:00          2415.0  40h 15m
 1  2023-07-29 17:50:00 2023-07-30 04:45:00           655.0  10h 55m
 18 2024-07-27 06:15:00 2024-07-27 10:25:00           250.0   4h 10m
 15 2024-05-25 13:40:00 2024-05-25 15:35:00           115.0   1h 55m
 2  2023-08-23 16:35:00 2023-08-23 17:35:00            60.0    1h 0m
 9  2024-04-06 15:25:00 2024-04-06 16:15:00            50.0   0h 50m
 7  2024-02-20 15:25:00 2024-02-20 16:10:00            45.0   0h 45m
 3  2023-09-19 06:35:00 2023-09-19 07:20:00            45.0   0h 45m
 16 2024-07-12 00:45:00 2024-07-12 01:25:00            40.0   0h 40m
 13 2024-05-01 01:55:00 2024-05-01 02:35:00            40.0   0h 40m,
 'gaps_df':             start_time            end_time  length_minutes
 0  2023-06-08 16:50:00 2023-06-08 17:15:00            25.0
 1  2023-07-29 17:50:00 2023-07-30 04:45:00           655.0
 2  2023-08-23 16:35:00 2023-08-23 17:35:00            60.0
 3  2023-09-19 06:35:00 2023-09-19 07:20:00            45.0
 4  2023-12-15 15:35:00 2023-12-15 16:00:00            25.0
 5  2023-12-20 14:50:00 2023-12-22 07:05:00          2415.0
 6  2024-02-19 02:50:00 2024-02-19 03:15:00            25.0
 7  2024-02-20 15:25:00 2024-02-20 16:10:00            45.0
 8  2024-04-04 02:00:00 2024-04-04 02:25:00            25.0
 9  2024-04-06 15:25:00 2024-04-06 16:15:00            50.0
 10 2024-04-13 12:25:00 2024-04-13 13:00:00            35.0
 11 2024-04-14 14:15:00 2024-04-14 14:45:00            30.0
 12 2024-04-17 01:55:00 2024-04-17 02:25:00            30.0
 13 2024-05-01 01:55:00 2024-05-01 02:35:00            40.0
 14 2024-05-16 01:15:00 2024-05-16 01:40:00            25.0
 15 2024-05-25 13:40:00 2024-05-25 15:35:00           115.0
 16 2024-07-12 00:45:00 2024-07-12 01:25:00            40.0
 17 2024-07-23 15:00:00 2024-07-23 15:25:00            25.0
 18 2024-07-27 06:15:00 2024-07-27 10:25:00           250.0}
```
## Example Gap Analysis Dashboard
![gap_analysis_dashboard](../tutorials/load_and_export_data_files/load_and_export_data_17_1.png)
## Interpreting Results

### Good Data Quality Indicators
- Low initial missing percentage (<5%)
- Few long gaps (>20 minutes)
- Consistent gap distribution
- No regular patterns in gap timing

### Potential Issues to Watch For
1. **Regular Gap Patterns**
   - May indicate systematic problems
   - Could be related to daily activities

2. **Increasing Gap Frequency**
   - Might suggest sensor degradation
   - Could indicate calibration issues

3. **Clustered Gaps**
   - May correspond to specific activities
   - Could indicate device interference

4. **Long Gaps**
   - Check for sensor changes
   - Review device settings
   - Consider user activities

## Impact on Analysis

Understanding gaps is crucial for:

1. **Data Quality Assessment**
   - Determine if dataset is suitable for analysis
   - Identify periods that may need special handling

2. **Processing Decisions**
   - Choose appropriate interpolation settings
   - Decide whether to exclude certain periods

3. **Result Interpretation**
   - Account for missing data in conclusions
   - Understand limitations of analysis

4. **Device Management**
   - Identify potential sensor issues
   - Optimize sensor usage and replacement timing

## Best Practices

1. **Regular Monitoring**
   - Run gap analysis periodically
   - Track changes in gap patterns
   - Document significant gaps

2. **Documentation**
   - Note sensor changes
   - Record known device issues
   - Track user activities that may affect readings

3. **Analysis Adjustment**
   - Consider gap impact on results
   - Use appropriate statistical methods
   - Document data quality in reports

4. **Quality Improvement**
   - Use insights to improve data collection
   - Optimize device settings
   - Adjust user practices if needed