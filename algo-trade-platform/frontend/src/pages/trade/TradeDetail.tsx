import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { 
  ArrowDown, 
  ArrowUp, 
  Clock, 
  Edit2, 
  FileText, 
  TrendingUp, 
  X,
  Save,
  Trash2,
  RefreshCw
} from 'lucide-react';
import { useTradingData } from '../../context/TradingDataContext';
import { formatCurrency, formatDateTime } from '../../utils/formatters';
import PerformanceChart from '../../components/charts/PerformanceChart';
import toast from 'react-hot-toast';

interface TradeNote {
  id: string;
  content: string;
  timestamp: string;
  author: string;
}

interface TradeExecution {
  id: string;
  timestamp: string;
  type: 'entry' | 'exit' | 'partial';
  quantity: number;
  price: number;
  fees: number;
}

interface PriceHistory {
  timestamp: string;
  price: number;
  volume: number;
}

const TradeDetail = () => {
  const { id } = useParams();
  const { activeTrades } = useTradingData();
  const trade = activeTrades.find(t => t.id === id);
  
  const [showNoteForm, setShowNoteForm] = useState(false);
  const [note, setNote] = useState('');
  const [notes, setNotes] = useState<TradeNote[]>([]);
  const [executions, setExecutions] = useState<TradeExecution[]>([]);
  const [priceHistory, setPriceHistory] = useState<PriceHistory[]>([]);
  const [editingParameters, setEditingParameters] = useState(false);
  const [parameters, setParameters] = useState({
    stopLoss: 0,
    takeProfit: 0,
    quantity: 0
  });
  const [realTimePrice, setRealTimePrice] = useState(0);
  const [realTimePnL, setRealTimePnL] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  useEffect(() => {
    if (trade) {
      setParameters({
        stopLoss: trade.stopLoss || 0,
        takeProfit: trade.takeProfit || 0,
        quantity: trade.quantity
      });
      setRealTimePrice(trade.currentPrice);
      setRealTimePnL(trade.pnl);
      
      fetchTradeDetails();
      setupWebSocketConnections();
    }
  }, [trade]);

  const fetchTradeDetails = async () => {
    if (!id) return;

    try {
      // Fetch trade notes
      const notesRes = await fetch(`/api/trades/${id}/notes`);
      if (notesRes.ok) {
        const notesData = await notesRes.json();
        setNotes(notesData);
      }

      // Fetch execution details
      const executionsRes = await fetch(`/api/trades/${id}/executions`);
      if (executionsRes.ok) {
        const executionsData = await executionsRes.json();
        setExecutions(executionsData);
      }

      // Fetch price history
      const priceHistoryRes = await fetch(`/api/trades/${id}/price-history`);
      if (priceHistoryRes.ok) {
        const priceHistoryData = await priceHistoryRes.json();
        setPriceHistory(priceHistoryData);
      }
    } catch (err) {
      console.error('Failed to fetch trade details:', err);
      // Set mock data
      setNotes([
        {
          id: '1',
          content: 'Initial entry based on momentum signal',
          timestamp: new Date().toISOString(),
          author: 'System'
        }
      ]);
      setExecutions([
        {
          id: '1',
          timestamp: trade?.entryTime || new Date().toISOString(),
          type: 'entry',
          quantity: trade?.quantity || 0,
          price: trade?.entryPrice || 0,
          fees: 7.95
        }
      ]);
    }
  };

  const setupWebSocketConnections = () => {
    if (!trade) return;

    // Real-time trade updates
    const tradeWs = new WebSocket(`ws://localhost:8080/api/ws/trades/${id}`);
    tradeWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Handle trade updates
      console.log('Trade update:', data);
    };

    // Real-time price updates
    const priceWs = new WebSocket(`ws://localhost:8080/api/ws/market/data/${trade.symbol}`);
    priceWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setRealTimePrice(data.price);
    };

    // Real-time P&L updates
    const pnlWs = new WebSocket(`ws://localhost:8080/api/ws/trades/${id}/pnl`);
    pnlWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setRealTimePnL(data.pnl);
    };

    // Real-time execution updates
    const executionWs = new WebSocket(`ws://localhost:8080/api/ws/trades/${id}/executions`);
    executionWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setExecutions(prev => [...prev, data]);
    };

    // Cleanup function
    return () => {
      tradeWs.close();
      priceWs.close();
      pnlWs.close();
      executionWs.close();
    };
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!note.trim() || !id) return;

    try {
      const response = await fetch(`/api/trades/${id}/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: note }),
      });

      if (response.ok) {
        const newNote = await response.json();
        setNotes([...notes, newNote]);
        setNote('');
        setShowNoteForm(false);
        toast.success('Note added successfully');
      } else {
        toast.error('Failed to add note');
      }
    } catch (err) {
      console.error('Failed to add note:', err);
      toast.error('Failed to add note');
    }
  };

  const handleDeleteNote = async (noteId: string) => {
    if (!confirm('Are you sure you want to delete this note?')) return;

    try {
      const response = await fetch(`/api/trades/${id}/notes/${noteId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setNotes(notes.filter(n => n.id !== noteId));
        toast.success('Note deleted successfully');
      } else {
        toast.error('Failed to delete note');
      }
    } catch (err) {
      console.error('Failed to delete note:', err);
      toast.error('Failed to delete note');
    }
  };

  const handleUpdateParameters = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id) return;

    try {
      const response = await fetch(`/api/trades/${id}/parameters`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(parameters),
      });

      if (response.ok) {
        setEditingParameters(false);
        toast.success('Trade parameters updated successfully');
      } else {
        toast.error('Failed to update parameters');
      }
    } catch (err) {
      console.error('Failed to update parameters:', err);
      toast.error('Failed to update parameters');
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await fetchTradeDetails();
      toast.success('Trade details refreshed');
    } catch (error) {
      toast.error('Failed to refresh trade details');
    } finally {
      setIsRefreshing(false);
    }
  };

  if (!trade) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <h2 className="text-xl font-medium text-gray-900 dark:text-white">Trade not found</h2>
          <p className="mt-2 text-gray-500 dark:text-gray-400">
            The trade you're looking for doesn't exist or has been closed.
          </p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Trade Details
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            ID: {trade.id}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 flex items-center"
          >
            <RefreshCw size={16} className={`mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => setEditingParameters(!editingParameters)}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 flex items-center"
          >
            <Edit2 size={16} className="mr-2" />
            Edit Trade
          </button>
          <button className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700">
            Close Trade
          </button>
        </div>
      </div>
      
      {/* Trade Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Symbol</div>
          <div className="mt-1 flex items-center">
            <div className="text-2xl font-semibold text-gray-900 dark:text-white">{trade.symbol}</div>
            <div className={`ml-2 px-2 py-1 text-xs font-medium rounded-full ${
              trade.direction === 'long'
                ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200'
                : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200'
            }`}>
              {trade.direction.toUpperCase()}
            </div>
          </div>
          <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">{trade.strategyName}</div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Position Size</div>
          <div className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
            {trade.quantity} shares
          </div>
          <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {formatCurrency(trade.quantity * realTimePrice)} total value
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Entry Price</div>
          <div className="mt-1 text-2xl font-semibold text-gray-900 dark:text-white">
            {formatCurrency(trade.entryPrice)}
          </div>
          <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Current: {formatCurrency(realTimePrice)}
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Current P&L</div>
          <div className={`mt-1 text-2xl font-semibold ${
            realTimePnL > 0 
              ? 'text-green-600 dark:text-green-400' 
              : 'text-red-600 dark:text-red-400'
          }`}>
            {formatCurrency(realTimePnL)}
          </div>
          <div className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {((realTimePnL / (trade.entryPrice * trade.quantity)) * 100).toFixed(2)}% return
          </div>
        </div>
      </div>
      
      {/* Price Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-6">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Price Action</h2>
          <div className="h-96">
            <PerformanceChart timeRange="1d" />
          </div>
        </div>
      </div>
      
      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trade Parameters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white">Risk Management</h2>
              {!editingParameters && (
                <button
                  onClick={() => setEditingParameters(true)}
                  className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                >
                  <Edit2 size={16} />
                </button>
              )}
            </div>
            
            {editingParameters ? (
              <form onSubmit={handleUpdateParameters} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Stop Loss
                  </label>
                  <input
                    type="number"
                    value={parameters.stopLoss}
                    onChange={(e) => setParameters({ ...parameters, stopLoss: parseFloat(e.target.value) })}
                    className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                    step="0.01"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Take Profit
                  </label>
                  <input
                    type="number"
                    value={parameters.takeProfit}
                    onChange={(e) => setParameters({ ...parameters, takeProfit: parseFloat(e.target.value) })}
                    className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                    step="0.01"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Quantity
                  </label>
                  <input
                    type="number"
                    value={parameters.quantity}
                    onChange={(e) => setParameters({ ...parameters, quantity: parseInt(e.target.value) })}
                    className="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                  />
                </div>
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setEditingParameters(false)}
                    className="px-3 py-1 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-3 py-1 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 flex items-center"
                  >
                    <Save size={14} className="mr-1" />
                    Save
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <div className="text-sm text-gray-500 dark:text-gray-400">Stop Loss</div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {formatCurrency(parameters.stopLoss)}
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <div className="text-sm text-gray-500 dark:text-gray-400">Take Profit</div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {formatCurrency(parameters.takeProfit)}
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <div className="text-sm text-gray-500 dark:text-gray-400">Risk Amount</div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {formatCurrency(trade.risk)}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* Trade Notes */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium text-gray-900 dark:text-white">Trade Notes</h2>
              <button
                onClick={() => setShowNoteForm(!showNoteForm)}
                className="text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
              >
                <Edit2 size={16} />
              </button>
            </div>
            
            {showNoteForm ? (
              <form onSubmit={handleAddNote} className="space-y-4">
                <textarea
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  rows={4}
                  className="block w-full rounded-md border-gray-300 dark:border-gray-600 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:bg-gray-700 dark:text-white sm:text-sm"
                  placeholder="Add a note about this trade..."
                />
                <div className="flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => setShowNoteForm(false)}
                    className="px-3 py-1 text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-3 py-1 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                  >
                    Save Note
                  </button>
                </div>
              </form>
            ) : (
              <div className="space-y-3">
                {notes.length > 0 ? (
                  notes.map((note) => (
                    <div key={note.id} className="p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <p className="text-sm text-gray-900 dark:text-white">{note.content}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            {note.author} • {formatDateTime(note.timestamp)}
                          </p>
                        </div>
                        <button
                          onClick={() => handleDeleteNote(note.id)}
                          className="text-red-600 hover:text-red-700 ml-2"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-sm text-gray-500 dark:text-gray-400">
                    No notes added yet.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Execution History */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="p-6">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Execution History</h2>
          <div className="space-y-3">
            {executions.map((execution) => (
              <div key={execution.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={`w-2 h-2 rounded-full ${
                    execution.type === 'entry' ? 'bg-blue-500' :
                    execution.type === 'exit' ? 'bg-red-500' : 'bg-yellow-500'
                  }`} />
                  <div>
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {execution.type.charAt(0).toUpperCase() + execution.type.slice(1)} - {execution.quantity} shares
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {formatDateTime(execution.timestamp)}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {formatCurrency(execution.price)}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Fees: {formatCurrency(execution.fees)}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradeDetail;