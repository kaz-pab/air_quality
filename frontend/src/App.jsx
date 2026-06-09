import { useState, useEffect } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

const API = "http://localhost:8000";

const POLLUTANT_COLORS = {
  NO2: "#e74c3c",
  PM10: "#e67e22",
  PM25: "#8e44ad",
};

export default function App() {
  const [meta, setMeta] = useState(null);
  const [station, setStation] = useState("");
  const [pollutant, setPollutant] = useState("");
  const [year, setYear] = useState("");
  const [view, setView] = useState("daily");
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    axios.get(`${API}/meta`).then((res) => {
      setMeta(res.data);
      setStation(res.data.stations[0]);
      setPollutant(res.data.pollutants[0]);
      setYear(res.data.years[res.data.years.length - 1]);
    });
  }, []);

  useEffect(() => {
    if (!station || !pollutant || !year) return;
    setLoading(true);
    axios
      .get(`${API}/${view}`, { params: { station, pollutant, year } })
      .then((res) => setData(res.data))
      .finally(() => setLoading(false));
  }, [station, pollutant, year, view]);

  const xKey = view === "daily" ? "date" : "hour";
  const xLabel = view === "daily" ? "Date" : "Hour of day";

  if (!meta) return <div style={{ padding: 40 }}>Loading...</div>;

  return (
    <div style={{ padding: 32, fontFamily: "sans-serif", maxWidth: 1100 }}>
      <h1 style={{ marginBottom: 24 }}>Warsaw Air Quality</h1>

      <div style={{ display: "flex", gap: 16, marginBottom: 24, flexWrap: "wrap" }}>
        <label>
          Station&nbsp;
          <select value={station} onChange={(e) => setStation(e.target.value)}>
            {meta.stations.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </label>

        <label>
          Pollutant&nbsp;
          <select value={pollutant} onChange={(e) => setPollutant(e.target.value)}>
            {meta.pollutants.map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
        </label>

        <label>
          Year&nbsp;
          <select value={year} onChange={(e) => setYear(Number(e.target.value))}>
            {meta.years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </label>

        <label>
          View&nbsp;
          <select value={view} onChange={(e) => setView(e.target.value)}>
            <option value="daily">Daily average</option>
            <option value="hourly">Hourly profile</option>
          </select>
        </label>
      </div>

      {loading ? (
        <div>Loading data...</div>
      ) : (
        <ResponsiveContainer width="100%" height={420}>
          <LineChart data={data} margin={{ top: 8, right: 24, bottom: 8, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} label={{ value: xLabel, position: "insideBottom", offset: -4 }} />
            <YAxis label={{ value: "ug/m3", angle: -90, position: "insideLeft" }} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="avg_value"
              stroke={POLLUTANT_COLORS[pollutant] || "#3498db"}
              dot={false}
              name={`${pollutant} avg`}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}