import React, { useEffect, useState } from "react";
import LineChart from "@cloudscape-design/components/line-chart";
import Header from "@cloudscape-design/components/header";
import Select, { SelectProps } from "@cloudscape-design/components/select";
import { LineChartProps } from "@cloudscape-design/components";
import { fetchVoltageData } from "./data";
import { commonChartProps } from "../chart-commons";
import { WidgetConfig, WidgetDataType } from "../interfaces";

const timeFilters: SelectProps.Option[] = [
  { label: "Last 2 Hours (All data points)", value: "2hr" },
  { label: "Last 1 Day (Avg every 5 min)", value: "1day" },
  { label: "Last 1 Week (Avg every 15 min)", value: "1week" },
  { label: "Last 1 Month (Avg every 1 hour)", value: "1month" },
];

const VoltageContent = () => {
  const [voltageDomain, setVoltageDomain] = useState<Date[]>([]);
  const [voltageSeries, setVoltageSeries] = useState<LineChartProps<Date>["series"]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedTimeFilter, setSelectedTimeFilter] = useState<SelectProps.Option>(timeFilters[0]);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const { voltageDomain, voltageSeries } = await fetchVoltageData(selectedTimeFilter.value as string);
        setVoltageDomain(voltageDomain.map((date) => new Date(date)));
        setVoltageSeries(voltageSeries.map(series => ({
          ...series,
          data: series.data.map(point => ({ x: new Date(point.x), y: point.y }))
        })));
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
          xScaleType="categorical"
          series={voltageSeries}
          xTitle="Time"
          yTitle="Current (R Phase)"
          ariaLabel="Current Over Time"
          ariaDescription="Line chart showing current fluctuations over time."
          xTickFormatter={(date) => new Date(date).toLocaleTimeString([], {day:'2-digit', hour: "2-digit", minute: "2-digit" })}
        />
      )}
    </div>
  );
};

const VoltageHeader = () => <Header>Current (R Phase) - Transformer Bay 2</Header>;

export const voltageWidget: WidgetConfig = {
  definition: { defaultRowSpan: 4, defaultColumnSpan: 2, minRowSpan: 3 },
  data: {
    icon: "lineChart",
    title: "Current Over Time",
    description: "Displays current readings (R Phase) over time for Transformer Bay 2",
    header: VoltageHeader,
    content: VoltageContent,
    staticMinHeight: 660,
  } as WidgetDataType,
};