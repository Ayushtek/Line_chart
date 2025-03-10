import { LineChartProps } from "@cloudscape-design/components/line-chart";

/**
 * Fetch voltage data with filters applied.
 * @param filter - Time range filter ("2hr", "1day", "1week", "1month")
 */
export async function fetchVoltageData(filter: string) {
  try {
    const response = await fetch(
      `http://127.0.0.1:8200/analytics/get_voltage_data?filter=${filter}`
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch JSON: ${response.statusText}`);
    }

    const jsonData = await response.json();

    if (!jsonData || !Array.isArray(jsonData) || jsonData.length === 0) {
      console.warn("No data received for the selected filter.");
      return { voltageDomain: [], voltageSeries: [] };
    }

    return {
      voltageDomain: jsonData.map((item) => new Date(item.deviceTimestamp)),
      voltageSeries: [
        {
          title: "Current (R Phase) - Transformer Bay 2",
          type: "line" as const,
          data: jsonData
            .filter((item) => item.R !== null) // Ignore null values
            .map((item) => ({
              x: new Date(item.deviceTimestamp), // Ensure x-axis uses Date objects
              y: item.R,
            })),
        },
      ] as LineChartProps<Date>["series"],
    };
  } catch (error) {
    console.error("Error loading voltage data:", error);
    return { voltageDomain: [], voltageSeries: [] };
  }
}
