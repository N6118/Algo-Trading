import { useEffect, useRef } from 'react';
import { useTradingData } from '../../context/TradingDataContext';

interface PerformanceChartProps {
  timeRange: '1d' | '1w' | '1m' | '3m' | '1y';
}

const PerformanceChart = ({ timeRange }: PerformanceChartProps) => {
  const chartRef = useRef<HTMLCanvasElement>(null);
  const { performanceHistory } = useTradingData();
  
  useEffect(() => {
    // In a real application, we would render a chart here using a library
    // like Chart.js, Recharts, or D3
    
    if (chartRef.current) {
      const ctx = chartRef.current.getContext('2d');
      if (ctx) {
        // This is a placeholder for actual chart rendering
        // We'd use the performance data based on the timeRange
        
        // Mock chart drawing for visual representation
        const width = chartRef.current.width;
        const height = chartRef.current.height;
        
        // Clear canvas
        ctx.clearRect(0, 0, width, height);
        
        // Create gradient
        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, 'rgba(37, 99, 235, 0.1)');
        gradient.addColorStop(1, 'rgba(37, 99, 235, 0)');
        
        // Draw area
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.moveTo(0, height * 0.8);
        
        // Create a mock performance line - in a real app this would use actual data
        for (let i = 0; i < width; i += width/20) {
          const randomVariance = Math.random() * 0.1 - 0.05;
          const y = height * (0.5 + randomVariance);
          ctx.lineTo(i, y);
        }
        
        ctx.lineTo(width, height * 0.3);
        ctx.lineTo(width, height);
        ctx.lineTo(0, height);
        ctx.closePath();
        ctx.fill();
        
        // Draw line
        ctx.strokeStyle = '#2563eb';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(0, height * 0.8);
        
        // Redraw the same line for the stroke
        for (let i = 0; i < width; i += width/20) {
          const randomVariance = Math.random() * 0.1 - 0.05;
          const y = height * (0.5 + randomVariance);
          ctx.lineTo(i, y);
        }
        
        ctx.lineTo(width, height * 0.3);
        ctx.stroke();
      }
    }
  }, [timeRange, performanceHistory]);
  
  return (
    <div className="w-full h-full flex items-center justify-center">
      <canvas 
        ref={chartRef} 
        width={800} 
        height={300}
        className="w-full h-full"
      ></canvas>
    </div>
  );
};

export default PerformanceChart;

export { PerformanceChart }