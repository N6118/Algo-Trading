import { useEffect, useRef, useMemo } from 'react';
import { useTradingData } from '../../context/TradingDataContext';

interface PerformanceChartProps {
  timeRange: '1d' | '1w' | '1m' | '3m' | '1y';
}

const PerformanceChart = ({ timeRange }: PerformanceChartProps) => {
  const chartRef = useRef<HTMLCanvasElement>(null);
  const { performanceHistory } = useTradingData();
  
  // Filter data based on time range
  const filteredData = useMemo(() => {
    if (!performanceHistory.length) return [];
    
    const now = new Date();
    let daysBack = 30; // default to 1 month
    
    switch (timeRange) {
      case '1d':
        daysBack = 1;
        break;
      case '1w':
        daysBack = 7;
        break;
      case '1m':
        daysBack = 30;
        break;
      case '3m':
        daysBack = 90;
        break;
      case '1y':
        daysBack = 365;
        break;
    }
    
    const cutoffDate = new Date(now.getTime() - daysBack * 24 * 60 * 60 * 1000);
    return performanceHistory.filter(point => new Date(point.date) >= cutoffDate);
  }, [performanceHistory, timeRange]);
  
  useEffect(() => {
    if (!chartRef.current || !filteredData.length) return;
    
    const canvas = chartRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Set canvas size for high DPI displays
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    
    const width = rect.width;
    const height = rect.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Calculate data bounds
    const values = filteredData.map(d => d.value);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);
    const valueRange = maxValue - minValue || 1; // Avoid division by zero
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, 'rgba(37, 99, 235, 0.2)');
    gradient.addColorStop(1, 'rgba(37, 99, 235, 0.05)');
    
    // Draw area
    ctx.fillStyle = gradient;
    ctx.beginPath();
    
    filteredData.forEach((point, index) => {
      const x = (index / (filteredData.length - 1)) * width;
      const y = height - ((point.value - minValue) / valueRange) * height;
      
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    
    // Close the area
    ctx.lineTo(width, height);
    ctx.lineTo(0, height);
    ctx.closePath();
    ctx.fill();
    
    // Draw line
    ctx.strokeStyle = '#2563eb';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    
    filteredData.forEach((point, index) => {
      const x = (index / (filteredData.length - 1)) * width;
      const y = height - ((point.value - minValue) / valueRange) * height;
      
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    
    ctx.stroke();
    
    // Draw data points for shorter time ranges
    if (timeRange === '1d' || timeRange === '1w') {
      ctx.fillStyle = '#2563eb';
      filteredData.forEach((point, index) => {
        const x = (index / (filteredData.length - 1)) * width;
        const y = height - ((point.value - minValue) / valueRange) * height;
        
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, 2 * Math.PI);
        ctx.fill();
      });
    }
    
  }, [filteredData, timeRange]);
  
  if (!filteredData.length) {
    return (
      <div className="w-full h-full flex items-center justify-center text-gray-500 dark:text-gray-400">
        No performance data available for the selected time range
      </div>
    );
  }
  
  return (
    <div className="w-full h-full relative">
      <canvas 
        ref={chartRef} 
        className="w-full h-full"
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
};

export default PerformanceChart;

export { PerformanceChart };