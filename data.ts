export interface VoltageDataItem {
  deviceTimestamp: string;
  R: number ; 
  Y: number ;
  B: number ; 
  N: number  ;
}

export interface TimingData {
  total_time_seconds: number;
  db_connection_seconds: number;
  query_execution_seconds: number;
  data_processing_seconds: number;
}
export async function fetchVoltageData(filter: string) {
  try {
    console.log("Sending request with filter:", filter); // Debugging line
    const response = await fetch(`http://127.0.0.1:7200/analytics/get_voltage_data?filter=${encodeURIComponent(filter)}`);
    if (!response.ok) throw new Error(`Failed to fetch JSON: ${response.statusText}`);

    const jsonData: { data: VoltageDataItem[]; timing: TimingData } = await response.json();
    if (!jsonData.data || jsonData.data.length === 0) return { voltageDomain: [], voltageSeries: [], timing: null };

    return {
      voltageDomain: jsonData.data.map((item) => new Date(item.deviceTimestamp.replace(" ", "T"))), // Fix timestamp parsing
      voltageSeries: ["R", "Y", "B", "N"].map((phase) => ({
        title: `Current (${phase} Phase)`,
        type: "line" as const,
        data: jsonData.data
          .filter((item) => item[phase as keyof VoltageDataItem] !== null)
          .map((item) => ({
            x: new Date(item.deviceTimestamp.replace(" ", "T")), // Ensure correct Date format
            y: item[phase as keyof VoltageDataItem]!,
          })),
      })),
      timing: jsonData.timing,
    };
  } catch (error) {
    console.error("Error loading voltage data:", error);
    return { voltageDomain: [], voltageSeries: [], timing: null };
  }
}

