import { useEffect, useRef } from "react";
import Chart from "chart.js/auto";

export default function ChartCanvas({ config, className = "" }) {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    Chart.defaults.color = "#64748b";
    Chart.defaults.font.family = "Inter, Manrope, system-ui, sans-serif";
    Chart.defaults.font.size = 12;
  }, []);

  useEffect(() => {
    if (!canvasRef.current) return;
    if (chartRef.current) chartRef.current.destroy();
    // Soportar plugins a nivel de instancia (config.plugins array)
    const { plugins: chartPlugins, ...restConfig } = config;
    const chartConfig = {
      ...restConfig,
      ...(chartPlugins && Array.isArray(chartPlugins) ? { plugins: chartPlugins } : {}),
    };
    chartRef.current = new Chart(canvasRef.current, chartConfig);
    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
        chartRef.current = null;
      }
    };
  }, [config]);

  return <canvas ref={canvasRef} className={`chart-canvas ${className}`.trim()} />;
}
