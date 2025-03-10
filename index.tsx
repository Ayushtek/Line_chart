import React, { useEffect, useState } from "react";
import LineChart from "@cloudscape-design/components/line-chart";
import Header from "@cloudscape-design/components/header";
import Select, { SelectProps } from "@cloudscape-design/components/select";
import { LineChartProps } from "@cloudscape-design/components";
import { fetchVoltageData, TimingData } from "./data";
import { commonChartProps } from "../chart-commons";
import { WidgetConfig, WidgetDataType } from "../interfaces";

const timeFilters: SelectProps.Option[] = [
  { label: "Last 2 Hours (All data points)", value: "2hr" },
  { label: "Last 1 Day (Avg every 5 min)", value: "1day" },
  { label: "Last 1 Week (Avg every 15 min)", value: "1week" },
  { label: "Last 1 Month (Avg every 1 hour)", value: "1month" },
  { label: "Last 3 Months (Avg every 1 hour)", value: "3month" },
];

const VoltageContent = () => {
  const [voltageDomain, setVoltageDomain] = useState<string[]>([]);
  const [voltageSeries, setVoltageSeries] = useState<LineChartProps<string>["series"]>([]);
  const [timing, setTiming] = useState<TimingData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedTimeFilter, setSelectedTimeFilter] = useState<SelectProps.Option>(timeFilters[0]);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const filterValue = selectedTimeFilter.value as string;
        const { voltageDomain, voltageSeries, timing } = await fetchVoltageData(filterValue);

        // Convert timestamps into formatted strings (for categorical X-axis)
        const formattedDomain = voltageDomain.map((timestamp: string) =>
          new Date(timestamp).toLocaleString([], { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
        );

        // Ensure each phase (R, Y, B, N) is mapped correctly
        const formattedSeries = voltageSeries.map(series => ({
          ...series,
          data: series.data.map((point: { x: string; y: number }) => ({
            x: new Date(point.x).toLocaleString([], { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }),
            y: point.y,
          })),
        }));

        setVoltageDomain(formattedDomain);
        setVoltageSeries(formattedSeries);
        setTiming(timing);
      } catch (error) {
        console.error("Error fetching voltage data:", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [selectedTimeFilter]);

  return (
    <div>
      {/* Time Filter Dropdown */}
      <div style={{ display: "flex", gap: "10px", marginBottom: "15px" }}>
        <Select
          selectedOption={selectedTimeFilter}
          onChange={({ detail }) => setSelectedTimeFilter(detail.selectedOption)}
          options={timeFilters}
        />
      </div>

      {/* Chart Rendering */}
      {loading ? (
        <p>Loading chart data...</p>
      ) : voltageSeries.length === 0 ? (
        <p>No data available</p>
      ) : (
        <LineChart
          {...commonChartProps}
          height={300}
          fitHeight
          xDomain={voltageDomain}
          xScaleType="categorical"  // Fixing X-Axis scaling issue
          series={voltageSeries}
          xTitle="Time"
          yTitle="Current (A)"
          ariaLabel="Current Over Time"
          ariaDescription="Line chart showing current fluctuations over time."
          xTickFormatter={(timestamp: string) => timestamp} // Formatting X-axis labels
          detailOverlay={true} // Enables drag-and-drop overlays
        />
      )}

      {/* Execution Timing Metrics */}
      {timing && (
        <div className="mt-4 p-4 bg-gray-100 rounded">
          <h2 className="font-semibold mb-2">Execution Timings (seconds):</h2>
          <p>Total API Time: {timing.total_time_seconds.toFixed(4)}s</p>
          <p>DB Connection Time: {timing.db_connection_seconds.toFixed(4)}s</p>
          <p>Query Execution Time: {timing.query_execution_seconds.toFixed(4)}s</p>
          <p>Data Processing Time: {timing.data_processing_seconds.toFixed(4)}s</p>
        </div>
      )}
    </div>
  );
};

const VoltageHeader = () => <Header>Current (R, Y, B, N Phase) - Transformer Bay 2</Header>;

export const voltageWidget1: WidgetConfig = {
  definition: { defaultRowSpan: 4, defaultColumnSpan: 2, minRowSpan: 3 },
  data: {
    icon: "lineChart",
    title: "Current Over Time",
    description: "Displays current readings (R, Y, B, N Phases) over time for Transformer Bay 2",
    header: VoltageHeader,
    content: VoltageContent,
    staticMinHeight: 660,
  } as WidgetDataType,
};
