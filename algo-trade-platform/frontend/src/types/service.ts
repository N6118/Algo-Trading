import { AxiosResponse } from 'axios';
import { SignalGeneration } from './signal';
import { Strategy } from './strategy';
import { TradeCreateRequest, TradeResponse } from './trade';

export interface ServiceResponse<T> {
  data: T;
  meta?: {
    pagination?: {
      total: number;
      skip: number;
      limit: number;
    };
    timestamp: number;
  };
}

export interface ServiceResponseError {
  message: string;
  code?: string;
  details?: any;
}

export interface ServiceResponseWrapper<T> {
  data: T | null;
  error: ServiceResponseError | null;
  isLoading: boolean;
}

// Signal Service Types
export interface SignalServiceResponse<T> extends ServiceResponse<T> {}
export type SignalListResponse = SignalServiceResponse<SignalGeneration[]>;
export type SignalDetailsResponse = SignalServiceResponse<SignalGeneration>;

// Strategy Service Types
export interface StrategyServiceResponse<T> extends ServiceResponse<T> {}
export type StrategyListResponse = StrategyServiceResponse<Strategy[]>;
export type StrategyDetailsResponse = StrategyServiceResponse<Strategy>;

// Trade Service Types
export interface TradeServiceResponse<T> extends ServiceResponse<T> {}
export type TradeListResponse = TradeServiceResponse<TradeResponse[]>;
export type TradeDetailsResponse = TradeServiceResponse<TradeResponse>;
export type TradeCreateResponse = TradeServiceResponse<TradeResponse>;
